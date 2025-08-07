"""
API routes for Employment management.

This module provides CRUD operations for managing employment records,
including creation, updates, termination, and history tracking.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

from ...database.models import Employment, Person, Position, Department
from ...database.db import get_db
from ..dependencies import (
    get_database_session, get_pagination_params, get_search_params,
    get_common_query_params, get_date_range_params, PaginationParams, 
    SearchParams, CommonQueryParams, DateRangeParams
)
from ..schemas.employment import (
    EmploymentCreate, EmploymentUpdate, EmploymentTerminate, EmploymentResponse,
    EmploymentSummary, EmploymentHistory, EmploymentStatistics, EmploymentSearch,
    EmploymentBulkCreate, EmploymentBulkTerminate, EmploymentTransfer
)
from ..schemas.common import (
    PaginatedResponse, SuccessResponse, create_success_response,
    create_paginated_response
)
from ...core.exceptions import (
    EmploymentNotFoundError, PersonNotFoundError, PositionNotFoundError,
    ActiveEmploymentExistsError, InvalidEmploymentPeriodError,
    CannotTerminateEmploymentError, HTTPBadRequestError, HTTPInternalServerError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/employment", tags=["employment"])


@router.post(
    "/",
    response_model=EmploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employment record",
    description="Create a new employment record linking a person to a position."
)
async def create_employment(
    employment_data: EmploymentCreate,
    db: Session = Depends(get_database_session)
) -> EmploymentResponse:
    """Create a new employment record."""
    try:
        # Check if person exists
        person = db.query(Person).filter(Person.id == employment_data.person_id).first()
        if not person:
            raise PersonNotFoundError(str(employment_data.person_id))
        
        # Check if position exists
        position = db.query(Position).join(Department).filter(Position.id == employment_data.position_id).first()
        if not position:
            raise PositionNotFoundError(str(employment_data.position_id))
        
        # Check if person already has active employment
        existing_employment = db.query(Employment).filter(
            Employment.person_id == employment_data.person_id,
            Employment.is_active == True
        ).first()
        if existing_employment:
            raise ActiveEmploymentExistsError(person.full_name)
        
        # Create new employment
        db_employment = Employment(**employment_data.model_dump())
        db.add(db_employment)
        db.commit()
        db.refresh(db_employment)
        
        # Add related entity information for response
        db_employment.person_name = person.full_name
        db_employment.person_email = person.email
        db_employment.position_title = position.title
        db_employment.department_name = position.department.name
        
        logger.info(f"Created employment: {person.full_name} -> {position.title} ({db_employment.id})")
        return EmploymentResponse.from_orm(db_employment)
        
    except (PersonNotFoundError, PositionNotFoundError, ActiveEmploymentExistsError):
        raise
    except Exception as e:
        logger.error(f"Error creating employment: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to create employment: {str(e)}")


@router.get(
    "/",
    response_model=PaginatedResponse[EmploymentSummary],
    summary="List employment records",
    description="Get a paginated list of employment records with optional search and filtering."
)
async def list_employment(
    params: CommonQueryParams = Depends(get_common_query_params),
    department: Optional[str] = Query(None, description="Filter by department name"),
    position: Optional[str] = Query(None, description="Filter by position title"),
    person_name: Optional[str] = Query(None, description="Filter by person name"),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[EmploymentSummary]:
    """Get a paginated list of employment records."""
    try:
        # Build base query with joins
        query = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
        )
        
        # Apply search filters
        if params.search.query:
            search_term = f"%{params.search.query}%"
            query = query.filter(
                or_(
                    Person.first_name.ilike(search_term),
                    Person.last_name.ilike(search_term),
                    func.concat(Person.first_name, ' ', Person.last_name).ilike(search_term),
                    Position.title.ilike(search_term),
                    Department.name.ilike(search_term)
                )
            )
        
        # Apply specific filters
        if department:
            query = query.filter(Department.name.ilike(f"%{department}%"))
        
        if position:
            query = query.filter(Position.title.ilike(f"%{position}%"))
        
        if person_name:
            query = query.filter(
                func.concat(Person.first_name, ' ', Person.last_name).ilike(f"%{person_name}%")
            )
        
        # Apply active filter
        if params.active is not None:
            query = query.filter(Employment.is_active == params.active)
        
        # Apply date range filters
        if params.date_range.start_date:
            query = query.filter(Employment.start_date >= params.date_range.start_date)
        
        if params.date_range.end_date:
            query = query.filter(
                or_(
                    Employment.end_date.is_(None),
                    Employment.end_date <= params.date_range.end_date
                )
            )
        
        # Apply sorting
        if params.search.sort_by:
            if params.search.sort_by == "person_name":
                sort_column = func.concat(Person.first_name, ' ', Person.last_name)
            elif params.search.sort_by == "position_title":
                sort_column = Position.title
            elif params.search.sort_by == "department_name":
                sort_column = Department.name
            else:
                sort_column = getattr(Employment, params.search.sort_by, None)
            
            if sort_column is not None:
                if params.search.is_descending:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                logger.warning(f"Invalid sort column: {params.search.sort_by}")
        else:
            query = query.order_by(desc(Employment.start_date))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset, limit = params.pagination.get_offset_limit()
        employments = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        employment_summaries = []
        for emp in employments:
            summary_data = {
                "id": emp.id,
                "person_name": emp.person.full_name,
                "position_title": emp.position.title,
                "department_name": emp.position.department.name,
                "start_date": emp.start_date,
                "is_active": emp.is_active
            }
            employment_summaries.append(EmploymentSummary(**summary_data))
        
        return create_paginated_response(
            items=employment_summaries,
            page=params.pagination.page,
            size=params.pagination.size,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing employment records: {str(e)}")
        raise HTTPInternalServerError(f"Failed to list employment records: {str(e)}")


@router.get(
    "/{employment_id}",
    response_model=EmploymentResponse,
    summary="Get employment record by ID",
    description="Get detailed information about a specific employment record."
)
async def get_employment(
    employment_id: UUID,
    db: Session = Depends(get_database_session)
) -> EmploymentResponse:
    """Get an employment record by ID."""
    try:
        employment = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
            .filter(Employment.id == employment_id)
            .first()
        )
        if not employment:
            raise EmploymentNotFoundError(str(employment_id))
        
        # Add related entity information for response
        employment.person_name = employment.person.full_name
        employment.person_email = employment.person.email
        employment.position_title = employment.position.title
        employment.department_name = employment.position.department.name
        
        return EmploymentResponse.from_orm(employment)
        
    except EmploymentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting employment {employment_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get employment record: {str(e)}")


@router.get(
    "/person/{person_id}",
    response_model=EmploymentHistory,
    summary="Get employment history for a person",
    description="Get complete employment history for a specific person."
)
async def get_person_employment_history(
    person_id: UUID,
    db: Session = Depends(get_database_session)
) -> EmploymentHistory:
    """Get employment history for a person."""
    try:
        # Check if person exists
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Get all employment records for this person
        employments = (
            db.query(Employment)
            .join(Position)
            .join(Department)
            .filter(Employment.person_id == person_id)
            .order_by(desc(Employment.start_date))
            .all()
        )
        
        # Separate current and past employments
        current_employment = None
        past_employments = []
        total_tenure_years = 0
        
        for emp in employments:
            employment_data = {
                "id": emp.id,
                "position_title": emp.position.title,
                "department_name": emp.position.department.name,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "salary": float(emp.salary) if emp.salary else None,
                "duration_years": emp.duration_years
            }
            
            # Add to total tenure
            if emp.duration_years:
                total_tenure_years += emp.duration_years
            
            if emp.is_active:
                current_employment = employment_data
            else:
                past_employments.append(employment_data)
        
        return EmploymentHistory(
            person_id=person_id,
            person_name=person.full_name,
            total_employments=len(employments),
            current_employment=current_employment,
            past_employments=past_employments,
            total_tenure_years=round(total_tenure_years, 2)
        )
        
    except PersonNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting employment history for person {person_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get employment history: {str(e)}")


@router.put(
    "/{employment_id}",
    response_model=EmploymentResponse,
    summary="Update employment record",
    description="Update employment information such as salary or position."
)
async def update_employment(
    employment_id: UUID,
    employment_data: EmploymentUpdate,
    db: Session = Depends(get_database_session)
) -> EmploymentResponse:
    """Update an employment record."""
    try:
        employment = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
            .filter(Employment.id == employment_id)
            .first()
        )
        if not employment:
            raise EmploymentNotFoundError(str(employment_id))
        
        # Check if position is being changed
        if employment_data.position_id:
            new_position = db.query(Position).join(Department).filter(
                Position.id == employment_data.position_id
            ).first()
            if not new_position:
                raise PositionNotFoundError(str(employment_data.position_id))
        
        # Update employment fields
        update_data = employment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employment, field, value)
        
        db.commit()
        db.refresh(employment)
        
        # Add related entity information for response
        employment.person_name = employment.person.full_name
        employment.person_email = employment.person.email
        employment.position_title = employment.position.title
        employment.department_name = employment.position.department.name
        
        logger.info(f"Updated employment: {employment.person.full_name} -> {employment.position.title} ({employment.id})")
        return EmploymentResponse.from_orm(employment)
        
    except (EmploymentNotFoundError, PositionNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error updating employment {employment_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update employment: {str(e)}")


@router.post(
    "/{employment_id}/terminate",
    response_model=EmploymentResponse,
    summary="Terminate employment",
    description="Terminate an active employment record."
)
async def terminate_employment(
    employment_id: UUID,
    termination_data: EmploymentTerminate,
    db: Session = Depends(get_database_session)
) -> EmploymentResponse:
    """Terminate an employment record."""
    try:
        employment = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
            .filter(Employment.id == employment_id)
            .first()
        )
        if not employment:
            raise EmploymentNotFoundError(str(employment_id))
        
        # Check if employment is already terminated
        if not employment.is_active:
            raise CannotTerminateEmploymentError(str(employment_id))
        
        # Validate end date
        if termination_data.end_date < employment.start_date:
            raise InvalidEmploymentPeriodError("End date cannot be before start date")
        
        # Terminate employment
        employment.terminate(termination_data.end_date)
        db.commit()
        db.refresh(employment)
        
        # Add related entity information for response
        employment.person_name = employment.person.full_name
        employment.person_email = employment.person.email
        employment.position_title = employment.position.title
        employment.department_name = employment.position.department.name
        
        logger.info(f"Terminated employment: {employment.person.full_name} -> {employment.position.title} ({employment.id})")
        return EmploymentResponse.from_orm(employment)
        
    except (EmploymentNotFoundError, CannotTerminateEmploymentError, InvalidEmploymentPeriodError):
        raise
    except Exception as e:
        logger.error(f"Error terminating employment {employment_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to terminate employment: {str(e)}")


@router.post(
    "/{employment_id}/transfer",
    response_model=EmploymentResponse,
    summary="Transfer employee to new position",
    description="Transfer an employee to a different position."
)
async def transfer_employee(
    employment_id: UUID,
    transfer_data: EmploymentTransfer,
    db: Session = Depends(get_database_session)
) -> EmploymentResponse:
    """Transfer an employee to a new position."""
    try:
        employment = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
            .filter(Employment.id == employment_id)
            .first()
        )
        if not employment:
            raise EmploymentNotFoundError(str(employment_id))
        
        # Check if employment is active
        if not employment.is_active:
            raise HTTPBadRequestError("Cannot transfer terminated employment")
        
        # Check if new position exists
        new_position = db.query(Position).join(Department).filter(
            Position.id == transfer_data.new_position_id
        ).first()
        if not new_position:
            raise PositionNotFoundError(str(transfer_data.new_position_id))
        
        # Validate transfer date
        if transfer_data.transfer_date < employment.start_date:
            raise InvalidEmploymentPeriodError("Transfer date cannot be before employment start date")
        
        old_position_title = employment.position.title
        old_department_name = employment.position.department.name
        
        # Update employment record
        employment.position_id = transfer_data.new_position_id
        if transfer_data.new_salary:
            employment.salary = transfer_data.new_salary
        
        db.commit()
        db.refresh(employment)
        
        # Add related entity information for response
        employment.person_name = employment.person.full_name
        employment.person_email = employment.person.email
        employment.position_title = employment.position.title
        employment.department_name = employment.position.department.name
        
        logger.info(f"Transferred employee: {employment.person.full_name} from {old_position_title} ({old_department_name}) to {employment.position.title} ({employment.position.department.name})")
        return EmploymentResponse.from_orm(employment)
        
    except (EmploymentNotFoundError, PositionNotFoundError, InvalidEmploymentPeriodError, HTTPBadRequestError):
        raise
    except Exception as e:
        logger.error(f"Error transferring employee {employment_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to transfer employee: {str(e)}")


@router.delete(
    "/{employment_id}",
    response_model=SuccessResponse,
    summary="Delete employment record",
    description="Delete an employment record completely."
)
async def delete_employment(
    employment_id: UUID,
    db: Session = Depends(get_database_session)
) -> SuccessResponse:
    """Delete an employment record."""
    try:
        employment = db.query(Employment).filter(Employment.id == employment_id).first()
        if not employment:
            raise EmploymentNotFoundError(str(employment_id))
        
        # Get employment info for logging
        employment_info = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .filter(Employment.id == employment_id)
            .first()
        )
        
        person_name = employment_info.person.full_name if employment_info else "Unknown"
        position_title = employment_info.position.title if employment_info else "Unknown"
        
        # Delete employment
        db.delete(employment)
        db.commit()
        
        logger.info(f"Deleted employment record: {person_name} -> {position_title} ({employment_id})")
        return create_success_response("Employment record deleted successfully")
        
    except EmploymentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting employment {employment_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to delete employment record: {str(e)}")


@router.get(
    "/search/advanced",
    response_model=PaginatedResponse[EmploymentSummary],
    summary="Advanced employment search",
    description="Search employment records with advanced filtering options."
)
async def search_employment(
    person_name: Optional[str] = Query(None, description="Search by employee name"),
    person_email: Optional[str] = Query(None, description="Search by employee email"),
    position: Optional[str] = Query(None, description="Filter by position title"),
    department: Optional[str] = Query(None, description="Filter by department name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    start_date_from: Optional[date] = Query(None, description="Filter by start date (from)"),
    start_date_to: Optional[date] = Query(None, description="Filter by start date (to)"),
    min_salary: Optional[float] = Query(None, ge=0, description="Minimum salary filter"),
    max_salary: Optional[float] = Query(None, ge=0, description="Maximum salary filter"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[EmploymentSummary]:
    """Advanced search for employment records."""
    try:
        # Validate ranges
        if start_date_from and start_date_to and start_date_to < start_date_from:
            raise HTTPBadRequestError("start_date_to must be greater than or equal to start_date_from")
        
        if min_salary is not None and max_salary is not None and max_salary < min_salary:
            raise HTTPBadRequestError("max_salary must be greater than or equal to min_salary")
        
        # Build base query
        query = (
            db.query(Employment)
            .join(Person)
            .join(Position)
            .join(Department)
        )
        
        # Apply filters
        if person_name:
            query = query.filter(
                func.concat(Person.first_name, ' ', Person.last_name).ilike(f"%{person_name}%")
            )
        
        if person_email:
            query = query.filter(Person.email.ilike(f"%{person_email}%"))
        
        if position:
            query = query.filter(Position.title.ilike(f"%{position}%"))
        
        if department:
            query = query.filter(Department.name.ilike(f"%{department}%"))
        
        if is_active is not None:
            query = query.filter(Employment.is_active == is_active)
        
        if start_date_from:
            query = query.filter(Employment.start_date >= start_date_from)
        
        if start_date_to:
            query = query.filter(Employment.start_date <= start_date_to)
        
        if min_salary is not None:
            query = query.filter(Employment.salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(Employment.salary <= max_salary)
        
        # Order by start date (newest first)
        query = query.order_by(desc(Employment.start_date))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset, limit = pagination.get_offset_limit()
        employments = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        employment_summaries = []
        for emp in employments:
            summary_data = {
                "id": emp.id,
                "person_name": emp.person.full_name,
                "position_title": emp.position.title,
                "department_name": emp.position.department.name,
                "start_date": emp.start_date,
                "is_active": emp.is_active
            }
            employment_summaries.append(EmploymentSummary(**summary_data))
        
        return create_paginated_response(
            items=employment_summaries,
            page=pagination.page,
            size=pagination.size,
            total=total
        )
        
    except HTTPBadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error in advanced employment search: {str(e)}")
        raise HTTPInternalServerError(f"Failed to search employment records: {str(e)}")


@router.get(
    "/statistics/overview",
    response_model=EmploymentStatistics,
    summary="Get employment statistics",
    description="Get comprehensive statistics about employment records."
)
async def get_employment_statistics(
    db: Session = Depends(get_database_session)
) -> EmploymentStatistics:
    """Get employment statistics."""
    try:
        # Get all employment records
        all_employments = db.query(Employment).all()
        active_employments = [emp for emp in all_employments if emp.is_active]
        terminated_employments = [emp for emp in all_employments if not emp.is_active]
        
        # Calculate average tenure
        total_tenure_months = 0
        tenure_count = 0
        for emp in all_employments:
            if emp.duration_days:
                total_tenure_months += emp.duration_days / 30.44  # Average days per month
                tenure_count += 1
        
        average_tenure_months = total_tenure_months / tenure_count if tenure_count > 0 else 0
        
        # Calculate salary statistics
        salaries = [float(emp.salary) for emp in active_employments if emp.salary]
        average_salary = sum(salaries) / len(salaries) if salaries else None
        
        salary_statistics = {}
        if salaries:
            import statistics
            salary_statistics = {
                "min": min(salaries),
                "max": max(salaries),
                "median": statistics.median(salaries),
                "std_dev": statistics.stdev(salaries) if len(salaries) > 1 else 0
            }
        
        # Calculate turnover rate
        turnover_rate = 0
        if len(all_employments) > 0:
            turnover_rate = (len(terminated_employments) / len(all_employments)) * 100
        
        # Department breakdown
        dept_stats = (
            db.query(
                Department.name,
                func.count(Employment.id).label('total_count'),
                func.sum(func.case([(Employment.is_active == True, 1)], else_=0)).label('active_count'),
                func.avg(func.case([(Employment.is_active == True, Employment.salary)])).label('avg_salary')
            )
            .join(Position)
            .join(Employment)
            .group_by(Department.name)
            .all()
        )
        
        department_breakdown = []
        for dept_name, total_count, active_count, avg_salary in dept_stats:
            department_breakdown.append({
                "department": dept_name,
                "total_count": total_count,
                "active_count": active_count or 0,
                "average_salary": float(avg_salary) if avg_salary else None
            })
        
        # Position breakdown
        pos_stats = (
            db.query(
                Position.title,
                func.count(Employment.id).label('total_count'),
                func.sum(func.case([(Employment.is_active == True, 1)], else_=0)).label('active_count'),
                func.avg(func.case([(Employment.is_active == True, Employment.salary)])).label('avg_salary')
            )
            .join(Employment)
            .group_by(Position.title)
            .all()
        )
        
        position_breakdown = []
        for pos_title, total_count, active_count, avg_salary in pos_stats:
            position_breakdown.append({
                "position": pos_title,
                "total_count": total_count,
                "active_count": active_count or 0,
                "average_salary": float(avg_salary) if avg_salary else None
            })
        
        return EmploymentStatistics(
            total_employments=len(all_employments),
            active_employments=len(active_employments),
            terminated_employments=len(terminated_employments),
            average_tenure_months=round(average_tenure_months, 2),
            average_salary=average_salary,
            salary_statistics=salary_statistics,
            turnover_rate=round(turnover_rate, 2),
            department_breakdown=department_breakdown,
            position_breakdown=position_breakdown
        )
        
    except Exception as e:
        logger.error(f"Error getting employment statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get employment statistics: {str(e)}")


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create employment records",
    description="Create multiple employment records in a single request."
)
async def bulk_create_employment(
    bulk_data: EmploymentBulkCreate,
    db: Session = Depends(get_database_session)
) -> dict:
    """Bulk create employment records."""
    try:
        created_employments = []
        errors = []
        
        for i, emp_data in enumerate(bulk_data.employments):
            try:
                # Check if person exists
                person = db.query(Person).filter(Person.id == emp_data.person_id).first()
                if not person:
                    errors.append({
                        "index": i,
                        "person_id": str(emp_data.person_id),
                        "error": f"Person not found: {emp_data.person_id}"
                    })
                    continue
                
                # Check if position exists
                position = db.query(Position).filter(Position.id == emp_data.position_id).first()
                if not position:
                    errors.append({
                        "index": i,
                        "position_id": str(emp_data.position_id),
                        "error": f"Position not found: {emp_data.position_id}"
                    })
                    continue
                
                # Check if person already has active employment
                existing_employment = db.query(Employment).filter(
                    Employment.person_id == emp_data.person_id,
                    Employment.is_active == True
                ).first()
                if existing_employment:
                    errors.append({
                        "index": i,
                        "person_name": person.full_name,
                        "error": f"Person already has active employment: {person.full_name}"
                    })
                    continue
                
                # Create employment
                db_employment = Employment(**emp_data.model_dump())
                db.add(db_employment)
                db.flush()  # Get ID without committing
                
                created_employments.append({
                    "index": i,
                    "id": str(db_employment.id),
                    "person_name": person.full_name,
                    "position_title": position.title
                })
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e)
                })
        
        # Commit all successful creations
        if created_employments:
            db.commit()
        
        logger.info(f"Bulk created {len(created_employments)} employment records with {len(errors)} errors")
        
        return {
            "success_count": len(created_employments),
            "error_count": len(errors),
            "created_employments": created_employments,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk create employment: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to bulk create employment records: {str(e)}")


# Health check for employment endpoint
@router.get(
    "/health",
    response_model=dict,
    summary="Employment endpoint health check",
    description="Check the health of the employment endpoint."
)
async def employment_health_check(
    db: Session = Depends(get_database_session)
) -> dict:
    """Health check for employment endpoint."""
    try:
        # Test database query
        total_count = db.query(Employment).count()
        active_count = db.query(Employment).filter(Employment.is_active == True).count()
        
        return {
            "status": "healthy",
            "total_employment_records": total_count,
            "active_employment_records": active_count,
            "timestamp": func.now()
        }
        
    except Exception as e:
        logger.error(f"Employment health check failed: {str(e)}")
        raise HTTPInternalServerError(f"Employment endpoint unhealthy: {str(e)}")