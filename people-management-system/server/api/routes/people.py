"""
API routes for People management.

This module provides CRUD operations and search functionality for managing
people in the system, including their personal information and relationships
with employment records.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from ...database.models import Person, Employment, Position, Department
from ...database.db import get_db
from ..dependencies import (
    get_database_session, get_pagination_params, get_search_params,
    get_common_query_params, PaginationParams, SearchParams, CommonQueryParams
)
from ..schemas.person import (
    PersonCreate, PersonUpdate, PersonResponse, PersonSummary,
    PersonWithEmployment, PersonSearch, PersonBulkCreate, PersonAddressUpdate,
    PersonContactUpdate
)
from ..schemas.common import (
    PaginatedResponse, SuccessResponse, create_success_response,
    create_paginated_response
)
from ...core.exceptions import (
    PersonNotFoundError, EmailAlreadyExistsError, HTTPBadRequestError,
    HTTPInternalServerError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/people", tags=["people"])


@router.post(
    "/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new person",
    description="Create a new person record with the provided information."
)
async def create_person(
    person_data: PersonCreate,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Create a new person."""
    try:
        # Check if email already exists
        existing_person = db.query(Person).filter(Person.email == person_data.email).first()
        if existing_person:
            raise EmailAlreadyExistsError(person_data.email)
        
        # Create new person
        db_person = Person(**person_data.dict())
        db.add(db_person)
        db.commit()
        db.refresh(db_person)
        
        logger.info(f"Created new person: {db_person.full_name} ({db_person.id})")
        return PersonResponse.from_orm(db_person)
        
    except EmailAlreadyExistsError:
        raise
    except Exception as e:
        logger.error(f"Error creating person: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to create person: {str(e)}")


@router.get(
    "/",
    response_model=PaginatedResponse[PersonSummary],
    summary="List people",
    description="Get a paginated list of people with optional search and filtering."
)
async def list_people(
    params: CommonQueryParams = Depends(get_common_query_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PersonSummary]:
    """Get a paginated list of people."""
    try:
        # Build base query
        query = db.query(Person)
        
        # Apply search filters
        if params.search.query:
            search_term = f"%{params.search.query}%"
            query = query.filter(
                or_(
                    Person.first_name.ilike(search_term),
                    Person.last_name.ilike(search_term),
                    Person.email.ilike(search_term),
                    func.concat(Person.first_name, ' ', Person.last_name).ilike(search_term)
                )
            )
        
        # Apply active filter (show only people with active employment)
        if params.active is not None and params.active:
            query = query.join(Employment).filter(Employment.is_active == True)
        
        # Apply sorting
        if params.search.sort_by:
            sort_column = getattr(Person, params.search.sort_by, None)
            if sort_column:
                if params.search.is_descending:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                logger.warning(f"Invalid sort column: {params.search.sort_by}")
        else:
            query = query.order_by(Person.last_name, Person.first_name)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset, limit = params.pagination.get_offset_limit()
        people = query.offset(offset).limit(limit).all()
        
        # Convert to response format with employment info
        people_summaries = []
        for person in people:
            current_employment = person.current_employment
            summary_data = {
                "id": person.id,
                "full_name": person.full_name,
                "email": person.email,
                "current_position": current_employment.position.title if current_employment else None,
                "current_department": current_employment.position.department.name if current_employment else None
            }
            people_summaries.append(PersonSummary(**summary_data))
        
        return create_paginated_response(
            items=people_summaries,
            page=params.pagination.page,
            size=params.pagination.size,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing people: {str(e)}")
        raise HTTPInternalServerError(f"Failed to list people: {str(e)}")


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Get person by ID",
    description="Get detailed information about a specific person."
)
async def get_person(
    person_id: UUID,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Get a person by ID."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        return PersonResponse.from_orm(person)
        
    except PersonNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting person {person_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get person: {str(e)}")


@router.get(
    "/{person_id}/employment",
    response_model=PersonWithEmployment,
    summary="Get person with employment details",
    description="Get person information including current and past employment records."
)
async def get_person_with_employment(
    person_id: UUID,
    db: Session = Depends(get_database_session)
) -> PersonWithEmployment:
    """Get a person with employment details."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Get current employment
        current_employment = person.current_employment
        current_emp_data = None
        if current_employment:
            current_emp_data = {
                "id": current_employment.id,
                "position": current_employment.position.title,
                "department": current_employment.position.department.name,
                "start_date": current_employment.start_date,
                "salary": float(current_employment.salary) if current_employment.salary else None
            }
        
        # Get employment history (past employments)
        past_employments = [
            {
                "id": emp.id,
                "position": emp.position.title,
                "department": emp.position.department.name,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "salary": float(emp.salary) if emp.salary else None
            }
            for emp in person.employments if not emp.is_active
        ]
        
        # Create response data
        person_data = PersonResponse.from_orm(person).dict()
        person_data["current_employment"] = current_emp_data
        person_data["employment_history"] = past_employments
        
        return PersonWithEmployment(**person_data)
        
    except PersonNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting person employment {person_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get person employment: {str(e)}")


@router.put(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Update person",
    description="Update person information with the provided data."
)
async def update_person(
    person_id: UUID,
    person_data: PersonUpdate,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Update a person."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Check if email is being updated and if it already exists
        if person_data.email and person_data.email != person.email:
            existing_person = db.query(Person).filter(
                and_(Person.email == person_data.email, Person.id != person_id)
            ).first()
            if existing_person:
                raise EmailAlreadyExistsError(person_data.email)
        
        # Update person fields
        update_data = person_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        db.commit()
        db.refresh(person)
        
        logger.info(f"Updated person: {person.full_name} ({person.id})")
        return PersonResponse.from_orm(person)
        
    except (PersonNotFoundError, EmailAlreadyExistsError):
        raise
    except Exception as e:
        logger.error(f"Error updating person {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update person: {str(e)}")


@router.patch(
    "/{person_id}/contact",
    response_model=PersonResponse,
    summary="Update person contact information",
    description="Update only the contact information (email and phone) for a person."
)
async def update_person_contact(
    person_id: UUID,
    contact_data: PersonContactUpdate,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Update person contact information."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Check if email is being updated and if it already exists
        if contact_data.email and contact_data.email != person.email:
            existing_person = db.query(Person).filter(
                and_(Person.email == contact_data.email, Person.id != person_id)
            ).first()
            if existing_person:
                raise EmailAlreadyExistsError(contact_data.email)
        
        # Update contact fields
        update_data = contact_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        db.commit()
        db.refresh(person)
        
        logger.info(f"Updated contact info for person: {person.full_name} ({person.id})")
        return PersonResponse.from_orm(person)
        
    except (PersonNotFoundError, EmailAlreadyExistsError):
        raise
    except Exception as e:
        logger.error(f"Error updating person contact {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update person contact: {str(e)}")


@router.patch(
    "/{person_id}/address",
    response_model=PersonResponse,
    summary="Update person address",
    description="Update only the address information for a person."
)
async def update_person_address(
    person_id: UUID,
    address_data: PersonAddressUpdate,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Update person address information."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Update address fields
        update_data = address_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        db.commit()
        db.refresh(person)
        
        logger.info(f"Updated address for person: {person.full_name} ({person.id})")
        return PersonResponse.from_orm(person)
        
    except PersonNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating person address {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update person address: {str(e)}")


@router.delete(
    "/{person_id}",
    response_model=SuccessResponse,
    summary="Delete person",
    description="Delete a person and all associated employment records."
)
async def delete_person(
    person_id: UUID,
    db: Session = Depends(get_database_session)
) -> SuccessResponse:
    """Delete a person."""
    try:
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        person_name = person.full_name
        
        # Delete person (cascade will handle employment records)
        db.delete(person)
        db.commit()
        
        logger.info(f"Deleted person: {person_name} ({person_id})")
        return create_success_response(f"Person '{person_name}' deleted successfully")
        
    except PersonNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting person {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to delete person: {str(e)}")


@router.get(
    "/search/advanced",
    response_model=PaginatedResponse[PersonSummary],
    summary="Advanced person search",
    description="Search people with advanced filtering options."
)
async def search_people(
    name: Optional[str] = Query(None, description="Search by name"),
    email: Optional[str] = Query(None, description="Search by email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    active_only: bool = Query(True, description="Show only active employees"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PersonSummary]:
    """Advanced search for people."""
    try:
        # Build base query
        query = db.query(Person)
        
        # Join with employment and position tables for filtering
        if department or position or active_only:
            query = query.join(Employment).join(Position).join(Department)
        
        # Apply filters
        if name:
            search_term = f"%{name}%"
            query = query.filter(
                or_(
                    Person.first_name.ilike(search_term),
                    Person.last_name.ilike(search_term),
                    func.concat(Person.first_name, ' ', Person.last_name).ilike(search_term)
                )
            )
        
        if email:
            query = query.filter(Person.email.ilike(f"%{email}%"))
        
        if department:
            query = query.filter(Department.name.ilike(f"%{department}%"))
        
        if position:
            query = query.filter(Position.title.ilike(f"%{position}%"))
        
        if active_only:
            query = query.filter(Employment.is_active == True)
        
        # Order by name
        query = query.order_by(Person.last_name, Person.first_name)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset, limit = pagination.get_offset_limit()
        people = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        people_summaries = []
        for person in people:
            current_employment = person.current_employment
            summary_data = {
                "id": person.id,
                "full_name": person.full_name,
                "email": person.email,
                "current_position": current_employment.position.title if current_employment else None,
                "current_department": current_employment.position.department.name if current_employment else None
            }
            people_summaries.append(PersonSummary(**summary_data))
        
        return create_paginated_response(
            items=people_summaries,
            page=pagination.page,
            size=pagination.size,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error in advanced people search: {str(e)}")
        raise HTTPInternalServerError(f"Failed to search people: {str(e)}")


@router.get(
    "/by-email/{email}",
    response_model=PersonResponse,
    summary="Get person by email",
    description="Find a person by their email address."
)
async def get_person_by_email(
    email: str,
    db: Session = Depends(get_database_session)
) -> PersonResponse:
    """Get a person by email address."""
    try:
        person = db.query(Person).filter(Person.email == email.lower()).first()
        if not person:
            raise HTTPBadRequestError(f"No person found with email: {email}")
        
        return PersonResponse.from_orm(person)
        
    except HTTPBadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error getting person by email {email}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get person by email: {str(e)}")


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create people",
    description="Create multiple people in a single request."
)
async def bulk_create_people(
    bulk_data: PersonBulkCreate,
    db: Session = Depends(get_database_session)
) -> dict:
    """Bulk create people."""
    try:
        created_people = []
        errors = []
        
        for i, person_data in enumerate(bulk_data.people):
            try:
                # Check if email already exists
                existing_person = db.query(Person).filter(Person.email == person_data.email).first()
                if existing_person:
                    errors.append({
                        "index": i,
                        "email": person_data.email,
                        "error": f"Email already exists: {person_data.email}"
                    })
                    continue
                
                # Create person
                db_person = Person(**person_data.dict())
                db.add(db_person)
                db.flush()  # Get ID without committing
                
                created_people.append({
                    "index": i,
                    "id": str(db_person.id),
                    "name": db_person.full_name,
                    "email": db_person.email
                })
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "email": person_data.email,
                    "error": str(e)
                })
        
        # Commit all successful creations
        if created_people:
            db.commit()
        
        logger.info(f"Bulk created {len(created_people)} people with {len(errors)} errors")
        
        return {
            "success_count": len(created_people),
            "error_count": len(errors),
            "created_people": created_people,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk create people: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to bulk create people: {str(e)}")


# Health check for people endpoint
@router.get(
    "/health",
    response_model=dict,
    summary="People endpoint health check",
    description="Check the health of the people endpoint and database connectivity."
)
async def people_health_check(
    db: Session = Depends(get_database_session)
) -> dict:
    """Health check for people endpoint."""
    try:
        # Test database query
        count = db.query(Person).count()
        
        return {
            "status": "healthy",
            "total_people": count,
            "timestamp": func.now()
        }
        
    except Exception as e:
        logger.error(f"People health check failed: {str(e)}")
        raise HTTPInternalServerError(f"People endpoint unhealthy: {str(e)}")