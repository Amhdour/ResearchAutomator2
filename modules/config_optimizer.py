"""
Configuration Optimizer Module

Provides intelligent configuration suggestions and optimizations
based on usage patterns and API limitations.
"""

from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)

class ConfigOptimizer:
    """Optimize configuration based on usage patterns and constraints"""
    
    def __init__(self, config):
        self.config = config
        
    def optimize_for_rate_limits(self) -> Dict[str, Any]:
        """Optimize configuration to work better with API rate limits"""
        optimizations = {}
        
        # Reduce max sources to limit API calls
        if self.config.max_sources > 5:
            optimizations['max_sources'] = 5
            logger.info("Reduced max_sources to 5 to manage API rate limits")
        
        # Use more conservative temperature for consistent results
        if self.config.temperature_default > 0.5:
            optimizations['temperature_default'] = 0.3
            logger.info("Reduced temperature for more deterministic results")
        
        # Reduce max tokens to fit within limits
        if self.config.max_tokens_default > 800:
            optimizations['max_tokens_default'] = 600
            logger.info("Reduced max_tokens to fit within rate limits")
        
        # Increase retry delays
        if self.config.retry_delay < 2.0:
            optimizations['retry_delay'] = 3.0
            logger.info("Increased retry delay for better rate limit handling")
        
        return optimizations
    
    def suggest_free_tier_config(self) -> Dict[str, Any]:
        """Suggest configuration optimized for free tier usage"""
        return {
            'max_sources': 3,
            'search_depth': 'shallow',
            'max_tokens_default': 400,
            'temperature_default': 0.3,
            'max_findings_per_phase': 10,
            'retry_delay': 5.0,
            'max_retries': 2
        }
    
    def estimate_token_usage(self, research_goal: str) -> Dict[str, int]:
        """Estimate token usage for a research goal"""
        goal_complexity = len(research_goal.split())
        
        # Rough estimates based on goal complexity
        base_tokens = 1000
        per_source_tokens = 800
        synthesis_tokens = 1500
        report_tokens = 2000
        
        estimated_sources = min(self.config.max_sources, max(3, goal_complexity // 5))
        
        total_estimated = (
            base_tokens + 
            (estimated_sources * per_source_tokens) +
            synthesis_tokens +
            report_tokens
        )
        
        return {
            'estimated_total_tokens': total_estimated,
            'estimated_sources': estimated_sources,
            'base_tokens': base_tokens,
            'per_source_tokens': per_source_tokens * estimated_sources,
            'synthesis_tokens': synthesis_tokens,
            'report_tokens': report_tokens
        }
    
    def suggest_model_alternatives(self) -> List[Dict[str, str]]:
        """Suggest alternative models for different use cases"""
        return [
            {
                'model': 'llama3-8b-8192',
                'use_case': 'Faster responses, lower token usage',
                'pros': 'Faster, uses fewer tokens',
                'cons': 'Less sophisticated reasoning'
            },
            {
                'model': 'mixtral-8x7b-32768',
                'use_case': 'Balanced performance and efficiency',
                'pros': 'Good balance of speed and quality',
                'cons': 'Moderate token usage'
            },
            {
                'model': 'llama3-70b-8192',
                'use_case': 'Best quality for complex research',
                'pros': 'Highest quality responses',
                'cons': 'Slower, uses more tokens'
            }
        ]