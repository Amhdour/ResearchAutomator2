"""
Database Operations

High-level database operations for research sessions, findings, and analytics.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func
from .models import DatabaseManager, ResearchSession, ResearchPhase, Finding, Citation, SourceQuality, UserPreferences
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseOperations:
    """High-level database operations for research agent"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()  # Ensure tables exist
        
    def create_research_session(self, research_goal: str, config: Dict[str, Any]) -> str:
        """Create a new research session"""
        session_id = str(uuid.uuid4())
        
        session = self.db_manager.get_session()
        try:
            research_session = ResearchSession(
                session_id=session_id,
                research_goal=research_goal,
                max_sources=config.get('max_sources', 10),
                search_depth=config.get('search_depth', 'medium'),
                citation_style=config.get('citation_style', 'APA'),
                model_used=config.get('default_model', 'llama3-70b-8192'),
                status='active'
            )
            
            session.add(research_session)
            session.commit()
            
            logger.info(f"Created research session: {session_id}")
            return session_id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create research session: {str(e)}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def update_session_status(self, session_id: str, status: str, **kwargs) -> bool:
        """Update research session status and metadata"""
        session = self.db_manager.get_session()
        try:
            research_session = session.query(ResearchSession).filter_by(session_id=session_id).first()
            if not research_session:
                logger.warning(f"Research session not found: {session_id}")
                return False
            
            research_session.status = status
            research_session.updated_at = datetime.now()
            
            # Update additional fields if provided
            for key, value in kwargs.items():
                if hasattr(research_session, key):
                    setattr(research_session, key, value)
            
            if status == 'completed':
                research_session.completed_at = datetime.now()
            
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update session status: {str(e)}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def save_research_phase(self, session_id: str, phase_data: Dict[str, Any]) -> bool:
        """Save research phase data"""
        session = self.db_manager.get_session()
        try:
            research_phase = ResearchPhase(
                session_id=session_id,
                phase_id=phase_data.get('phase_id', ''),
                title=phase_data.get('phase_title', ''),
                description=phase_data.get('description', ''),
                status='completed' if phase_data.get('success') else 'failed',
                documents_retrieved=phase_data.get('documents_retrieved', 0),
                documents_stored=phase_data.get('documents_stored', 0),
                search_terms=phase_data.get('search_terms', []),
                expected_sources=phase_data.get('expected_sources', []),
                execution_time=phase_data.get('execution_time', 0.0),
                completed_at=datetime.now()
            )
            
            session.add(research_phase)
            session.commit()
            
            logger.debug(f"Saved research phase: {phase_data.get('phase_id')}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to save research phase: {str(e)}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def save_findings(self, session_id: str, findings: List[Dict[str, Any]]) -> int:
        """Save research findings"""
        session = self.db_manager.get_session()
        saved_count = 0
        
        try:
            for finding_data in findings:
                # Create content hash for deduplication
                content_str = json.dumps(finding_data.get('key_findings', []), sort_keys=True)
                content_hash = str(hash(content_str))
                
                # Check if finding already exists
                existing = session.query(Finding).filter_by(
                    session_id=session_id,
                    content_hash=content_hash
                ).first()
                
                if existing:
                    continue  # Skip duplicate
                
                finding = Finding(
                    session_id=session_id,
                    source_title=finding_data.get('source_title', ''),
                    source_url=finding_data.get('source_url', ''),
                    source_type=finding_data.get('source_type', 'web'),
                    key_findings=finding_data.get('key_findings', []),
                    relevant_facts=finding_data.get('relevant_facts', []),
                    statistics=finding_data.get('statistics', []),
                    conclusions=finding_data.get('conclusions', []),
                    relevance_score=finding_data.get('relevance_score', 0.0),
                    confidence_level=finding_data.get('confidence_level', 'medium'),
                    content_hash=content_hash
                )
                
                session.add(finding)
                saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} findings for session {session_id}")
            return saved_count
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to save findings: {str(e)}")
            return 0
        finally:
            self.db_manager.close_session(session)
    
    def save_citations(self, session_id: str, citations: List[Dict[str, Any]]) -> int:
        """Save citations"""
        session = self.db_manager.get_session()
        saved_count = 0
        
        try:
            for citation_data in citations:
                # Check for duplicate by URL and content
                existing = session.query(Citation).filter_by(
                    session_id=session_id,
                    url=citation_data.get('url', ''),
                    content=citation_data.get('content', '')
                ).first()
                
                if existing:
                    continue  # Skip duplicate
                
                citation = Citation(
                    session_id=session_id,
                    citation_type=citation_data.get('type', 'source'),
                    title=citation_data.get('title', ''),
                    authors=citation_data.get('authors', []),
                    url=citation_data.get('url', ''),
                    date=citation_data.get('date', ''),
                    source_type=citation_data.get('source_type', 'web'),
                    content=citation_data.get('content', ''),
                    context=citation_data.get('context', ''),
                    quote=citation_data.get('quote', ''),
                    page_section=citation_data.get('page_section', '')
                )
                
                session.add(citation)
                saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} citations for session {session_id}")
            return saved_count
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to save citations: {str(e)}")
            return 0
        finally:
            self.db_manager.close_session(session)
    
    def get_research_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get research session data"""
        session = self.db_manager.get_session()
        try:
            research_session = session.query(ResearchSession).filter_by(session_id=session_id).first()
            if not research_session:
                return None
            
            return {
                'session_id': research_session.session_id,
                'research_goal': research_session.research_goal,
                'status': research_session.status,
                'created_at': research_session.created_at.isoformat(),
                'completed_at': research_session.completed_at.isoformat() if research_session.completed_at else None,
                'total_sources': research_session.total_sources,
                'total_findings': research_session.total_findings,
                'total_citations': research_session.total_citations,
                'quality_score': research_session.quality_score,
                'execution_time': research_session.execution_time,
                'config': {
                    'max_sources': research_session.max_sources,
                    'search_depth': research_session.search_depth,
                    'citation_style': research_session.citation_style,
                    'model_used': research_session.model_used
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get research session: {str(e)}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_session_findings(self, session_id: str) -> List[Dict[str, Any]]:
        """Get findings for a research session"""
        session = self.db_manager.get_session()
        try:
            findings = session.query(Finding).filter_by(session_id=session_id).all()
            
            return [{
                'id': f.id,
                'source_title': f.source_title,
                'source_url': f.source_url,
                'source_type': f.source_type,
                'key_findings': f.key_findings,
                'relevant_facts': f.relevant_facts,
                'statistics': f.statistics,
                'conclusions': f.conclusions,
                'relevance_score': f.relevance_score,
                'confidence_level': f.confidence_level,
                'extracted_at': f.extracted_at.isoformat()
            } for f in findings]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get session findings: {str(e)}")
            return []
        finally:
            self.db_manager.close_session(session)
    
    def get_session_citations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get citations for a research session"""
        session = self.db_manager.get_session()
        try:
            citations = session.query(Citation).filter_by(session_id=session_id).all()
            
            return [{
                'id': c.id,
                'type': c.citation_type,
                'title': c.title,
                'authors': c.authors,
                'url': c.url,
                'date': c.date,
                'source_type': c.source_type,
                'content': c.content,
                'context': c.context,
                'quote': c.quote,
                'created_at': c.created_at.isoformat()
            } for c in citations]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get session citations: {str(e)}")
            return []
        finally:
            self.db_manager.close_session(session)
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent research sessions"""
        session = self.db_manager.get_session()
        try:
            sessions = session.query(ResearchSession).order_by(desc(ResearchSession.created_at)).limit(limit).all()
            
            return [{
                'session_id': s.session_id,
                'research_goal': s.research_goal,
                'status': s.status,
                'created_at': s.created_at.isoformat(),
                'total_sources': s.total_sources,
                'total_findings': s.total_findings,
                'quality_score': s.quality_score
            } for s in sessions]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get recent sessions: {str(e)}")
            return []
        finally:
            self.db_manager.close_session(session)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get research analytics and statistics"""
        session = self.db_manager.get_session()
        try:
            # Basic counts
            total_sessions = session.query(ResearchSession).count()
            completed_sessions = session.query(ResearchSession).filter_by(status='completed').count()
            total_findings = session.query(Finding).count()
            total_citations = session.query(Citation).count()
            
            # Average quality score
            avg_quality = session.query(func.avg(ResearchSession.quality_score)).filter(
                ResearchSession.quality_score.isnot(None)
            ).scalar() or 0.0
            
            # Recent activity (last 7 days)
            from sqlalchemy import and_
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            
            recent_sessions = session.query(ResearchSession).filter(
                ResearchSession.created_at >= week_ago
            ).count()
            
            return {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'success_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'total_findings': total_findings,
                'total_citations': total_citations,
                'average_quality_score': round(avg_quality, 2),
                'recent_sessions_7d': recent_sessions,
                'avg_findings_per_session': round(total_findings / total_sessions, 1) if total_sessions > 0 else 0,
                'avg_citations_per_session': round(total_citations / total_sessions, 1) if total_sessions > 0 else 0
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get analytics: {str(e)}")
            return {}
        finally:
            self.db_manager.close_session(session)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a research session and all related data"""
        session = self.db_manager.get_session()
        try:
            research_session = session.query(ResearchSession).filter_by(session_id=session_id).first()
            if not research_session:
                return False
            
            # SQLAlchemy will handle cascade deletes for related records
            session.delete(research_session)
            session.commit()
            
            logger.info(f"Deleted research session: {session_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete session: {str(e)}")
            return False
        finally:
            self.db_manager.close_session(session)