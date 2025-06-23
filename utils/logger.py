"""
Logger Module

Provides consistent logging functionality across the autonomous research agent.
Configures structured logging with appropriate levels and formatting.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import os

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the record
        return super().format(record)

def setup_logger(name: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    Set up logger with consistent formatting
    
    Args:
        name: Logger name (defaults to 'autonomous_research_agent')
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    if name is None:
        name = "autonomous_research_agent"
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if logs directory exists or can be created)
    try:
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        log_filename = f"{logs_dir}/research_agent_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)  # More detailed logging to file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
    except (OSError, PermissionError):
        # If we can't create log files, just use console logging
        pass
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get logger for specific module
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance for the module
    """
    # Create module-specific logger name
    if name == "__main__":
        logger_name = "autonomous_research_agent.main"
    elif name.startswith("modules."):
        logger_name = f"autonomous_research_agent.{name}"
    elif name.startswith("utils."):
        logger_name = f"autonomous_research_agent.{name}"
    else:
        logger_name = f"autonomous_research_agent.{name}"
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    
    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        # Get log level from environment or default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger = setup_logger(logger_name, log_level)
    
    return logger

class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        class_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(class_name)

class ResearchLogger:
    """Specialized logger for research operations"""
    
    def __init__(self, research_session_id: str):
        self.session_id = research_session_id
        self.logger = get_logger(f"research_session_{research_session_id}")
        self.start_time = datetime.now()
        
    def log_phase_start(self, phase_name: str, phase_id: str) -> None:
        """Log the start of a research phase"""
        self.logger.info(f"Phase Started - {phase_name} (ID: {phase_id})")
    
    def log_phase_complete(self, phase_name: str, phase_id: str, duration: float, 
                          findings_count: int, sources_count: int) -> None:
        """Log the completion of a research phase"""
        self.logger.info(
            f"Phase Completed - {phase_name} (ID: {phase_id}) | "
            f"Duration: {duration:.2f}s | Findings: {findings_count} | Sources: {sources_count}"
        )
    
    def log_source_retrieved(self, source_title: str, source_url: str, 
                           content_length: int, relevance_score: float) -> None:
        """Log successful source retrieval"""
        self.logger.debug(
            f"Source Retrieved - {source_title[:50]}... | "
            f"Content: {content_length} chars | Relevance: {relevance_score:.2f}"
        )
    
    def log_source_failed(self, source_url: str, error: str) -> None:
        """Log failed source retrieval"""
        self.logger.warning(f"Source Failed - {source_url} | Error: {error}")
    
    def log_llm_call(self, operation: str, prompt_length: int, 
                     response_length: int, duration: float) -> None:
        """Log LLM API calls"""
        self.logger.debug(
            f"LLM Call - {operation} | "
            f"Prompt: {prompt_length} chars | Response: {response_length} chars | "
            f"Duration: {duration:.2f}s"
        )
    
    def log_quality_check(self, component: str, score: float, issues: list) -> None:
        """Log quality check results"""
        status = "PASS" if score >= 0.7 else "REVIEW" if score >= 0.5 else "FAIL"
        self.logger.info(
            f"Quality Check - {component} | Score: {score:.2f} | Status: {status} | "
            f"Issues: {len(issues)}"
        )
    
    def log_research_complete(self, total_findings: int, total_sources: int, 
                            total_citations: int, overall_quality: float) -> None:
        """Log research completion"""
        duration = (datetime.now() - self.start_time).total_seconds()
        self.logger.info(
            f"Research Complete - Session: {self.session_id} | "
            f"Duration: {duration:.1f}s | Findings: {total_findings} | "
            f"Sources: {total_sources} | Citations: {total_citations} | "
            f"Quality: {overall_quality:.2f}"
        )

def configure_logging_level(level: str) -> None:
    """
    Configure logging level for all research agent loggers
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Update all existing research agent loggers
    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith("autonomous_research_agent"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
            
            # Update handler levels
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(log_level)

def get_log_stats() -> dict:
    """
    Get statistics about current logging configuration
    
    Returns:
        Dictionary with logging statistics
    """
    stats = {
        'active_loggers': 0,
        'total_handlers': 0,
        'file_handlers': 0,
        'console_handlers': 0,
        'log_levels': {}
    }
    
    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith("autonomous_research_agent"):
            logger = logging.getLogger(logger_name)
            stats['active_loggers'] += 1
            stats['total_handlers'] += len(logger.handlers)
            
            # Count handler types
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    stats['file_handlers'] += 1
                elif isinstance(handler, logging.StreamHandler):
                    stats['console_handlers'] += 1
            
            # Count log levels
            level_name = logging.getLevelName(logger.level)
            stats['log_levels'][level_name] = stats['log_levels'].get(level_name, 0) + 1
    
    return stats

# Initialize root logger on module import
_root_logger = setup_logger()
