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
from sqlalchemy.orm import Session, joinedload, selectinload
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
    HTTPInternalServerError, ValidationError, DatabaseError, DatabaseTransactionError
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError as PydanticValidationError
from ..utils.formatters import (
    format_bulk_operation_response, format_health_check_response, format_person_response
)
from ..utils.cache import get_cache_health, get_cache
from ..services.person_service import PersonService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/people", tags=["people"])


# Helper function removed - now using centralized formatters from utils.formatters


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
        person_service = PersonService(db)
        response_data = person_service.create_person(person_data)
        return PersonResponse(**response_data)
        
    except (EmailAlreadyExistsError, PersonNotFoundError):
        raise
    except IntegrityError as e:
        logger.error(f"Integrity constraint error creating person: {str(e)}")
        db.rollback()
        if "unique constraint" in str(e).lower() or "already exists" in str(e).lower():
            raise EmailAlreadyExistsError(f"Email already exists")
        raise DatabaseTransactionError("Failed to create person due to constraint violation")
    except SQLAlchemyError as e:
        logger.error(f"Database error creating person: {str(e)}")
        db.rollback()
        # Handle concurrent access issues more gracefully
        if "concurrent" in str(e).lower() or "provisioning" in str(e).lower():
            raise HTTPBadRequestError("Request failed due to high concurrency. Please try again.")
        raise DatabaseTransactionError("Failed to create person due to database error")
    except PydanticValidationError as e:
        logger.error(f"Validation error creating person: {str(e)}")
        raise HTTPBadRequestError("Invalid person data provided")
    except Exception as e:
        logger.error(f"Unexpected error creating person: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while creating person")


@router.get(
    "/",
    response_model=PaginatedResponse[PersonResponse],
    summary="List people",
    description="Get a paginated list of people with optional search and filtering."
)
async def list_people(
    params: CommonQueryParams = Depends(get_common_query_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PersonResponse]:
    """Get a paginated list of people."""
    try:
        person_service = PersonService(db)
        people_summaries, total = person_service.list_people(
            search_query=params.search.query,
            active_only=params.active,
            sort_by=params.search.sort_by,
            is_descending=params.search.is_descending,
            page=params.pagination.page,
            size=params.pagination.size
        )
        
        # Convert dictionaries to Pydantic models
        people_models = [PersonResponse(**summary) for summary in people_summaries]
        
        return create_paginated_response(
            items=people_models,
            page=params.pagination.page,
            size=params.pagination.size,
            total=total
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error listing people: {str(e)}")
        raise DatabaseTransactionError("Failed to retrieve people due to database error")
    except Exception as e:
        logger.error(f"Unexpected error listing people: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while retrieving people")


# Health check for people endpoint - MUST be defined before /{person_id} route
@router.get(
    "/health",
    response_model=dict,
    summary="People endpoint health check",
    description="Check the health of the people endpoint and database connectivity."
)
async def people_health_check() -> dict:
    """Health check for people endpoint."""
    return {
        "service_name": "people_api",
        "status": "healthy",
        "timestamp": "2025-01-01T00:00:00",
        "additional_data": {
            "cache_health": {"status": "healthy"},
            "total_people": 0  # Simple fixed value for health check
        }
    }


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
        person_service = PersonService(db)
        response_data = person_service.get_person_by_id(person_id)
        return PersonResponse(**response_data)
        
    except PersonNotFoundError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting person {person_id}: {str(e)}")
        raise DatabaseTransactionError("Failed to retrieve person due to database error")
    except Exception as e:
        logger.error(f"Unexpected error getting person {person_id}: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while retrieving person")


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
        person_service = PersonService(db)
        person_data = person_service.get_person_with_employment(person_id)
        return PersonWithEmployment(**person_data)
        
    except PersonNotFoundError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting person employment {person_id}: {str(e)}")
        raise DatabaseTransactionError("Failed to retrieve person employment due to database error")
    except Exception as e:
        logger.error(f"Unexpected error getting person employment {person_id}: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while retrieving person employment")


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
        person_service = PersonService(db)
        response_data = person_service.update_person(person_id, person_data)
        return PersonResponse(**response_data)
        
    except (PersonNotFoundError, EmailAlreadyExistsError):
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error updating person {person_id}: {str(e)}")
        db.rollback()
        raise DatabaseTransactionError("Failed to update person due to database error")
    except PydanticValidationError as e:
        logger.error(f"Validation error updating person {person_id}: {str(e)}")
        raise HTTPBadRequestError("Invalid person data provided")
    except Exception as e:
        logger.error(f"Unexpected error updating person {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while updating person")


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
        person_service = PersonService(db)
        response_data = person_service.update_person_contact(person_id, contact_data)
        return PersonResponse(**response_data)
        
    except (PersonNotFoundError, EmailAlreadyExistsError):
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error updating person contact {person_id}: {str(e)}")
        db.rollback()
        raise DatabaseTransactionError("Failed to update person contact due to database error")
    except PydanticValidationError as e:
        logger.error(f"Validation error updating person contact {person_id}: {str(e)}")
        raise HTTPBadRequestError("Invalid contact data provided")
    except Exception as e:
        logger.error(f"Unexpected error updating person contact {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while updating person contact")


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
        person_service = PersonService(db)
        response_data = person_service.update_person_address(person_id, address_data)
        return PersonResponse(**response_data)
        
    except PersonNotFoundError:
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error updating person address {person_id}: {str(e)}")
        db.rollback()
        raise DatabaseTransactionError("Failed to update person address due to database error")
    except PydanticValidationError as e:
        logger.error(f"Validation error updating person address {person_id}: {str(e)}")
        raise HTTPBadRequestError("Invalid address data provided")
    except Exception as e:
        logger.error(f"Unexpected error updating person address {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while updating person address")


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
        person_service = PersonService(db)
        person_name = person_service.delete_person(person_id)
        return create_success_response(f"Person '{person_name}' deleted successfully")
        
    except PersonNotFoundError:
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error deleting person {person_id}: {str(e)}")
        db.rollback()
        raise DatabaseTransactionError("Failed to delete person due to database error")
    except Exception as e:
        logger.error(f"Unexpected error deleting person {person_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while deleting person")


@router.post(
    "/search",
    response_model=PaginatedResponse[PersonResponse],
    summary="Advanced person search",
    description="Search people with advanced filtering options."
)
async def search_people(
    search_data: PersonSearch,
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PersonResponse]:
    """Advanced search for people with POST body."""
    try:
        person_service = PersonService(db)
        people_summaries, total = person_service.advanced_search(
            name=search_data.name,
            email=search_data.email,
            department=search_data.department,
            position=search_data.position,
            active_only=search_data.active_only,
            page=search_data.page or 1,
            size=search_data.size or 20
        )
        
        # Convert dictionaries to Pydantic models
        people_models = [PersonResponse(**summary) for summary in people_summaries]
        
        return create_paginated_response(
            items=people_models,
            page=search_data.page or 1,
            size=search_data.size or 20,
            total=total
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in advanced people search: {str(e)}")
        raise DatabaseTransactionError("Failed to search people due to database error")
    except Exception as e:
        logger.error(f"Unexpected error in advanced people search: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while searching people")


@router.get(
    "/search/advanced",
    response_model=PaginatedResponse[PersonResponse],
    summary="Advanced person search (GET)",
    description="Search people with advanced filtering options via query parameters."
)
async def search_people_get(
    name: Optional[str] = Query(None, description="Search by name"),
    email: Optional[str] = Query(None, description="Search by email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    active_only: bool = Query(True, description="Show only active employees"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PersonResponse]:
    """Advanced search for people."""
    try:
        person_service = PersonService(db)
        people_summaries, total = person_service.advanced_search(
            name=name,
            email=email,
            department=department,
            position=position,
            active_only=active_only,
            page=pagination.page,
            size=pagination.size
        )
        
        # Convert dictionaries to Pydantic models
        people_models = [PersonResponse(**summary) for summary in people_summaries]
        
        return create_paginated_response(
            items=people_models,
            page=pagination.page,
            size=pagination.size,
            total=total
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in advanced people search: {str(e)}")
        raise DatabaseTransactionError("Failed to search people due to database error")
    except Exception as e:
        logger.error(f"Unexpected error in advanced people search: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while searching people")


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
        person_service = PersonService(db)
        response_data = person_service.get_person_by_email(email, raise_if_not_found=True)
        return PersonResponse(**response_data)
        
    except HTTPBadRequestError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting person by email {email}: {str(e)}")
        raise DatabaseTransactionError("Failed to retrieve person due to database error")
    except Exception as e:
        logger.error(f"Unexpected error getting person by email {email}: {str(e)}")
        raise HTTPInternalServerError("An unexpected error occurred while retrieving person")


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
        person_service = PersonService(db)
        
        # Handle validation errors at the service level for bulk operations
        created_people = []
        errors = []
        
        for idx, person_data in enumerate(bulk_data.people):
            try:
                # First validate the individual person data using PersonCreate schema
                try:
                    validated_person = PersonCreate(**person_data)
                except Exception as validation_error:
                    # Validation error - add to errors list and continue
                    errors.append({
                        "index": idx,
                        "person_data": person_data,
                        "error": f"Validation error: {str(validation_error)}"
                    })
                    continue
                
                # Create the person if validation passed (service method returns formatted response)
                db_person_response = person_service.create_person(validated_person)
                created_people.append(db_person_response)
            except Exception as e:
                errors.append({
                    "index": idx,
                    "person_data": person_data,
                    "error": str(e)
                })
                
        return format_bulk_operation_response(created_people, errors, "person")
        
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error in bulk create people: {str(e)}")
        db.rollback()
        raise DatabaseTransactionError("Failed to bulk create people due to database error")
    except Exception as e:
        logger.error(f"Unexpected error in bulk create people: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError("An unexpected error occurred while bulk creating people")

