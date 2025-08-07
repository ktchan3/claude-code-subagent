"""
Person service layer for business logic.

This module contains all business logic related to person operations,
including CRUD operations, validation, search, and data processing.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import or_, and_, func

from ...database.models import Person, Employment, Position, Department
from ...core.exceptions import (
    PersonNotFoundError, EmailAlreadyExistsError, HTTPBadRequestError
)
from ..utils.formatters import (
    format_person_response, format_person_summary, format_person_with_employment
)
from ..utils.security import (
    InputSanitizer, SecurityError, sanitize_person_data, log_security_event, sanitize_search_term
)
from ..utils.cache import (
    cache_result, cache_person_search, CacheInvalidator, get_cache, SHORT_CACHE_TTL
)
from ..utils.cache_invalidation import get_smart_invalidator, get_cache_strategies
from ..schemas.person import PersonCreate, PersonUpdate, PersonContactUpdate, PersonAddressUpdate

logger = logging.getLogger(__name__)


class PersonService:
    """
    Service class for person-related business logic.
    
    This service handles all person operations including validation,
    data processing, and database interactions.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the person service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_person(self, person_data: PersonCreate) -> Dict[str, Any]:
        """
        Create a new person with validation and business logic.
        
        Args:
            person_data: Person creation data
            
        Returns:
            Dictionary with formatted person data
            
        Raises:
            EmailAlreadyExistsError: If email already exists
            ValueError: If validation fails
        """
        logger.debug("Creating new person")
        
        # Check if email already exists
        if self.get_person_by_email(person_data.email, raise_if_not_found=False):
            raise EmailAlreadyExistsError(person_data.email)
        
        # Prepare data for database insertion
        person_dict = person_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Sanitize data for security
        from ..utils.security import sanitize_person_data
        person_dict = sanitize_person_data(person_dict)
        
        # Handle tags field conversion (List[str] -> JSON string)
        if 'tags' in person_dict and person_dict['tags'] is not None:
            person_dict['tags'] = json.dumps(person_dict['tags'])
        
        # Create and save person
        db_person = Person(**person_dict)
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        
        logger.info(f"Created person: {db_person.full_name} ({db_person.id})")
        
        # Invalidate relevant caches
        CacheInvalidator.invalidate_person_caches()
        
        return format_person_response(db_person)
    
    def get_person_by_id(self, person_id: UUID) -> Dict[str, Any]:
        """
        Get a person by ID.
        
        Args:
            person_id: Person UUID
            
        Returns:
            Dictionary with formatted person data
            
        Raises:
            PersonNotFoundError: If person not found
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        return format_person_response(person)
    
    def get_person_by_email(self, email: str, raise_if_not_found: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a person by email address.
        
        Args:
            email: Email address
            raise_if_not_found: Whether to raise exception if not found
            
        Returns:
            Dictionary with formatted person data or None
            
        Raises:
            HTTPBadRequestError: If person not found and raise_if_not_found is True
        """
        sanitized_email = sanitize_search_term(email.lower())
        person = self.db.query(Person).filter(Person.email == sanitized_email).first()
        
        if not person:
            if raise_if_not_found:
                raise HTTPBadRequestError(f"No person found with email: {email}")
            return None
        
        return format_person_response(person)
    
    def get_person_with_employment(self, person_id: UUID) -> Dict[str, Any]:
        """
        Get a person with employment details using eager loading.
        
        Args:
            person_id: Person UUID
            
        Returns:
            Dictionary with person and employment data
            
        Raises:
            PersonNotFoundError: If person not found
        """
        person = self.db.query(Person).options(
            selectinload(Person.employments).joinedload(Employment.position).joinedload(Position.department)
        ).filter(Person.id == person_id).first()
        
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        return format_person_with_employment(person)
    
    def update_person(self, person_id: UUID, person_data: PersonUpdate) -> Dict[str, Any]:
        """
        Update a person with validation.
        
        Args:
            person_id: Person UUID
            person_data: Person update data
            
        Returns:
            Dictionary with formatted person data
            
        Raises:
            PersonNotFoundError: If person not found
            EmailAlreadyExistsError: If email already exists for another person
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Check if email is being updated and if it already exists
        if person_data.email and person_data.email != person.email:
            existing_person = self.db.query(Person).filter(
                and_(Person.email == person_data.email, Person.id != person_id)
            ).first()
            if existing_person:
                raise EmailAlreadyExistsError(person_data.email)
        
        # Update person fields
        update_data = person_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Sanitize data for security
        from ..utils.security import sanitize_person_data
        update_data = sanitize_person_data(update_data)
        
        # Handle tags field conversion (List[str] -> JSON string)
        if 'tags' in update_data and update_data['tags'] is not None:
            update_data['tags'] = json.dumps(update_data['tags'])
        
        for field, value in update_data.items():
            setattr(person, field, value)
        
        self.db.commit()
        self.db.refresh(person)
        
        logger.info(f"Updated person: {person.full_name} ({person.id})")
        
        # Invalidate relevant caches
        CacheInvalidator.invalidate_person_caches()
        
        return format_person_response(person)
    
    def update_person_contact(self, person_id: UUID, contact_data: PersonContactUpdate) -> Dict[str, Any]:
        """
        Update person contact information.
        
        Args:
            person_id: Person UUID
            contact_data: Contact update data
            
        Returns:
            Dictionary with formatted person data
            
        Raises:
            PersonNotFoundError: If person not found
            EmailAlreadyExistsError: If email already exists for another person
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Check if email is being updated and if it already exists
        if contact_data.email and contact_data.email != person.email:
            existing_person = self.db.query(Person).filter(
                and_(Person.email == contact_data.email, Person.id != person_id)
            ).first()
            if existing_person:
                raise EmailAlreadyExistsError(contact_data.email)
        
        # Update contact fields
        update_data = contact_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        self.db.commit()
        self.db.refresh(person)
        
        logger.info(f"Updated contact info for person: {person.full_name} ({person.id})")
        
        # Invalidate relevant caches
        CacheInvalidator.invalidate_person_caches()
        
        return format_person_response(person)
    
    def update_person_address(self, person_id: UUID, address_data: PersonAddressUpdate) -> Dict[str, Any]:
        """
        Update person address information.
        
        Args:
            person_id: Person UUID
            address_data: Address update data
            
        Returns:
            Dictionary with formatted person data
            
        Raises:
            PersonNotFoundError: If person not found
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        # Update address fields
        update_data = address_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(person, field, value)
        
        self.db.commit()
        self.db.refresh(person)
        
        logger.info(f"Updated address for person: {person.full_name} ({person.id})")
        
        # Invalidate relevant caches
        CacheInvalidator.invalidate_person_caches()
        
        return format_person_response(person)
    
    def delete_person(self, person_id: UUID) -> str:
        """
        Delete a person and associated records.
        
        Args:
            person_id: Person UUID
            
        Returns:
            Name of deleted person
            
        Raises:
            PersonNotFoundError: If person not found
        """
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise PersonNotFoundError(str(person_id))
        
        person_name = person.full_name
        
        # Delete person (cascade will handle employment records)
        self.db.delete(person)
        self.db.commit()
        
        logger.info(f"Deleted person: {person_name} ({person_id})")
        
        # Invalidate relevant caches
        CacheInvalidator.invalidate_person_caches()
        
        return person_name
    
    # @cache_person_search(ttl=60)  # Cache for 1 minute due to frequent updates - temporarily disabled for security fix
    def list_people(
        self, 
        search_query: Optional[str] = None,
        active_only: Optional[bool] = None,
        sort_by: Optional[str] = None,
        is_descending: bool = False,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List people with search, filtering, and pagination.
        
        Args:
            search_query: Search term for name and email
            active_only: Filter by employment status
            sort_by: Sort column
            is_descending: Sort direction
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (list of full person responses, total count)
        """
        # Build base query with efficient eager loading
        query = self.db.query(Person).options(
            selectinload(Person.employments).selectinload(Employment.position).selectinload(Position.department)
        )
        
        # Apply search filters
        if search_query:
            sanitized_query = sanitize_search_term(search_query)
            logger.warning(f"DEBUG: search_query='{search_query}', sanitized_query='{sanitized_query}'")
            if sanitized_query:  # Only proceed if sanitization didn't return empty string
                search_term = f"%{sanitized_query}%"
                query = query.filter(
                    or_(
                        Person.first_name.ilike(search_term),
                        Person.last_name.ilike(search_term),
                        Person.email.ilike(search_term),
                        func.concat(Person.first_name, ' ', Person.last_name).ilike(search_term)
                    )
                )
            else:
                # If sanitization returned empty, return no results to prevent security issues
                logger.warning("DEBUG: Applying security filter - no results")
                query = query.filter(Person.id == None)  # This will return no results
        
        # Apply active filter
        if active_only is not None and active_only:
            query = query.join(Employment).filter(Employment.is_active == True)
        
        # Apply sorting
        if sort_by:
            sort_column = getattr(Person, sort_by, None)
            if sort_column:
                if is_descending:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                logger.warning(f"Invalid sort column: {sort_by}")
        else:
            query = query.order_by(Person.last_name, Person.first_name)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        people = query.offset(offset).limit(size).all()
        
        # Format response with full person data
        people_responses = [
            format_person_response(person)
            for person in people
        ]
        
        return people_responses, total
    
    @cache_person_search(ttl=60)  # Cache for 1 minute
    def advanced_search(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        active_only: bool = True,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Advanced search for people with multiple filters.
        
        Args:
            name: Name search term
            email: Email search term
            department: Department filter
            position: Position filter
            active_only: Show only active employees
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (list of person summaries, total count)
        """
        # Build base query with efficient eager loading
        query = self.db.query(Person).options(
            selectinload(Person.employments).selectinload(Employment.position).selectinload(Position.department)
        )
        
        # Join with employment and position tables for filtering
        if department or position:
            query = query.join(Employment).join(Position).join(Department)
        elif active_only:
            # Only join if we need to filter by active employment
            query = query.join(Employment, isouter=False)
        
        # Apply filters with sanitized input
        if name:
            sanitized_name = sanitize_search_term(name)
            search_term = f"%{sanitized_name}%"
            query = query.filter(
                or_(
                    Person.first_name.ilike(search_term),
                    Person.last_name.ilike(search_term),
                    func.concat(Person.first_name, ' ', Person.last_name).ilike(search_term)
                )
            )
        
        if email:
            sanitized_email = sanitize_search_term(email)
            query = query.filter(Person.email.ilike(f"%{sanitized_email}%"))
        
        if department:
            sanitized_dept = sanitize_search_term(department)
            query = query.filter(Department.name.ilike(f"%{sanitized_dept}%"))
        
        if position:
            sanitized_pos = sanitize_search_term(position)
            query = query.filter(Position.title.ilike(f"%{sanitized_pos}%"))
        
        if active_only:
            query = query.filter(Employment.is_active == True)
        
        # Order by name
        query = query.order_by(Person.last_name, Person.first_name)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        people = query.offset(offset).limit(size).all()
        
        # Format response with full person data
        people_responses = [
            format_person_response(person)
            for person in people
        ]
        
        return people_responses, total
    
    def bulk_create_people(self, people_data: List[PersonCreate]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Create multiple people in bulk with error handling.
        
        Args:
            people_data: List of person creation data
            
        Returns:
            Tuple of (created people info, errors)
        """
        created_people = []
        errors = []
        
        for i, person_data in enumerate(people_data):
            try:
                # Check if email already exists
                existing_person = self.db.query(Person).filter(Person.email == person_data.email).first()
                if existing_person:
                    errors.append({
                        "index": i,
                        "email": person_data.email,
                        "error": f"Email already exists: {person_data.email}"
                    })
                    continue
                
                # Create person
                person_dict = person_data.model_dump(exclude_unset=True, exclude_none=True)
                
                # Handle tags field conversion
                if 'tags' in person_dict and person_dict['tags'] is not None:
                    person_dict['tags'] = json.dumps(person_dict['tags'])
                
                db_person = Person(**person_dict)
                self.db.add(db_person)
                self.db.flush()  # Get ID without committing
                
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
            self.db.commit()
        
        logger.info(f"Bulk created {len(created_people)} people with {len(errors)} errors")
        
        # Invalidate relevant caches if any people were created
        if created_people:
            CacheInvalidator.invalidate_person_caches()
        
        return created_people, errors
    
    @cache_result(ttl=300, key_prefix="person_count")  # Cache for 5 minutes
    def get_person_count(self) -> int:
        """
        Get total count of people in the database.
        
        Returns:
            Total person count
        """
        return self.db.query(Person).count()