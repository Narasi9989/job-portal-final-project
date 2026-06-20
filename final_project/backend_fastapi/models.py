"""
OracleDB Data Models (Documentation & Reference)
Note: Using raw OracleDB queries instead of SQLAlchemy ORM.
These models serve as reference for the table structure.
"""

from typing import Optional
from datetime import datetime


class Company:
    """Company model representing the companies table."""
    def __init__(self, id: int, name: str, description: Optional[str] = None, website: Optional[str] = None):
        self.id = id
        self.name = name
        self.description = description
        self.website = website


class Job:
    """Job model representing the jobs table."""
    def __init__(self, 
                 id: int,
                 title: str,
                 description: Optional[str] = None,
                 location: Optional[str] = None,
                 salary: Optional[str] = None,
                 company_id: Optional[int] = None,
                 posted_date: Optional[datetime] = None,
                 is_active: bool = True):
        self.id = id
        self.title = title
        self.description = description
        self.location = location
        self.salary = salary
        self.company_id = company_id
        self.posted_date = posted_date
        self.is_active = is_active


class Users:
    """User model representing the users table."""
    def __init__(self,
                 id: int,
                 username: str,
                 email: str,
                 hashed_password: str,
                 is_active: str = "Y"):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active
