"""
API routes for System Statistics.

This module provides comprehensive statistics and analytics endpoints
for the people management system, including summaries, reports, and metrics.
"""

import logging
from typing import Dict, Any, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_, extract

from ...database.models import Person, Department, Position, Employment
from ...database.db import get_db
from ..dependencies import get_database_session, get_date_range_params, DateRangeParams
from ..schemas.common import StatisticsResponse, HealthCheckResponse
from ...core.exceptions import HTTPInternalServerError
from ...core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "/overview",
    response_model=StatisticsResponse,
    summary="Get system overview statistics",
    description="Get comprehensive overview statistics for the entire system."
)
async def get_system_statistics(
    db: Session = Depends(get_database_session)
) -> StatisticsResponse:
    """Get comprehensive system statistics."""
    try:
        # Basic counts
        total_people = db.query(Person).count()
        total_departments = db.query(Department).count()
        total_positions = db.query(Position).count()
        
        # Active employees count
        active_employees = db.query(Employment).filter(Employment.is_active == True).count()
        
        # Average salary calculation
        avg_salary_result = (
            db.query(func.avg(Employment.salary))
            .filter(and_(Employment.is_active == True, Employment.salary.isnot(None)))
            .scalar()
        )
        average_salary = float(avg_salary_result) if avg_salary_result else None
        
        # Employment statistics
        employment_stats = await _get_employment_statistics(db)
        
        return StatisticsResponse(
            total_people=total_people,
            active_employees=active_employees,
            total_departments=total_departments,
            total_positions=total_positions,
            average_salary=average_salary,
            employment_statistics=employment_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get system statistics: {str(e)}")


@router.get(
    "/departments",
    response_model=Dict[str, Any],
    summary="Get department statistics",
    description="Get detailed statistics for all departments."
)
async def get_department_statistics(
    include_empty: bool = Query(False, description="Include departments with no employees"),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get statistics for all departments."""
    try:
        # Base query for department statistics
        query = (
            db.query(
                Department.id,
                Department.name,
                func.count(Position.id).label('position_count'),
                func.count(case([(Employment.is_active == True, Employment.id)])).label('active_employees'),
                func.count(Employment.id).label('total_employees'),
                func.avg(case([(Employment.is_active == True, Employment.salary)])).label('avg_salary'),
                func.min(case([(Employment.is_active == True, Employment.salary)])).label('min_salary'),
                func.max(case([(Employment.is_active == True, Employment.salary)])).label('max_salary')
            )
            .outerjoin(Position, Department.id == Position.department_id)
            .outerjoin(Employment, Position.id == Employment.position_id)
            .group_by(Department.id, Department.name)
        )
        
        if not include_empty:
            query = query.having(func.count(case([(Employment.is_active == True, Employment.id)])) > 0)
        
        results = query.all()
        
        department_stats = []
        total_active_employees = 0
        total_salaries = []
        
        for result in results:
            active_count = result.active_employees or 0
            total_active_employees += active_count
            
            dept_stat = {
                "id": str(result.id),
                "name": result.name,
                "position_count": result.position_count or 0,
                "active_employees": active_count,
                "total_employees": result.total_employees or 0,
                "average_salary": float(result.avg_salary) if result.avg_salary else None,
                "salary_range": {
                    "min": float(result.min_salary) if result.min_salary else None,
                    "max": float(result.max_salary) if result.max_salary else None
                } if result.min_salary and result.max_salary else None
            }
            
            if result.avg_salary:
                total_salaries.append(float(result.avg_salary))
            
            department_stats.append(dept_stat)
        
        # Overall statistics
        overall_avg_salary = sum(total_salaries) / len(total_salaries) if total_salaries else None
        
        return {
            "summary": {
                "total_departments": len(department_stats),
                "total_active_employees": total_active_employees,
                "overall_average_salary": overall_avg_salary
            },
            "departments": department_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting department statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get department statistics: {str(e)}")


@router.get(
    "/positions",
    response_model=Dict[str, Any],
    summary="Get position statistics",
    description="Get detailed statistics for all positions."
)
async def get_position_statistics(
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    include_empty: bool = Query(False, description="Include positions with no employees"),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get statistics for all positions."""
    try:
        # Base query for position statistics
        query = (
            db.query(
                Position.id,
                Position.title,
                Department.name.label('department_name'),
                func.count(case([(Employment.is_active == True, Employment.id)])).label('active_employees'),
                func.count(Employment.id).label('total_employees'),
                func.avg(case([(Employment.is_active == True, Employment.salary)])).label('avg_salary'),
                func.min(case([(Employment.is_active == True, Employment.salary)])).label('min_salary'),
                func.max(case([(Employment.is_active == True, Employment.salary)])).label('max_salary')
            )
            .join(Department)
            .outerjoin(Employment, Position.id == Employment.position_id)
            .group_by(Position.id, Position.title, Department.name)
        )
        
        if department_id:
            query = query.filter(Position.department_id == department_id)
        
        if not include_empty:
            query = query.having(func.count(case([(Employment.is_active == True, Employment.id)])) > 0)
        
        results = query.all()
        
        position_stats = []
        total_active_employees = 0
        total_salaries = []
        
        for result in results:
            active_count = result.active_employees or 0
            total_active_employees += active_count
            
            pos_stat = {
                "id": str(result.id),
                "title": result.title,
                "department_name": result.department_name,
                "active_employees": active_count,
                "total_employees": result.total_employees or 0,
                "average_salary": float(result.avg_salary) if result.avg_salary else None,
                "salary_range": {
                    "min": float(result.min_salary) if result.min_salary else None,
                    "max": float(result.max_salary) if result.max_salary else None
                } if result.min_salary and result.max_salary else None
            }
            
            if result.avg_salary:
                total_salaries.append(float(result.avg_salary))
            
            position_stats.append(pos_stat)
        
        # Overall statistics
        overall_avg_salary = sum(total_salaries) / len(total_salaries) if total_salaries else None
        
        return {
            "summary": {
                "total_positions": len(position_stats),
                "total_active_employees": total_active_employees,  
                "overall_average_salary": overall_avg_salary
            },
            "positions": position_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting position statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get position statistics: {str(e)}")


@router.get(
    "/salary",
    response_model=Dict[str, Any],
    summary="Get salary statistics",
    description="Get comprehensive salary analysis and statistics."
)
async def get_salary_statistics(
    date_range: DateRangeParams = Depends(get_date_range_params),
    by_department: bool = Query(True, description="Include breakdown by department"),
    by_position: bool = Query(True, description="Include breakdown by position"),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get comprehensive salary statistics."""
    try:
        # Base query for active employments with salaries
        base_query = (
            db.query(Employment)
            .filter(and_(Employment.is_active == True, Employment.salary.isnot(None)))
        )
        
        # Apply date range filters
        if date_range.start_date:
            base_query = base_query.filter(Employment.start_date >= date_range.start_date)
        
        if date_range.end_date:
            base_query = base_query.filter(Employment.start_date <= date_range.end_date)
        
        # Get all salaries for overall statistics
        salaries = [float(emp.salary) for emp in base_query.all()]
        
        overall_stats = {}
        if salaries:
            import statistics
            overall_stats = {
                "count": len(salaries),
                "total": sum(salaries),
                "average": sum(salaries) / len(salaries),
                "median": statistics.median(salaries),
                "min": min(salaries),
                "max": max(salaries),
                "std_dev": statistics.stdev(salaries) if len(salaries) > 1 else 0
            }
            
            # Percentiles
            sorted_salaries = sorted(salaries)
            overall_stats["percentiles"] = {
                "25th": sorted_salaries[int(len(sorted_salaries) * 0.25)],
                "75th": sorted_salaries[int(len(sorted_salaries) * 0.75)],
                "90th": sorted_salaries[int(len(sorted_salaries) * 0.90)]
            }
        
        result = {"overall": overall_stats}
        
        # Department breakdown
        if by_department:
            dept_query = (
                db.query(
                    Department.name,
                    func.count(Employment.salary).label('count'),
                    func.sum(Employment.salary).label('total'),
                    func.avg(Employment.salary).label('average'),
                    func.min(Employment.salary).label('min_salary'),
                    func.max(Employment.salary).label('max_salary')
                )
                .join(Position)
                .join(Employment)
                .filter(and_(Employment.is_active == True, Employment.salary.isnot(None)))
            )
            
            if date_range.start_date:
                dept_query = dept_query.filter(Employment.start_date >= date_range.start_date)
            if date_range.end_date:
                dept_query = dept_query.filter(Employment.start_date <= date_range.end_date)
            
            dept_results = dept_query.group_by(Department.name).all()
            
            result["by_department"] = [
                {
                    "department": dept.name,
                    "count": dept.count,
                    "total": float(dept.total),
                    "average": float(dept.average),
                    "min": float(dept.min_salary),
                    "max": float(dept.max_salary)
                }
                for dept in dept_results
            ]
        
        # Position breakdown
        if by_position:
            pos_query = (
                db.query(
                    Position.title,
                    Department.name.label('department'),
                    func.count(Employment.salary).label('count'),
                    func.sum(Employment.salary).label('total'),
                    func.avg(Employment.salary).label('average'),
                    func.min(Employment.salary).label('min_salary'),
                    func.max(Employment.salary).label('max_salary')
                )
                .join(Department)
                .join(Employment)
                .filter(and_(Employment.is_active == True, Employment.salary.isnot(None)))
            )
            
            if date_range.start_date:
                pos_query = pos_query.filter(Employment.start_date >= date_range.start_date)
            if date_range.end_date:
                pos_query = pos_query.filter(Employment.start_date <= date_range.end_date)
            
            pos_results = pos_query.group_by(Position.title, Department.name).all()
            
            result["by_position"] = [
                {
                    "position": pos.title,
                    "department": pos.department,
                    "count": pos.count,
                    "total": float(pos.total),
                    "average": float(pos.average),
                    "min": float(pos.min_salary),
                    "max": float(pos.max_salary)
                }
                for pos in pos_results
            ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting salary statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get salary statistics: {str(e)}")


@router.get(
    "/tenure",
    response_model=Dict[str, Any],
    summary="Get tenure statistics",
    description="Get employee tenure analysis and statistics."
)
async def get_tenure_statistics(
    active_only: bool = Query(True, description="Include only active employees"),
    by_department: bool = Query(True, description="Include breakdown by department"),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get employee tenure statistics."""
    try:
        # Base query
        query = db.query(Employment).join(Position).join(Department)
        
        if active_only:
            query = query.filter(Employment.is_active == True)
        
        employments = query.all()
        
        # Calculate tenure for each employment
        tenures_days = []
        tenures_months = []
        tenures_years = []
        
        for emp in employments:
            if emp.duration_days is not None:
                tenures_days.append(emp.duration_days)
                tenures_months.append(emp.duration_days / 30.44)  # Average days per month
                tenures_years.append(emp.duration_days / 365.25)  # Average days per year
        
        overall_stats = {}
        if tenures_days:
            import statistics
            overall_stats = {
                "count": len(tenures_days),
                "average_days": sum(tenures_days) / len(tenures_days),
                "average_months": sum(tenures_months) / len(tenures_months),
                "average_years": sum(tenures_years) / len(tenures_years),
                "median_days": statistics.median(tenures_days),
                "median_months": statistics.median(tenures_months),
                "median_years": statistics.median(tenures_years),
                "min_days": min(tenures_days),
                "max_days": max(tenures_days),
                "std_dev_days": statistics.stdev(tenures_days) if len(tenures_days) > 1 else 0
            }
        
        result = {"overall": overall_stats}
        
        # Department breakdown
        if by_department:
            dept_tenures = {}
            for emp in employments:
                dept_name = emp.position.department.name
                if dept_name not in dept_tenures:
                    dept_tenures[dept_name] = []
                
                if emp.duration_days is not None:
                    dept_tenures[dept_name].append({
                        "days": emp.duration_days,
                        "months": emp.duration_days / 30.44,
                        "years": emp.duration_days / 365.25
                    })
            
            dept_stats = []
            for dept_name, tenures in dept_tenures.items():
                if tenures:
                    days = [t["days"] for t in tenures]
                    months = [t["months"] for t in tenures]
                    years = [t["years"] for t in tenures]
                    
                    dept_stat = {
                        "department": dept_name,
                        "count": len(tenures),
                        "average_days": sum(days) / len(days),
                        "average_months": sum(months) / len(months),
                        "average_years": sum(years) / len(years),
                        "min_days": min(days),
                        "max_days": max(days)
                    }
                    dept_stats.append(dept_stat)
            
            result["by_department"] = dept_stats
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting tenure statistics: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get tenure statistics: {str(e)}")


@router.get(
    "/hiring-trends",
    response_model=Dict[str, Any],
    summary="Get hiring trends",
    description="Get hiring trends and patterns over time."
)
async def get_hiring_trends(
    date_range: DateRangeParams = Depends(get_date_range_params),
    group_by: str = Query("month", regex="^(month|quarter|year)$", description="Group results by time period"),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get hiring trends over time."""
    try:
        # Base query
        query = db.query(Employment)
        
        # Apply date range
        if date_range.start_date:
            query = query.filter(Employment.start_date >= date_range.start_date)
        else:
            # Default to last 2 years
            query = query.filter(Employment.start_date >= date.today() - timedelta(days=730))
        
        if date_range.end_date:
            query = query.filter(Employment.start_date <= date_range.end_date)
        
        # Group by time period
        if group_by == "month":
            time_group = func.date_trunc('month', Employment.start_date)
            format_str = '%Y-%m'
        elif group_by == "quarter":
            time_group = func.date_trunc('quarter', Employment.start_date)
            format_str = '%Y-Q%q'
        else:  # year
            time_group = func.date_trunc('year', Employment.start_date)
            format_str = '%Y'
        
        # Get hiring counts by time period
        hiring_query = (
            db.query(
                time_group.label('period'),
                func.count(Employment.id).label('hires')
            )
            .group_by(time_group)
            .order_by(time_group)
        )
        
        hiring_results = hiring_query.all()
        
        # Get termination counts by time period (based on end_date)
        termination_query = (
            db.query(
                time_group.label('period'),
                func.count(Employment.id).label('terminations')
            )
            .filter(Employment.end_date.isnot(None))
            .group_by(time_group)
            .order_by(time_group)
        )
        
        if group_by == "month":
            termination_time_group = func.date_trunc('month', Employment.end_date)
        elif group_by == "quarter":
            termination_time_group = func.date_trunc('quarter', Employment.end_date)
        else:  # year
            termination_time_group = func.date_trunc('year', Employment.end_date)
        
        termination_query = (
            db.query(
                termination_time_group.label('period'),
                func.count(Employment.id).label('terminations')
            )
            .filter(Employment.end_date.isnot(None))
            .group_by(termination_time_group)
            .order_by(termination_time_group)
        )
        
        if date_range.start_date:
            termination_query = termination_query.filter(Employment.end_date >= date_range.start_date)
        if date_range.end_date:
            termination_query = termination_query.filter(Employment.end_date <= date_range.end_date)
        
        termination_results = termination_query.all()
        
        # Combine results
        trends = {}
        
        # Add hiring data
        for result in hiring_results:
            period_str = result.period.strftime(format_str) if hasattr(result.period, 'strftime') else str(result.period)
            trends[period_str] = {
                "period": period_str,
                "hires": result.hires,
                "terminations": 0,
                "net_change": result.hires
            }
        
        # Add termination data
        for result in termination_results:
            period_str = result.period.strftime(format_str) if hasattr(result.period, 'strftime') else str(result.period)
            if period_str in trends:
                trends[period_str]["terminations"] = result.terminations
                trends[period_str]["net_change"] = trends[period_str]["hires"] - result.terminations
            else:
                trends[period_str] = {
                    "period": period_str,
                    "hires": 0,
                    "terminations": result.terminations,
                    "net_change": -result.terminations
                }
        
        # Sort by period
        sorted_trends = sorted(trends.values(), key=lambda x: x["period"])
        
        # Calculate summary statistics
        total_hires = sum(t["hires"] for t in sorted_trends)
        total_terminations = sum(t["terminations"] for t in sorted_trends)
        net_change = total_hires - total_terminations
        
        return {
            "summary": {
                "total_hires": total_hires,
                "total_terminations": total_terminations,
                "net_change": net_change,
                "group_by": group_by
            },
            "trends": sorted_trends
        }
        
    except Exception as e:
        logger.error(f"Error getting hiring trends: {str(e)}")
        raise HTTPInternalServerError(f"Failed to get hiring trends: {str(e)}")


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Statistics endpoint health check",
    description="Check the health of the statistics endpoint and overall system health."
)
async def statistics_health_check(
    db: Session = Depends(get_database_session)
) -> HealthCheckResponse:
    """Health check for statistics endpoint."""
    try:
        settings = get_settings()
        
        # Test database connectivity with basic queries
        total_people = db.query(Person).count()
        active_employees = db.query(Employment).filter(Employment.is_active == True).count()
        
        # Calculate uptime (this is a simplified version)
        import time
        uptime_seconds = time.time() - 1704067200  # Arbitrary start time
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            version=settings.app_version,
            database_connected=True,
            uptime_seconds=uptime_seconds
        )
        
    except Exception as e:
        logger.error(f"Statistics health check failed: {str(e)}")
        raise HTTPInternalServerError(f"Statistics endpoint unhealthy: {str(e)}")


async def _get_employment_statistics(db: Session) -> Dict[str, Any]:
    """Helper function to get employment statistics."""
    try:
        total_employments = db.query(Employment).count()
        active_employments = db.query(Employment).filter(Employment.is_active == True).count()
        terminated_employments = total_employments - active_employments
        
        # Turnover rate
        turnover_rate = (terminated_employments / total_employments * 100) if total_employments > 0 else 0
        
        # Recent hires (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_hires = db.query(Employment).filter(Employment.start_date >= thirty_days_ago).count()
        
        # Recent terminations (last 30 days)
        recent_terminations = db.query(Employment).filter(
            and_(
                Employment.end_date.isnot(None),
                Employment.end_date >= thirty_days_ago
            )
        ).count()
        
        return {
            "total_employments": total_employments,
            "active_employments": active_employments,
            "terminated_employments": terminated_employments,
            "turnover_rate": round(turnover_rate, 2),
            "recent_hires_30_days": recent_hires,
            "recent_terminations_30_days": recent_terminations
        }
        
    except Exception as e:
        logger.error(f"Error getting employment statistics: {str(e)}")
        return {}