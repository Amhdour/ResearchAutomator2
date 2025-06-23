"""
Database Models

SQLAlchemy models for storing research sessions, findings, citations, and user data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from datetime import datetime

Base = declarative_base()

class ResearchSession(Base):
    """Research session tracking"""
    __tablename__ = 'research_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False)
    research_goal = Column(Text, nullable=False)
    status = Column(String(50), default='active')  # active, completed, failed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # Configuration
    max_sources = Column(Integer, default=10)
    search_depth = Column(String(50), default='medium')
    citation_style = Column(String(20), default='APA')
    model_used = Column(String(100))
    
    # Results metadata
    total_sources = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    total_citations = Column(Integer, default=0)
    quality_score = Column(Float)
    execution_time = Column(Float)
    
    # Relationships
    findings = relationship("Finding", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="session", cascade="all, delete-orphan")
    phases = relationship("ResearchPhase", back_populates="session", cascade="all, delete-orphan")

class ResearchPhase(Base):
    """Individual research phases within a session"""
    __tablename__ = 'research_phases'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('research_sessions.session_id'))
    phase_id = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Execution details
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time = Column(Float)
    
    # Results
    documents_retrieved = Column(Integer, default=0)
    documents_stored = Column(Integer, default=0)
    relevance_score = Column(Float)
    
    # Configuration
    search_terms = Column(JSON)
    expected_sources = Column(JSON)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="phases")

class Finding(Base):
    """Research findings from sources"""
    __tablename__ = 'findings'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('research_sessions.session_id'))
    
    # Source information
    source_title = Column(String(500))
    source_url = Column(Text)
    source_type = Column(String(100))  # web, academic, report
    
    # Content
    key_findings = Column(JSON)  # List of key findings
    relevant_facts = Column(JSON)  # List of relevant facts
    statistics = Column(JSON)  # List of statistics
    conclusions = Column(JSON)  # List of conclusions
    
    # Metadata
    relevance_score = Column(Float)
    confidence_level = Column(String(50))
    extracted_at = Column(DateTime, default=func.now())
    content_hash = Column(String(255))  # For deduplication
    
    # Relationships
    session = relationship("ResearchSession", back_populates="findings")

class Citation(Base):
    """Citations extracted from sources"""
    __tablename__ = 'citations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('research_sessions.session_id'))
    
    # Citation details
    citation_type = Column(String(50))  # claim, statistic, insight, source
    title = Column(String(500))
    authors = Column(JSON)  # List of authors
    url = Column(Text)
    date = Column(String(100))
    source_type = Column(String(100))
    
    # Content
    content = Column(Text)
    context = Column(Text)
    quote = Column(Text)
    page_section = Column(String(255))
    
    # Formatted citations
    apa_format = Column(Text)
    mla_format = Column(Text)
    chicago_format = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    quality_score = Column(Float)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="citations")

class SourceQuality(Base):
    """Source quality assessment and caching"""
    __tablename__ = 'source_quality'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    domain = Column(String(255))
    
    # Quality metrics
    credibility_score = Column(Float)
    content_quality_score = Column(Float)
    accessibility_score = Column(Float)
    overall_score = Column(Float)
    
    # Assessment details
    has_author = Column(Boolean, default=False)
    has_date = Column(Boolean, default=False)
    content_length = Column(Integer)
    is_academic = Column(Boolean, default=False)
    
    # Tracking
    first_assessed = Column(DateTime, default=func.now())
    last_assessed = Column(DateTime, default=func.now())
    assessment_count = Column(Integer, default=1)

class UserPreferences(Base):
    """User preferences and settings"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)  # Could be session-based or user-based
    
    # Default research settings
    default_max_sources = Column(Integer, default=10)
    default_search_depth = Column(String(50), default='medium')
    default_citation_style = Column(String(20), default='APA')
    default_model = Column(String(100), default='llama3-70b-8192')
    
    # Performance preferences
    optimize_for_free_tier = Column(Boolean, default=True)
    enable_batch_processing = Column(Boolean, default=True)
    
    # Research history
    total_sessions = Column(Integer, default=0)
    successful_sessions = Column(Integer, default=0)
    total_research_time = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, default=func.now())

# Database connection and session management
class DatabaseManager:
    """Manage database connections and operations"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
        
    def close_session(self, session):
        """Close a database session"""
        session.close()