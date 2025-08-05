"""
API routes for Department management.

This module provides CRUD operations for managing departments,
including their relationships with positions and employees.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ...database.models import Department, Position, Employment, Person
from ...database.db import get_db
from ..dependencies import (
    get_database_session, get_pagination_params, get_search_params,
    get_common_query_params, PaginationParams, SearchParams, CommonQueryParams
)
from ..schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentSummary,
    DepartmentWithPositions, DepartmentWithEmployees, DepartmentStatistics,
    DepartmentSearch, DepartmentBulkCreate
)
from ..schemas.common import (
    PaginatedResponse, SuccessResponse, create_success_response,
    create_paginated_response
)
from ...core.exceptions import (
    DepartmentNotFoundError, DepartmentNameExistsError, HTTPBadRequestError,
    HTTPInternalServerError, CannotDeleteDepartmentError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/departments", tags=["departments"])


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
    description="Create a new department with the provided information."
)
async def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_database_session)
) -> DepartmentResponse:
    """Create a new department."""
    try:
        # Check if department name already exists
        existing_department = db.query(Department).filter(
            Department.name == department_data.name
        ).first()
        if existing_department:
            raise DepartmentNameExistsError(department_data.name)
        
        # Create new department
        db_department = Department(**department_data.dict())
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
        
        logger.info(f"Created new department: {db_department.name} ({db_department.id})")
        return DepartmentResponse.from_orm(db_department)
        
    except DepartmentNameExistsError:
        raise
    except Exception as e:
        logger.error(f"Error creating department: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to create department: {str(e)}")


@router.get(
    "/",
    response_model=PaginatedResponse[DepartmentSummary],
    summary="List departments",
    description="Get a paginated list of departments with optional search and filtering."
)
async def list_departments(
    params: CommonQueryParams = Depends(get_common_query_params),
    has_positions: Optional[bool] = Query(None, description="Filter by departments with positions"),
    has_employees: Optional[bool] = Query(None, description="Filter by departments with active employees"),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[DepartmentSummary]:
    """Get a paginated list of departments."""
    try:
        # Build base query
        query = db.query(Department)
        
        # Apply search filters
        if params.search.query:
            search_term = f"%{params.search.query}%"
            query = query.filter(Department.name.ilike(search_term))
        
        # Apply position filter
        if has_positions is not None:
            if has_positions:
                query = query.join(Position)
            else:
                query = query.outerjoin(Position).filter(Position.id.is_(None))
        
        # Apply employee filter
        if has_employees is not None:
            if has_employees:
                query = query.join(Position).join(Employment).filter(Employment.is_active == True)
            else:
                query = query.outerjoin(Position).outerjoin(Employment).filter(
                    or_(Employment.id.is_(None), Employment.is_active == False)
                )
        
        # Apply sorting
        if params.search.sort_by:
            sort_column = getattr(Department, params.search.sort_by, None)
            if sort_column:
                if params.search.is_descending:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                logger.warning(f"Invalid sort column: {params.search.sort_by}")
        else:
            query = query.order_by(Department.name)
        
        # Get total count (distinct to handle joins)
        total = query.distinct().count()
        
        # Apply pagination
        offset, limit = params.pagination.get_offset_limit()
        departments = query.distinct().offset(offset).limit(limit).all()
        
        # Convert to response format
        department_summaries = []
        for dept in departments:
            summary_data = {
                "id": dept.id,
                "name": dept.name,
                "position_count": dept.position_count,
                "active_employee_count": dept.active_employment_count
            }
            department_summaries.append(DepartmentSummary(**summary_data))
        
        return create_paginated_response(
            items=department_summaries,
            page=params.pagination.page,
            size=params.pagination.size,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing departments: {str(e)}")
        raise HTTPInternalServerError(f"Failed to list departments: {str(e)}")


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department by ID",
    description="Get detailed information about a specific department."
)
async def get_department(
    department_id: UUID,
    db: Session = Depends(get_database_session)
) -> DepartmentResponse:
    """Get a department by ID."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        return DepartmentResponse.from_orm(department)
        
    except DepartmentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting department {department_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get department: {str(e)}")


@router.get(
    "/{department_id}/positions",
    response_model=DepartmentWithPositions,
    summary="Get department with positions",
    description="Get department information including all positions in the department."
)
async def get_department_with_positions(
    department_id: UUID,
    db: Session = Depends(get_database_session)
) -> DepartmentWithPositions:
    """Get a department with its positions."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        # Get positions with employee counts
        positions_data = []
        for position in department.positions:
            position_data = {
                "id": position.id,
                "title": position.title,
                "description": position.description,
                "employee_count": position.employee_count,
                "created_at": position.created_at,
                "updated_at": position.updated_at
            }
            positions_data.append(position_data)
        
        # Create response data
        dept_data = DepartmentResponse.from_orm(department).dict()
        dept_data["positions"] = positions_data
        
        return DepartmentWithPositions(**dept_data)
        
    except DepartmentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting department positions {department_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get department positions: {str(e)}")


@router.get(
    "/{department_id}/employees",
    response_model=DepartmentWithEmployees,
    summary="Get department with employees",
    description="Get department information including all active employees."
)
async def get_department_with_employees(
    department_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive employees"),
    db: Session = Depends(get_database_session)
) -> DepartmentWithEmployees:
    """Get a department with its employees."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        # Get employees in this department
        query = (
            db.query(Employment)
            .join(Position)
            .join(Person)
            .filter(Position.department_id == department_id)
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
                "position": emp.position.title,
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "salary": float(emp.salary) if emp.salary else None,
                "is_active": emp.is_active
            }
            employees_data.append(employee_data)
        
        # Create response data
        dept_data = DepartmentResponse.from_orm(department).dict()
        dept_data["employees"] = employees_data
        
        return DepartmentWithEmployees(**dept_data)
        
    except DepartmentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting department employees {department_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get department employees: {str(e)}")


@router.get(
    "/{department_id}/statistics",
    response_model=DepartmentStatistics,
    summary="Get department statistics",
    description="Get detailed statistics for a department including salary and tenure information."
)
async def get_department_statistics(
    department_id: UUID,
    db: Session = Depends(get_database_session)
) -> DepartmentStatistics:
    """Get statistics for a department."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        # Get all employments in this department
        all_employments = (
            db.query(Employment)
            .join(Position)
            .filter(Position.department_id == department_id)
            .all()
        )
        
        active_employments = [emp for emp in all_employments if emp.is_active]
        
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
        
        return DepartmentStatistics(
            id=department.id,
            name=department.name,
            total_positions=len(department.positions),
            total_employees=len(all_employments),
            active_employees=len(active_employments),
            average_salary=average_salary,
            salary_range=salary_range,
            average_tenure_months=average_tenure_months
        )
        
    except DepartmentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting department statistics {department_id}: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get department statistics: {str(e)}")


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update department information with the provided data."
)
async def update_department(
    department_id: UUID,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_database_session)
) -> DepartmentResponse:
    """Update a department."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        # Check if name is being updated and if it already exists
        if department_data.name and department_data.name != department.name:
            existing_department = db.query(Department).filter(
                Department.name == department_data.name
            ).first()
            if existing_department:
                raise DepartmentNameExistsError(department_data.name)
        
        # Update department fields
        update_data = department_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(department, field, value)
        
        db.commit()
        db.refresh(department)
        
        logger.info(f"Updated department: {department.name} ({department.id})")
        return DepartmentResponse.from_orm(department)
        
    except (DepartmentNotFoundError, DepartmentNameExistsError):
        raise
    except Exception as e:
        logger.error(f"Error updating department {department_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to update department: {str(e)}")


@router.delete(
    "/{department_id}",
    response_model=SuccessResponse,
    summary="Delete department",
    description="Delete a department if it has no positions."
)
async def delete_department(
    department_id: UUID,
    force: bool = Query(False, description="Force delete even if positions exist"),
    db: Session = Depends(get_database_session)
) -> SuccessResponse:
    """Delete a department."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise DepartmentNotFoundError(str(department_id))
        
        # Check if department has positions
        if department.positions and not force:
            raise CannotDeleteDepartmentError(department.name, len(department.positions))
        
        department_name = department.name
        
        # Delete department (cascade will handle positions and employments if force=True)
        db.delete(department)
        db.commit()
        
        logger.info(f"Deleted department: {department_name} ({department_id})")
        return create_success_response(f"Department '{department_name}' deleted successfully")
        
    except (DepartmentNotFoundError, CannotDeleteDepartmentError):
        raise
    except Exception as e:
        logger.error(f"Error deleting department {department_id}: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to delete department: {str(e)}")


@router.get(
    "/search/advanced",
    response_model=PaginatedResponse[DepartmentSummary],
    summary="Advanced department search",
    description="Search departments with advanced filtering options."
)
async def search_departments(
    name: Optional[str] = Query(None, description="Search by department name"),
    has_positions: Optional[bool] = Query(None, description="Filter by departments with positions"),
    has_employees: Optional[bool] = Query(None, description="Filter by departments with active employees"),
    min_employees: Optional[int] = Query(None, ge=0, description="Minimum number of active employees"),
    max_employees: Optional[int] = Query(None, ge=0, description="Maximum number of active employees"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_database_session)
) -> PaginatedResponse[DepartmentSummary]:
    """Advanced search for departments."""
    try:
        # Validate employee range
        if min_employees is not None and max_employees is not None and max_employees < min_employees:
            raise HTTPBadRequestError("max_employees must be greater than or equal to min_employees")
        
        # Build base query
        query = db.query(Department)
        
        # Apply filters
        if name:
            query = query.filter(Department.name.ilike(f"%{name}%"))
        
        # For employee count filtering, we need to join and group
        if min_employees is not None or max_employees is not None or has_employees is not None:
            # Subquery to count active employees per department
            employee_count_subquery = (
                db.query(
                    Position.department_id,
                    func.count(Employment.id).label('employee_count')
                )
                .join(Employment, Employment.position_id == Position.id)
                .filter(Employment.is_active == True)
                .group_by(Position.department_id)
                .subquery()
            )
            
            query = query.outerjoin(employee_count_subquery, 
                                  Department.id == employee_count_subquery.c.department_id)
            
            if has_employees is not None:
                if has_employees:
                    query = query.filter(employee_count_subquery.c.employee_count > 0)
                else:
                    query = query.filter(
                        or_(
                            employee_count_subquery.c.employee_count.is_(None),
                            employee_count_subquery.c.employee_count == 0
                        )
                    )
            
            if min_employees is not None:
                query = query.filter(
                    func.coalesce(employee_count_subquery.c.employee_count, 0) >= min_employees
                )
            
            if max_employees is not None:
                query = query.filter(
                    func.coalesce(employee_count_subquery.c.employee_count, 0) <= max_employees
                )
        
        if has_positions is not None:
            if has_positions:
                query = query.join(Position)
            else:
                query = query.outerjoin(Position).filter(Position.id.is_(None))
        
        # Order by name
        query = query.order_by(Department.name)
        
        # Get total count
        total = query.distinct().count()
        
        # Apply pagination
        offset, limit = pagination.get_offset_limit()
        departments = query.distinct().offset(offset).limit(limit).all()
        
        # Convert to response format
        department_summaries = []
        for dept in departments:
            summary_data = {
                "id": dept.id,
                "name": dept.name,
                "position_count": dept.position_count,
                "active_employee_count": dept.active_employment_count
            }
            department_summaries.append(DepartmentSummary(**summary_data))
        
        return create_paginated_response(
            items=department_summaries,
            page=pagination.page,
            size=pagination.size,
            total=total
        )
        
    except HTTPBadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error in advanced department search: {str(e)}")
        raise HTTPInternalServerError(f"Failed to search departments: {str(e)}")


@router.post(
    "/bulk",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create departments",
    description="Create multiple departments in a single request."
)
async def bulk_create_departments(
    bulk_data: DepartmentBulkCreate,
    db: Session = Depends(get_database_session)
) -> dict:
    """Bulk create departments."""
    try:
        created_departments = []
        errors = []
        
        for i, dept_data in enumerate(bulk_data.departments):
            try:
                # Check if department name already exists
                existing_department = db.query(Department).filter(
                    Department.name == dept_data.name
                ).first()
                if existing_department:
                    errors.append({
                        "index": i,
                        "name": dept_data.name,
                        "error": f"Department name already exists: {dept_data.name}"
                    })
                    continue
                
                # Create department
                db_department = Department(**dept_data.dict())
                db.add(db_department)
                db.flush()  # Get ID without committing
                
                created_departments.append({
                    "index": i,
                    "id": str(db_department.id),
                    "name": db_department.name
                })
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "name": dept_data.name,
                    "error": str(e)
                })
        
        # Commit all successful creations
        if created_departments:
            db.commit()
        
        logger.info(f"Bulk created {len(created_departments)} departments with {len(errors)} errors")
        
        return {
            "success_count": len(created_departments),
            "error_count": len(errors),
            "created_departments": created_departments,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk create departments: {str(e)}")
        db.rollback()
        raise HTTPInternalServerError(f"Failed to bulk create departments: {str(e)}")


# Health check for departments endpoint
@router.get(
    "/health",
    response_model=dict,
    summary="Departments endpoint health check",
    description="Check the health of the departments endpoint."
)
async def departments_health_check(
    db: Session = Depends(get_database_session)
) -> dict:
    """Health check for departments endpoint."""
    try:
        # Test database query
        count = db.query(Department).count()
        
        return {
            "status": "healthy",
            "total_departments": count,
            "timestamp": func.now()
        }
        
    except Exception as e:
        logger.error(f"Departments health check failed: {str(e)}")
        raise HTTPInternalServerError(f"Departments endpoint unhealthy: {str(e)}")