"""
Database seeder scripts for the people management system.

This module provides functions to populate the database with sample data
for development and testing purposes.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from .models import Person, Department, Position, Employment
from .db import get_db_session


logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeder class for managing sample data creation."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the seeder.
        
        Args:
            session: Database session (optional, will create if not provided)
        """
        self.session = session
        self._own_session = session is None
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.session:
            return self.session
        return get_db_session()
    
    def seed_departments(self) -> List[Department]:
        """
        Create sample departments.
        
        Returns:
            List of created department objects
        """
        departments_data = [
            {
                "name": "Engineering",
                "description": "Software development and technical operations team responsible for building and maintaining our products."
            },
            {
                "name": "Human Resources",
                "description": "People operations, recruitment, employee relations, and organizational development."
            },
            {
                "name": "Marketing",
                "description": "Brand management, digital marketing, content creation, and customer acquisition strategies."
            },
            {
                "name": "Sales",
                "description": "Revenue generation, client relationships, business development, and market expansion."
            },
            {
                "name": "Finance",
                "description": "Financial planning, accounting, budgeting, and business analytics."
            },
            {
                "name": "Operations",
                "description": "Business operations, process optimization, vendor management, and facilities."
            },
            {
                "name": "Customer Success",
                "description": "Client support, customer onboarding, account management, and retention strategies."
            }
        ]
        
        departments = []
        
        with self._get_session() as session:
            for dept_data in departments_data:
                # Check if department already exists
                existing = session.query(Department).filter_by(name=dept_data["name"]).first()
                if not existing:
                    department = Department(**dept_data)
                    session.add(department)
                    departments.append(department)
                    logger.info(f"Created department: {dept_data['name']}")
                else:
                    departments.append(existing)
                    logger.info(f"Department already exists: {dept_data['name']}")
            
            session.commit()
        
        return departments
    
    def seed_positions(self, departments: List[Department]) -> List[Position]:
        """
        Create sample positions for departments.
        
        Args:
            departments: List of departments to create positions for
            
        Returns:
            List of created position objects
        """
        # Map department names to position data
        positions_by_department = {
            "Engineering": [
                {"title": "Software Engineer", "description": "Develop and maintain software applications using modern technologies."},
                {"title": "Senior Software Engineer", "description": "Lead technical initiatives and mentor junior developers."},
                {"title": "Staff Software Engineer", "description": "Drive architectural decisions and cross-team technical initiatives."},
                {"title": "Engineering Manager", "description": "Manage engineering teams and coordinate technical projects."},
                {"title": "DevOps Engineer", "description": "Manage infrastructure, CI/CD pipelines, and deployment automation."},
                {"title": "QA Engineer", "description": "Ensure software quality through testing and automation."},
                {"title": "Data Engineer", "description": "Build and maintain data pipelines and analytics infrastructure."},
            ],
            "Human Resources": [
                {"title": "HR Generalist", "description": "Handle general HR functions including recruitment and employee relations."},
                {"title": "HR Manager", "description": "Lead HR initiatives and manage HR team operations."},
                {"title": "Recruiter", "description": "Source, screen, and hire talent across all departments."},
                {"title": "People Operations Specialist", "description": "Manage employee lifecycle and HR processes."},
            ],
            "Marketing": [
                {"title": "Marketing Manager", "description": "Develop and execute marketing strategies and campaigns."},
                {"title": "Content Marketing Specialist", "description": "Create engaging content for various marketing channels."},
                {"title": "Digital Marketing Specialist", "description": "Manage digital advertising and social media campaigns."},
                {"title": "Brand Manager", "description": "Maintain brand consistency and manage brand initiatives."},
                {"title": "Marketing Analyst", "description": "Analyze marketing performance and provide data-driven insights."},
            ],
            "Sales": [
                {"title": "Account Executive", "description": "Manage client relationships and drive revenue growth."},
                {"title": "Sales Development Representative", "description": "Generate and qualify leads for the sales team."},
                {"title": "Sales Manager", "description": "Lead sales team and develop sales strategies."},
                {"title": "Business Development Manager", "description": "Identify new business opportunities and partnerships."},
                {"title": "Sales Operations Specialist", "description": "Support sales processes and analyze sales performance."},
            ],
            "Finance": [
                {"title": "Financial Analyst", "description": "Perform financial analysis and support business decision-making."},
                {"title": "Accountant", "description": "Manage accounting operations and financial reporting."},
                {"title": "Finance Manager", "description": "Oversee financial operations and team management."},
                {"title": "Controller", "description": "Manage accounting operations and financial controls."},
            ],
            "Operations": [
                {"title": "Operations Manager", "description": "Oversee daily operations and process improvements."},
                {"title": "Business Analyst", "description": "Analyze business processes and recommend improvements."},
                {"title": "Project Manager", "description": "Plan, execute, and monitor business projects."},
                {"title": "Facilities Manager", "description": "Manage office facilities and vendor relationships."},
            ],
            "Customer Success": [
                {"title": "Customer Success Manager", "description": "Ensure customer satisfaction and retention."},
                {"title": "Customer Support Specialist", "description": "Provide technical support and resolve customer issues."},
                {"title": "Account Manager", "description": "Manage key customer accounts and relationships."},
                {"title": "Implementation Specialist", "description": "Guide new customers through product implementation."},
            ],
        }
        
        positions = []
        
        with self._get_session() as session:
            for department in departments:
                dept_positions = positions_by_department.get(department.name, [])
                
                for pos_data in dept_positions:
                    # Check if position already exists
                    existing = session.query(Position).filter_by(
                        title=pos_data["title"],
                        department_id=department.id
                    ).first()
                    
                    if not existing:
                        position = Position(
                            title=pos_data["title"],
                            description=pos_data["description"],
                            department_id=department.id
                        )
                        session.add(position)
                        positions.append(position)
                        logger.info(f"Created position: {pos_data['title']} in {department.name}")
                    else:
                        positions.append(existing)
                        logger.info(f"Position already exists: {pos_data['title']} in {department.name}")
            
            session.commit()
        
        return positions
    
    def seed_people(self) -> List[Person]:
        """
        Create sample people records.
        
        Returns:
            List of created person objects
        """
        people_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@company.com",
                "phone": "+1-555-0101",
                "date_of_birth": date(1985, 3, 15),
                "address": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102",
                "country": "United States"
            },
            {
                "first_name": "Emily",
                "last_name": "Johnson",
                "email": "emily.johnson@company.com",
                "phone": "+1-555-0102",
                "date_of_birth": date(1990, 7, 22),
                "address": "456 Oak Ave",
                "city": "Seattle",
                "state": "WA",
                "zip_code": "98101",
                "country": "United States"
            },
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "email": "michael.brown@company.com",
                "phone": "+1-555-0103",
                "date_of_birth": date(1988, 11, 8),
                "address": "789 Pine St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "country": "United States"
            },
            {
                "first_name": "Sarah",
                "last_name": "Davis",
                "email": "sarah.davis@company.com",
                "phone": "+1-555-0104",
                "date_of_birth": date(1992, 1, 30),
                "address": "321 Elm St",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80202",
                "country": "United States"
            },
            {
                "first_name": "David",
                "last_name": "Wilson",
                "email": "david.wilson@company.com",
                "phone": "+1-555-0105",
                "date_of_birth": date(1987, 9, 12),
                "address": "654 Maple Ave",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "country": "United States"
            },
            {
                "first_name": "Lisa",
                "last_name": "Anderson",
                "email": "lisa.anderson@company.com",
                "phone": "+1-555-0106",
                "date_of_birth": date(1991, 4, 18),
                "address": "987 Cedar St",
                "city": "Portland",
                "state": "OR",
                "zip_code": "97201",
                "country": "United States"
            },
            {
                "first_name": "Robert",
                "last_name": "Taylor",
                "email": "robert.taylor@company.com",
                "phone": "+1-555-0107",
                "date_of_birth": date(1983, 12, 5),
                "address": "147 Birch Ln",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60601",
                "country": "United States"
            },
            {
                "first_name": "Jennifer",
                "last_name": "Martinez",
                "email": "jennifer.martinez@company.com",
                "phone": "+1-555-0108",
                "date_of_birth": date(1989, 6, 25),
                "address": "258 Spruce St",
                "city": "Miami",
                "state": "FL",
                "zip_code": "33101",
                "country": "United States"
            },
            {
                "first_name": "Chris",
                "last_name": "Lee",
                "email": "chris.lee@company.com",
                "phone": "+1-555-0109",
                "date_of_birth": date(1986, 10, 14),
                "address": "369 Willow Dr",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90210",
                "country": "United States"
            },
            {
                "first_name": "Amanda",
                "last_name": "White",
                "email": "amanda.white@company.com",
                "phone": "+1-555-0110",
                "date_of_birth": date(1993, 2, 28),
                "address": "741 Aspen Way",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "United States"
            }
        ]
        
        people = []
        
        with self._get_session() as session:
            for person_data in people_data:
                # Check if person already exists
                existing = session.query(Person).filter_by(email=person_data["email"]).first()
                if not existing:
                    person = Person(**person_data)
                    session.add(person)
                    people.append(person)
                    logger.info(f"Created person: {person_data['first_name']} {person_data['last_name']}")
                else:
                    people.append(existing)
                    logger.info(f"Person already exists: {person_data['email']}")
            
            session.commit()
        
        return people
    
    def seed_employments(self, people: List[Person], positions: List[Position]) -> List[Employment]:
        """
        Create sample employment records.
        
        Args:
            people: List of people to create employments for
            positions: List of positions to assign people to
            
        Returns:
            List of created employment objects
        """
        if not people or not positions:
            logger.warning("Cannot create employments: missing people or positions")
            return []
        
        # Define salary ranges by position level
        salary_ranges = {
            "Software Engineer": (70000, 90000),
            "Senior Software Engineer": (100000, 130000),
            "Staff Software Engineer": (140000, 170000),
            "Engineering Manager": (150000, 180000),
            "DevOps Engineer": (80000, 110000),
            "QA Engineer": (65000, 85000),
            "Data Engineer": (85000, 115000),
            "HR Generalist": (55000, 70000),
            "HR Manager": (80000, 100000),
            "Recruiter": (60000, 80000),
            "People Operations Specialist": (50000, 65000),
            "Marketing Manager": (75000, 95000),
            "Content Marketing Specialist": (50000, 70000),
            "Digital Marketing Specialist": (55000, 75000),
            "Brand Manager": (70000, 90000),
            "Marketing Analyst": (60000, 80000),
            "Account Executive": (60000, 80000),
            "Sales Development Representative": (45000, 60000),
            "Sales Manager": (90000, 120000),
            "Business Development Manager": (80000, 110000),
            "Sales Operations Specialist": (55000, 75000),
            "Financial Analyst": (60000, 80000),
            "Accountant": (50000, 65000),
            "Finance Manager": (85000, 110000),
            "Controller": (100000, 130000),
            "Operations Manager": (75000, 95000),
            "Business Analyst": (65000, 85000),
            "Project Manager": (70000, 90000),
            "Facilities Manager": (55000, 75000),
            "Customer Success Manager": (70000, 90000),
            "Customer Support Specialist": (40000, 55000),
            "Account Manager": (65000, 85000),
            "Implementation Specialist": (60000, 80000),
        }
        
        employments = []
        
        with self._get_session() as session:
            # Create employment records for the first 10 people (assuming we have enough positions)
            import random
            available_positions = positions.copy()
            random.shuffle(available_positions)
            
            for i, person in enumerate(people[:min(len(people), len(positions))]):
                if i < len(available_positions):
                    position = available_positions[i]
                    
                    # Calculate salary
                    salary_range = salary_ranges.get(position.title, (50000, 70000))
                    salary = Decimal(random.randint(salary_range[0], salary_range[1]))
                    
                    # Calculate start date (between 6 months ago and 3 years ago)
                    days_ago = random.randint(180, 1095)
                    start_date = date.today() - timedelta(days=days_ago)
                    
                    # 90% chance of being active, 10% chance of being terminated
                    is_active = random.random() > 0.1
                    end_date = None
                    
                    if not is_active:
                        # End date between start date and today
                        end_days = random.randint(30, days_ago - 30)
                        end_date = start_date + timedelta(days=end_days)
                    
                    # Check if employment already exists
                    existing = session.query(Employment).filter_by(
                        person_id=person.id,
                        position_id=position.id
                    ).first()
                    
                    if not existing:
                        employment = Employment(
                            person_id=person.id,
                            position_id=position.id,
                            start_date=start_date,
                            end_date=end_date,
                            is_active=is_active,
                            salary=salary
                        )
                        session.add(employment)
                        employments.append(employment)
                        
                        status = "Active" if is_active else "Terminated"
                        logger.info(f"Created employment: {person.full_name} as {position.title} ({status})")
                    else:
                        employments.append(existing)
                        logger.info(f"Employment already exists: {person.full_name} as {position.title}")
            
            session.commit()
        
        return employments
    
    def seed_all(self) -> dict:
        """
        Seed all sample data.
        
        Returns:
            Dictionary with counts of created records
        """
        logger.info("Starting database seeding...")
        
        # Seed departments first
        departments = self.seed_departments()
        
        # Seed positions (depends on departments)
        positions = self.seed_positions(departments)
        
        # Seed people
        people = self.seed_people()
        
        # Seed employments (depends on people and positions)
        employments = self.seed_employments(people, positions)
        
        results = {
            "departments": len(departments),
            "positions": len(positions),
            "people": len(people),
            "employments": len(employments)
        }
        
        logger.info(f"Database seeding completed: {results}")
        return results


def seed_database(session: Optional[Session] = None) -> dict:
    """
    Convenience function to seed the database with sample data.
    
    Args:
        session: Database session (optional)
        
    Returns:
        Dictionary with counts of created records
    """
    seeder = DatabaseSeeder(session)
    return seeder.seed_all()


def clear_all_data(session: Optional[Session] = None) -> None:
    """
    Clear all data from the database.
    
    WARNING: This will delete all data in the database!
    
    Args:
        session: Database session (optional)
    """
    logger.warning("Clearing all database data...")
    
    with get_db_session() if session is None else session as db_session:
        # Delete in reverse dependency order
        db_session.query(Employment).delete()
        db_session.query(Position).delete()
        db_session.query(Department).delete()
        db_session.query(Person).delete()
        
        if session is None:
            db_session.commit()
    
    logger.warning("All database data cleared!")


def reset_and_seed_database(session: Optional[Session] = None) -> dict:
    """
    Clear all data and reseed the database.
    
    Args:
        session: Database session (optional)
        
    Returns:
        Dictionary with counts of created records
    """
    clear_all_data(session)
    return seed_database(session)


if __name__ == "__main__":
    """Run seeding when script is executed directly."""
    import sys
    import os
    
    # Add the project root to Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    
    from server.database.db import initialize_database
    
    # Initialize database
    initialize_database()
    
    # Seed with sample data
    results = seed_database()
    print(f"Database seeded successfully: {results}")