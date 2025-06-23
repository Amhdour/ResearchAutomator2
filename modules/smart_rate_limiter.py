"""
Smart Rate Limiter Module

Advanced rate limiting with token usage prediction and dynamic model switching.
"""

import time
import json
from typing import Dict, Any, Optional, Callable
from utils.logger import get_logger

logger = get_logger(__name__)

class SmartRateLimiter:
    """Advanced rate limiter with token prediction and model switching"""
    
    def __init__(self, config):
        self.config = config
        self.token_usage_log = []
        self.rate_limit_window = 60  # CloudGROQ rate limit window in seconds
        self.models_by_speed = [
            {'name': 'llama3-8b-8192', 'max_tokens': 8192, 'speed': 'fast', 'token_limit': 30000},
            {'name': 'mixtral-8x7b-32768', 'max_tokens': 32768, 'speed': 'medium', 'token_limit': 6000},
            {'name': 'llama3-70b-8192', 'max_tokens': 8192, 'speed': 'slow', 'token_limit': 6000}
        ]
        
    def estimate_tokens(self, prompt: str) -> int:
        """Estimate token count for a prompt (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(prompt) // 3
        
    def get_best_model(self, estimated_tokens: int, task_type: str = 'general') -> str:
        """Select best model based on token estimate and task type"""
        current_usage = self._get_current_minute_usage()
        
        # For simple tasks, prefer faster models
        if task_type in ['citation', 'extraction'] or estimated_tokens < 200:
            return 'llama3-8b-8192'
        
        # Check which models we can use without hitting limits
        for model in self.models_by_speed:
            if current_usage + estimated_tokens < model['token_limit'] * 0.8:  # 80% safety margin
                return model['name']
        
        # Fallback to fastest model
        return 'llama3-8b-8192'
    
    def should_wait(self, estimated_tokens: int) -> float:
        """Determine if we should wait and for how long"""
        current_usage = self._get_current_minute_usage()
        
        # If we're close to any limit, wait
        for model in self.models_by_speed:
            if current_usage + estimated_tokens > model['token_limit'] * 0.9:
                # Calculate wait time until usage drops
                oldest_in_window = self._get_oldest_usage_in_window()
                if oldest_in_window:
                    wait_time = 60 - (time.time() - oldest_in_window['timestamp'])
                    return max(0, wait_time)
        
        return 0
    
    def log_usage(self, tokens_used: int, model: str):
        """Log token usage for tracking"""
        self.token_usage_log.append({
            'timestamp': time.time(),
            'tokens': tokens_used,
            'model': model
        })
        
        # Keep only last hour of data
        cutoff_time = time.time() - 3600
        self.token_usage_log = [
            log for log in self.token_usage_log 
            if log['timestamp'] > cutoff_time
        ]
    
    def _get_current_minute_usage(self) -> int:
        """Get token usage in current minute"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        return sum(
            log['tokens'] for log in self.token_usage_log
            if log['timestamp'] > minute_ago
        )
    
    def _get_oldest_usage_in_window(self) -> Optional[Dict]:
        """Get oldest usage record in current window"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        in_window = [
            log for log in self.token_usage_log
            if log['timestamp'] > minute_ago
        ]
        
        return min(in_window, key=lambda x: x['timestamp']) if in_window else None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        current_usage = self._get_current_minute_usage()
        
        return {
            'current_minute_tokens': current_usage,
            'percentage_of_limit': (current_usage / 6000) * 100,
            'recommended_model': self.get_best_model(500),
            'safe_to_proceed': current_usage < 5000
        }