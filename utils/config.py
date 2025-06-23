"""
Configuration Module

Manages configuration settings for the autonomous research agent including
API keys, research parameters, and system settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration class for the autonomous research agent"""
    
    # API Configuration
    groq_api_key: str
    
    # Research Parameters
    max_sources: int = 10
    search_depth: str = "medium"  # shallow, medium, deep
    citation_style: str = "APA"   # APA, MLA, Chicago
    
    # Quality Thresholds
    min_relevance_score: float = 0.3
    min_source_quality: float = 0.5
    
    # Memory Configuration
    memory_collection_name: str = "research_memory"
    max_memory_items: int = 1000
    
    # LLM Configuration
    default_model: str = "llama3-70b-8192"
    max_tokens_default: int = 1000
    temperature_default: float = 0.7
    
    # Search Configuration
    web_search_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Report Configuration
    max_findings_per_phase: int = 20
    max_citations_display: int = 50
    include_appendices: bool = True
    
    @classmethod
    def from_environment(cls) -> 'Config':
        """
        Create configuration from environment variables
        
        Returns:
            Config instance with environment-based settings
        """
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            max_sources=int(os.getenv("MAX_SOURCES", "10")),
            search_depth=os.getenv("SEARCH_DEPTH", "medium"),
            citation_style=os.getenv("CITATION_STYLE", "APA"),
            min_relevance_score=float(os.getenv("MIN_RELEVANCE_SCORE", "0.3")),
            min_source_quality=float(os.getenv("MIN_SOURCE_QUALITY", "0.5")),
            memory_collection_name=os.getenv("MEMORY_COLLECTION_NAME", "research_memory"),
            max_memory_items=int(os.getenv("MAX_MEMORY_ITEMS", "1000")),
            default_model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            max_tokens_default=int(os.getenv("MAX_TOKENS_DEFAULT", "1000")),
            temperature_default=float(os.getenv("TEMPERATURE_DEFAULT", "0.7")),
            web_search_timeout=int(os.getenv("WEB_SEARCH_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            max_findings_per_phase=int(os.getenv("MAX_FINDINGS_PER_PHASE", "20")),
            max_citations_display=int(os.getenv("MAX_CITATIONS_DISPLAY", "50")),
            include_appendices=bool(os.getenv("INCLUDE_APPENDICES", "True").lower() == "true")
        )
    
    @classmethod
    def create_default(cls, groq_api_key: str) -> 'Config':
        """
        Create configuration with default settings
        
        Args:
            groq_api_key: CloudGROQ API key
            
        Returns:
            Config instance with default settings
        """
        return cls(groq_api_key=groq_api_key)
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration settings
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Validate required fields
        if not self.groq_api_key:
            issues.append("CloudGROQ API key is required")
        
        # Validate numeric ranges
        if self.max_sources < 1 or self.max_sources > 100:
            warnings.append("max_sources should be between 1 and 100")
        
        if self.min_relevance_score < 0 or self.min_relevance_score > 1:
            warnings.append("min_relevance_score should be between 0 and 1")
        
        if self.min_source_quality < 0 or self.min_source_quality > 1:
            warnings.append("min_source_quality should be between 0 and 1")
        
        if self.temperature_default < 0 or self.temperature_default > 2:
            warnings.append("temperature_default should be between 0 and 2")
        
        # Validate string choices
        valid_depths = ["shallow", "medium", "deep"]
        if self.search_depth not in valid_depths:
            warnings.append(f"search_depth should be one of: {', '.join(valid_depths)}")
        
        valid_styles = ["APA", "MLA", "Chicago"]
        if self.citation_style not in valid_styles:
            warnings.append(f"citation_style should be one of: {', '.join(valid_styles)}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'groq_api_key': '***hidden***' if self.groq_api_key else None,
            'max_sources': self.max_sources,
            'search_depth': self.search_depth,
            'citation_style': self.citation_style,
            'min_relevance_score': self.min_relevance_score,
            'min_source_quality': self.min_source_quality,
            'memory_collection_name': self.memory_collection_name,
            'max_memory_items': self.max_memory_items,
            'default_model': self.default_model,
            'max_tokens_default': self.max_tokens_default,
            'temperature_default': self.temperature_default,
            'web_search_timeout': self.web_search_timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'max_findings_per_phase': self.max_findings_per_phase,
            'max_citations_display': self.max_citations_display,
            'include_appendices': self.include_appendices
        }
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration from dictionary
        
        Args:
            config_dict: Dictionary with configuration updates
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_search_config(self) -> Dict[str, Any]:
        """
        Get search-specific configuration
        
        Returns:
            Dictionary with search configuration
        """
        return {
            'max_sources': self.max_sources,
            'search_depth': self.search_depth,
            'timeout': self.web_search_timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'min_relevance_score': self.min_relevance_score,
            'min_source_quality': self.min_source_quality
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM-specific configuration
        
        Returns:
            Dictionary with LLM configuration
        """
        return {
            'api_key': self.groq_api_key,
            'model': self.default_model,
            'max_tokens': self.max_tokens_default,
            'temperature': self.temperature_default
        }
    
    def get_memory_config(self) -> Dict[str, Any]:
        """
        Get memory-specific configuration
        
        Returns:
            Dictionary with memory configuration
        """
        return {
            'collection_name': self.memory_collection_name,
            'max_items': self.max_memory_items
        }
    
    def get_citation_config(self) -> Dict[str, Any]:
        """
        Get citation-specific configuration
        
        Returns:
            Dictionary with citation configuration
        """
        return {
            'style': self.citation_style,
            'max_display': self.max_citations_display
        }
    
    def get_report_config(self) -> Dict[str, Any]:
        """
        Get report-specific configuration
        
        Returns:
            Dictionary with report configuration
        """
        return {
            'max_findings_per_phase': self.max_findings_per_phase,
            'max_citations_display': self.max_citations_display,
            'include_appendices': self.include_appendices,
            'citation_style': self.citation_style
        }

class ConfigManager:
    """Manager for configuration persistence and updates"""
    
    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path or "config.json"
        self._config = None
    
    def load_config(self) -> Config:
        """
        Load configuration from file or environment
        
        Returns:
            Loaded configuration
        """
        if self._config is None:
            # Try to load from environment first
            self._config = Config.from_environment()
            
            # Validate configuration
            validation = self._config.validate()
            if not validation['valid']:
                raise ValueError(f"Invalid configuration: {', '.join(validation['issues'])}")
        
        return self._config
    
    def save_config(self, config: Config) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import json
            config_dict = config.to_dict()
            
            with open(self.config_file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> Config:
        """
        Update current configuration
        
        Args:
            updates: Configuration updates
            
        Returns:
            Updated configuration
        """
        if self._config is None:
            self._config = self.load_config()
        
        self._config.update_from_dict(updates)
        
        # Validate updated configuration
        validation = self._config.validate()
        if not validation['valid']:
            raise ValueError(f"Invalid configuration after update: {', '.join(validation['issues'])}")
        
        return self._config
    
    def reset_config(self) -> Config:
        """
        Reset configuration to defaults
        
        Returns:
            Reset configuration
        """
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        self._config = Config.create_default(groq_api_key)
        return self._config
