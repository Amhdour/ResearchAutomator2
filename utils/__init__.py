"""
Utilities Package

Common utilities for the autonomous research agent including configuration
management, logging, and helper functions.
"""

from .config import Config, ConfigManager
from .logger import setup_logger, get_logger, LoggerMixin, ResearchLogger, configure_logging_level

__version__ = "1.0.0"
__all__ = [
    'Config',
    'ConfigManager', 
    'setup_logger',
    'get_logger',
    'LoggerMixin',
    'ResearchLogger',
    'configure_logging_level'
]

# Initialize package-level logger
_package_logger = get_logger(__name__)
_package_logger.info("Autonomous Research Agent utilities package initialized")
