"""
Rate Limiter Module

Manages API rate limiting and implements retry logic with exponential backoff
to handle CloudGROQ API limits gracefully.
"""

import time
import asyncio
from typing import Callable, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiter with exponential backoff for API calls"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.last_call_time = 0
        self.min_interval = 1.0  # Minimum seconds between calls
        
    def wait_if_needed(self) -> None:
        """Wait if minimum interval hasn't passed since last call"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    def call_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with exponential backoff on rate limit errors"""
        self.wait_if_needed()
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "rate_limit_exceeded" in error_str or "429" in error_str:
                    if attempt < self.max_retries:
                        # Extract wait time from error message if available
                        wait_time = self._extract_wait_time(error_str)
                        if wait_time is None:
                            wait_time = self.base_delay * (2 ** attempt)
                        
                        logger.warning(f"Rate limited, waiting {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for rate limiting")
                        raise
                else:
                    # Not a rate limit error, re-raise immediately
                    raise
        
        return None
    
    def _extract_wait_time(self, error_message: str) -> Optional[float]:
        """Extract wait time from CloudGROQ error message"""
        try:
            # Look for pattern like "Please try again in 1.601999999s"
            import re
            match = re.search(r'try again in (\d+\.?\d*)s', error_message)
            if match:
                return float(match.group(1)) + 0.5  # Add small buffer
        except:
            pass
        return None