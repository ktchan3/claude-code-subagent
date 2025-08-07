"""
API routes for Position management.

This module provides CRUD operations for managing positions,
including their relationships with departments and employees.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ...database.models import Position, Department, Employment, Person
from ...database.db import get_db
from ..dependencies import (
    get_database_session, get_pagination_params, get_search_params,
    get_common_query_params, PaginationParams, SearchParams, CommonQueryParams
)
from ..schemas.position import (
    PositionCreate, PositionUpdate, PositionResponse, PositionSummary,
    PositionWithEmployees, PositionWithHistory, PositionStatistics,
    PositionSearch, PositionBulkCreate, PositionTransfer
)
from ..schemas.common import (
    PaginatedResponse, SuccessResponse, create_success_response,
    create_paginated_response
)
from ...core.exceptions import (
    PositionNotFoundError, DepartmentNotFoundError, PositionExistsError,
    HTTPBadRequestError, HTTPInternalServerError, CannotDeletePositionError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/positions", tags=["positions"])


@router.post(
    "/",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new position",
    description="Create a new position within a department."
)
async def create_position(
    position_data: PositionCreate,
    db: Session = Depends(get_database_session)
) -> PositionResponse:
    """Create a new position."""
    try:
        # Check if department exists
        department = db.query(Department).filter(Department.id == position_data.department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(position_data.department_id))
        
        # Check if position with same title already exists in the department
        existing_position = db.query(Position).filter(
            Position.title == position_data.title,
            Position.department_id == position_data.department_id
        ).first()
        if existing_position:
            raise PositionExistsError(position_data.title, department.name)
        
        # Create new position
        db_position = Position(**position_data.model_dump())
        db.add(db_position)
        db.commit()
        db.refresh(db_position)
        
        # Fetch with department name for response
        db_position.department_name = department.name
        
        logger.info(f"Created new position: {db_position.title} in {department.name} ({db_position.id})")
        return PositionResponse.from_orm(db_position)
        
    except (DepartmentNotFoundError, PositionExistsError):
        raise
    except Exception as e:
        logger.error(f"Error creating position: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to create position: {str(e)}")


@router.get(
    "/",
    response_model=PaginatedResponse[PositionSummary],
    summary="List positions",
    description="Get a paginated list of positions with optional search and filtering."
)
async def list_positions(
    params: CommonQueryParams = Depends(get_common_query_params),
    department_id: Optional[UUID] = Query(None, description="Filter by department ID"),
    has_employees: Optional[bool] = Query(None, description="Filter by positions with active employees"),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PositionSummary]:
    """Get a paginated list of positions."""
    try:
        # Build base query with department join
        query = db.query(Position).join(Department)
        
        # Apply search filters
        if params.search.query:
            search_term = f"%{params.search.query}%"
            query = query.filter(
                or_(
                    Position.title.ilike(search_term),
                    Department.name.ilike(search_term)
                )
            )
        
        # Apply department filter
        if department_id:
            query = query.filter(Position.department_id == department_id)
        
        # Apply employee filter
        if has_employees is not None:
            if has_employees:
                query = query.join(Employment).filter(Employment.is_active == True)
            else:
                query = query.outerjoin(Employment).filter(
                    or_(Employment.id.is_(None), Employment.is_active == False)
                )
        
        # Apply sorting
        if params.search.sort_by:
            if params.search.sort_by == "department_name":
                sort_column = Department.name
            else:
                sort_column = getattr(Position, params.search.sort_by, None)
            
            if sort_column is not None:
                if params.search.is_descending:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                logger.warning(f"Invalid sort column: {params.search.sort_by}")
        else:
            query = query.order_by(Department.name, Position.title)
        
        # Get total count (distinct to handle joins)
        total = query.distinct().count()
        
        # Apply pagination
        offset, limit = params.pagination.get_offset_limit()
        positions = query.distinct().offset(offset).limit(limit).all()
        
        # Convert to response format
        position_summaries = []
        for pos in positions:
            summary_data = {
                "id": pos.id,
                "title": pos.title,
                "department_name": pos.department.name,
                "employee_count": pos.employee_count
            }
            position_summaries.append(PositionSummary(**summary_data))
        
        return create_paginated_response(
            items=position_summaries,
            page=params.pagination.page,
            size=params.pagination.size,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing positions: {str(e)}")
        raise HTTPInternalServerError(f"Failed to list positions: {str(e)}")


@router.get(
    "/{position_id}",
    response_model=PositionResponse,
    summary="Get position by ID",
    description="Get detailed information about a specific position."
)
async def get_position(
    position_id: UUID,
    db: Session = Depends(get_database_session)
) -> PositionResponse:
    """Get a position by ID."""
    try:
        position = db.query(Position).join(Department).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Add department name to response
        position.department_name = position.department.name
        return PositionResponse.from_orm(position)
        
    except PositionNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting position {position_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get position: {str(e)}")


@router.get(
    "/{position_id}/employees",
    response_model=PositionWithEmployees,
    summary="Get position with employees",
    description="Get position information including all employees in the position."
)
async def get_position_with_employees(
    position_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive employees"),
    db: Session = Depends(get_database_session)
) -> PositionWithEmployees:
    """Get a position with its employees."""
    try:
        position = db.query(Position).join(Department).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Get employees in this position
        query = (
            db.query(Employment)
            .join(Person)
            .filter(Employment.position_id == position_id)
        )
        
        if not include_inactive:
            query = query.filter(Employment.is_active == True)
        
        employments = query.all()
        
        # Format employee data
        employees_data = []
        for emp in employments:
            employee_data = {
                "id": emp.person_id,
                "full_name": emp.person.full_name,
                "email": emp.person.email,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "salary": float(emp.salary) if emp.salary else None,
                "is_active": emp.is_active
            }
            employees_data.append(employee_data)
        
        # Create response data
        position.department_name = position.department.name
        pos_data = PositionResponse.from_orm(position).model_dump()
        pos_data["employees"] = employees_data
        
        return PositionWithEmployees(**pos_data)
        
    except PositionNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting position employees {position_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get position employees: {str(e)}")


@router.get(
    "/{position_id}/history",
    response_model=PositionWithHistory,
    summary="Get position with employment history",
    description="Get position information including current and past employees."
)
async def get_position_with_history(
    position_id: UUID,
    db: Session = Depends(get_database_session)
) -> PositionWithHistory:
    """Get a position with its employment history."""
    try:
        position = db.query(Position).join(Department).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Get all employments for this position
        all_employments = (
            db.query(Employment)
            .join(Person)
            .filter(Employment.position_id == position_id)
            .order_by(Employment.start_date.desc())
            .all()
        )
        
        # Separate current and past employees
        current_employees = []
        past_employees = []
        
        for emp in all_employments:
            employee_data = {
                "id": emp.person_id,
                "full_name": emp.person.full_name,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "salary": float(emp.salary) if emp.salary else None
            }
            
            if emp.is_active:
                current_employees.append(employee_data)
            else:
                past_employees.append(employee_data)
        
        # Create response data
        position.department_name = position.department.name
        pos_data = PositionResponse.from_orm(position).model_dump()
        pos_data["current_employees"] = current_employees
        pos_data["past_employees"] = past_employees
        
        return PositionWithHistory(**pos_data)
        
    except PositionNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting position history {position_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get position history: {str(e)}")


@router.get(
    "/{position_id}/statistics",
    response_model=PositionStatistics,
    summary="Get position statistics",
    description="Get detailed statistics for a position including salary and tenure information."
)
async def get_position_statistics(
    position_id: UUID,
    db: Session = Depends(get_database_session)
) -> PositionStatistics:
    """Get statistics for a position."""
    try:
        position = db.query(Position).join(Department).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Get all employments in this position
        all_employments = (
            db.query(Employment)
            .filter(Employment.position_id == position_id)
            .all()
        )
        
        active_employments = [emp for emp in all_employments if emp.is_active]
        terminated_employments = [emp for emp in all_employments if not emp.is_active]
        
        # Calculate salary statistics
        salaries = [float(emp.salary) for emp in active_employments if emp.salary]
        average_salary = sum(salaries) / len(salaries) if salaries else None
        salary_range = {
            "min": min(salaries) if salaries else None,
            "max": max(salaries) if salaries else None
        } if salaries else None
        
        # Calculate average tenure
        total_tenure_months = 0
        tenure_count = 0
        for emp in active_employments:
            if emp.duration_days:
                total_tenure_months += emp.duration_days / 30.44  # Average days per month
                tenure_count += 1
        
        average_tenure_months = total_tenure_months / tenure_count if tenure_count > 0 else None
        
        # Calculate turnover rate
        turnover_rate = 0
        if len(all_employments) > 0:
            turnover_rate = (len(terminated_employments) / len(all_employments)) * 100
        
        return PositionStatistics(
            id=position.id,
            title=position.title,
            department_name=position.department.name,
            total_employees=len(all_employments),
            active_employees=len(active_employments),
            average_salary=average_salary,
            salary_range=salary_range,
            average_tenure_months=average_tenure_months,
            turnover_rate=turnover_rate
        )
        
    except PositionNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting position statistics {position_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get position statistics: {str(e)}")


@router.put(
    "/{position_id}",
    response_model=PositionResponse,
    summary="Update position",
    description="Update position information with the provided data."
)
async def update_position(
    position_id: UUID,
    position_data: PositionUpdate,
    db: Session = Depends(get_database_session)
) -> PositionResponse:
    """Update a position."""
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Check if department exists (if being changed)
        if position_data.department_id:
            department = db.query(Department).filter(Department.id == position_data.department_id).first()
            if not department:
                raise DepartmentNotFoundError(str(position_data.department_id))
        
        # Check if title is being updated and if it already exists in the department
        if position_data.title and position_data.title != position.title:
            dept_id = position_data.department_id or position.department_id
            existing_position = db.query(Position).filter(
                Position.title == position_data.title,
                Position.department_id == dept_id,
                Position.id != position_id
            ).first()
            if existing_position:
                department = db.query(Department).filter(Department.id == dept_id).first()
                raise PositionExistsError(position_data.title, department.name if department else "Unknown")
        
        # Update position fields
        update_data = position_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)
        
        db.commit()
        db.refresh(position)
        
        # Add department name for response
        position.department_name = position.department.name
        
        logger.info(f"Updated position: {position.title} ({position.id})")
        return PositionResponse.from_orm(position)
        
    except (PositionNotFoundError, DepartmentNotFoundError, PositionExistsError):
        raise
    except Exception as e:
        logger.error(f"Error updating position {position_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update position: {str(e)}")


@router.post(
    "/{position_id}/transfer",
    response_model=PositionResponse,
    summary="Transfer position to another department",
    description="Move a position to a different department."
)
async def transfer_position(
    position_id: UUID,
    transfer_data: PositionTransfer,
    db: Session = Depends(get_database_session)
) -> PositionResponse:
    """Transfer a position to another department."""
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Check if new department exists
        new_department = db.query(Department).filter(Department.id == transfer_data.new_department_id).first()
        if not new_department:
            raise DepartmentNotFoundError(str(transfer_data.new_department_id))
        
        # Check if position with same title already exists in the new department
        existing_position = db.query(Position).filter(
            Position.title == position.title,
            Position.department_id == transfer_data.new_department_id,
            Position.id != position_id
        ).first()
        if existing_position:
            raise PositionExistsError(position.title, new_department.name)
        
        old_department_name = position.department.name
        
        # Transfer position
        position.department_id = transfer_data.new_department_id
        db.commit()
        db.refresh(position)
        
        # Add department name for response
        position.department_name = new_department.name
        
        logger.info(f"Transferred position {position.title} from {old_department_name} to {new_department.name}")
        return PositionResponse.from_orm(position)
        
    except (PositionNotFoundError, DepartmentNotFoundError, PositionExistsError):
        raise
    except Exception as e:
        logger.error(f"Error transferring position {position_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to transfer position: {str(e)}")


@router.delete(
    "/{position_id}",
    response_model=SuccessResponse,
    summary="Delete position",
    description="Delete a position if it has no active employees."
)
async def delete_position(
    position_id: UUID,
    force: bool = Query(False, description="Force delete even if active employees exist"),
    db: Session = Depends(get_database_session)
) -> SuccessResponse:
    """Delete a position."""
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise PositionNotFoundError(str(position_id))
        
        # Check if position has active employees
        active_employees = [emp for emp in position.employments if emp.is_active]
        if active_employees and not force:
            raise CannotDeletePositionError(position.title, len(active_employees))
        
        position_title = position.title
        
        # Delete position (cascade will handle employment records if force=True)
        db.delete(position)
        db.commit()
        
        logger.info(f"Deleted position: {position_title} ({position_id})")
        return create_success_response(f"Position '{position_title}' deleted successfully")
        
    except (PositionNotFoundError, CannotDeletePositionError):
        raise
    except Exception as e:
        logger.error(f"Error deleting position {position_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to delete position: {str(e)}")


@router.get(
    "/search/advanced",
    response_model=PaginatedResponse[PositionSummary],
    summary="Advanced position search",
    description="Search positions with advanced filtering options."
)
async def search_positions(
    title: Optional[str] = Query(None, description="Search by position title"),
    department: Optional[str] = Query(None, description="Filter by department name"),
    department_id: Optional[UUID] = Query(None, description="Filter by department ID"),
    has_employees: Optional[bool] = Query(None, description="Filter by positions with active employees"),
    min_employees: Optional[int] = Query(None, ge=0, description="Minimum number of active employees"),
    max_employees: Optional[int] = Query(None, ge=0, description="Maximum number of active employees"),
    min_salary: Optional[float] = Query(None, ge=0, description="Minimum average salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="Maximum average salary"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[PositionSummary]:
    """Advanced search for positions."""
    try:
        # Validate ranges
        if min_employees is not None and max_employees is not None and max_employees < min_employees:
            raise HTTPBadRequestError("max_employees must be greater than or equal to min_employees")
        
        if min_salary is not None and max_salary is not None and max_salary < min_salary:
            raise HTTPBadRequestError("max_salary must be greater than or equal to min_salary")
        
        # Build base query
        query = db.query(Position).join(Department)
        
        # Apply filters
        if title:
            query = query.filter(Position.title.ilike(f"%{title}%"))
        
        if department:
            query = query.filter(Department.name.ilike(f"%{department}%"))
        
        if department_id:
            query = query.filter(Position.department_id == department_id)
        
        # For employee and salary filtering, we need to join with employments
        if (min_employees is not None or max_employees is not None or 
            has_employees is not None or min_salary is not None or max_salary is not None):
            
            # Subquery for employee counts and average salary per position
            stats_subquery = (
                db.query(
                    Employment.position_id,
                    func.count(Employment.id).label('employee_count'),
                    func.avg(Employment.salary).label('avg_salary')
                )
                .filter(Employment.is_active == True)
                .group_by(Employment.position_id)
                .subquery()
            )
            
            query = query.outerjoin(stats_subquery, Position.id == stats_subquery.c.position_id)
            
            if has_employees is not None:
                if has_employees:
                    query = query.filter(stats_subquery.c.employee_count > 0)
                else:
                    query = query.filter(
                        or_(
                            stats_subquery.c.employee_count.is_(None),
                            stats_subquery.c.employee_count == 0
                        )
                    )
            
            if min_employees is not None:
                query = query.filter(
                    func.coalesce(stats_subquery.c.employee_count, 0) >= min_employees
                )
            
            if max_employees is not None:
                query = query.filter(
                    func.coalesce(stats_subquery.c.employee_count, 0) <= max_employees
                )
            
            if min_salary is not None:
                query = query.filter(stats_subquery.c.avg_salary >= min_salary)
            
            if max_salary is not None:
                query = query.filter(stats_subquery.c.avg_salary <= max_salary)
        
        # Order by department and title
        query = query.order_by(Department.name, Position.title)
        
        # Get total count
        total = query.distinct().count()
        
        # Apply pagination
        offset, limit = pagination.get_offset_limit()
        positions = query.distinct().offset(offset).limit(limit).all()
        
        # Convert to response format
        position_summaries = []
        for pos in positions:
            summary_data = {
                "id": pos.id,
                "title": pos.title,
                "department_name": pos.department.name,
                "employee_count": pos.employee_count
            }
            position_summaries.append(PositionSummary(**summary_data))
        
        return create_paginated_response(
            items=position_summaries,
            page=pagination.page,
            size=pagination.size,
            total=total
        )
        
    except HTTPBadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error in advanced position search: {str(e)}")
        raise HTTPInternalServerError(f"Failed to search positions: {str(e)}")


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create positions",
    description="Create multiple positions in a single request."
)
async def bulk_create_positions(
    bulk_data: PositionBulkCreate,
    db: Session = Depends(get_database_session)
) -> dict:
    """Bulk create positions."""
    try:
        created_positions = []
        errors = []
        
        for i, pos_data in enumerate(bulk_data.positions):
            try:
                # Check if department exists
                department = db.query(Department).filter(Department.id == pos_data.department_id).first()
                if not department:
                    errors.append({
                        "index": i,
                        "title": pos_data.title,
                        "error": f"Department not found: {pos_data.department_id}"
                    })
                    continue
                
                # Check if position already exists in department
                existing_position = db.query(Position).filter(
                    Position.title == pos_data.title,
                    Position.department_id == pos_data.department_id
                ).first()
                if existing_position:
                    errors.append({
                        "index": i,
                        "title": pos_data.title,
                        "error": f"Position already exists in department: {pos_data.title}"
                    })
                    continue
                
                # Create position
                db_position = Position(**pos_data.model_dump())
                db.add(db_position)
                db.flush()  # Get ID without committing
                
                created_positions.append({
                    "index": i,
                    "id": str(db_position.id),
                    "title": db_position.title,
                    "department": department.name
                })
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "title": pos_data.title,
                    "error": str(e)
                })
        
        # Commit all successful creations
        if created_positions:
            db.commit()
        
        logger.info(f"Bulk created {len(created_positions)} positions with {len(errors)} errors")
        
        return {
            "success_count": len(created_positions),
            "error_count": len(errors),
            "created_positions": created_positions,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk create positions: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to bulk create positions: {str(e)}")


# Health check for positions endpoint
@router.get(
    "/health",
    response_model=dict,
    summary="Positions endpoint health check",
    description="Check the health of the positions endpoint."
)
async def positions_health_check(
    db: Session = Depends(get_database_session)
) -> dict:
    """Health check for positions endpoint."""
    try:
        # Test database query
        count = db.query(Position).count()
        
        return {
            "status": "healthy",
            "total_positions": count,
            "timestamp": func.now()
        }
        
    except Exception as e:
        logger.error(f"Positions health check failed: {str(e)}")
        raise HTTPInternalServerError(f"Positions endpoint unhealthy: {str(e)}")