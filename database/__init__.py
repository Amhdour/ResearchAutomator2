"""
Database Package

PostgreSQL database integration for the autonomous research agent.
"""

from .models import (
    DatabaseManager, 
    ResearchSession, 
    ResearchPhase, 
    Finding, 
    Citation, 
    SourceQuality, 
    UserPreferences
)
from .operations import DatabaseOperations

__all__ = [
    'DatabaseManager',
    'DatabaseOperations', 
    'ResearchSession',
    'ResearchPhase',
    'Finding',
    'Citation',
    'SourceQuality',
    'UserPreferences'
]