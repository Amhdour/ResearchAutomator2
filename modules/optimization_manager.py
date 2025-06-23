"""
Optimization Manager Module

Manages API usage optimization, caching, and intelligent content reduction.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class OptimizationManager:
    """Manages optimization strategies for reduced API usage"""
    
    def __init__(self, config):
        self.config = config
        self.response_cache = {}
        self.token_usage_tracker = []
        
    def optimize_prompt(self, prompt: str, task_type: str = 'general') -> str:
        """Optimize prompts to reduce token usage while maintaining quality"""
        
        optimizations = {
            'citation': self._optimize_citation_prompt,
            'extraction': self._optimize_extraction_prompt,
            'synthesis': self._optimize_synthesis_prompt,
            'planning': self._optimize_planning_prompt,
            'general': self._optimize_general_prompt
        }
        
        optimizer = optimizations.get(task_type, self._optimize_general_prompt)
        return optimizer(prompt)
    
    def should_skip_llm_call(self, content: str, task_type: str) -> bool:
        """Determine if we can skip an LLM call based on content analysis"""
        
        # Skip very short content
        if len(content.strip()) < 50:
            logger.info(f"Skipping LLM call for short content ({len(content)} chars)")
            return True
        
        # Skip if content is mostly URLs or references
        lines = content.split('\n')
        url_lines = sum(1 for line in lines if 'http' in line or 'www.' in line)
        if url_lines / len(lines) > 0.7:
            logger.info("Skipping LLM call for URL-heavy content")
            return True
        
        # Skip repeated content (check cache)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.response_cache:
            logger.info("Using cached response for duplicate content")
            return True
        
        return False
    
    def get_cached_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return self.response_cache.get(content_hash)
    
    def cache_response(self, content: str, response: Dict[str, Any]):
        """Cache response for future use"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self.response_cache[content_hash] = response
        
        # Keep cache size manageable
        if len(self.response_cache) > 100:
            # Remove oldest entries
            keys_to_remove = list(self.response_cache.keys())[:-50]
            for key in keys_to_remove:
                del self.response_cache[key]
    
    def create_fallback_citations(self, source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create basic citations without LLM when rate limited"""
        citations = []
        
        if source_metadata.get('title') and source_metadata.get('url'):
            citation = {
                'type': 'source',
                'title': source_metadata['title'],
                'url': source_metadata['url'],
                'authors': source_metadata.get('authors', []),
                'date': source_metadata.get('published', ''),
                'source_type': source_metadata.get('type', 'web'),
                'content': f"Source: {source_metadata['title']}",
                'context': 'Retrieved document',
                'quote': '',
                'fallback': True  # Mark as fallback citation
            }
            citations.append(citation)
        
        return citations
    
    def extract_key_info_simple(self, content: str) -> Dict[str, Any]:
        """Extract key information using simple text analysis when LLM unavailable"""
        lines = content.split('\n')
        sentences = content.split('.')
        
        # Simple keyword extraction
        key_findings = []
        statistics = []
        conclusions = []
        
        # Look for sentences with key indicators
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            # Check for statistical information
            if any(indicator in sentence.lower() for indicator in ['%', 'percent', 'study found', 'research shows', 'data indicates']):
                statistics.append(sentence)
            
            # Check for conclusions
            elif any(indicator in sentence.lower() for indicator in ['conclude', 'therefore', 'in summary', 'results show']):
                conclusions.append(sentence)
            
            # General key findings
            elif any(indicator in sentence.lower() for indicator in ['important', 'significant', 'key', 'main', 'primary']):
                key_findings.append(sentence)
        
        return {
            'key_findings': key_findings[:3],  # Limit results
            'relevant_facts': sentences[:3],
            'statistics': statistics[:2],
            'conclusions': conclusions[:2],
            'confidence_level': 'low',  # Mark as simple extraction
            'relevance_score': 0.5,
            'fallback_extraction': True
        }
    
    def _optimize_citation_prompt(self, prompt: str) -> str:
        """Optimize citation extraction prompts"""
        return f"Extract 2-3 key citations from this text. Be concise:\n\n{prompt[:1000]}"
    
    def _optimize_extraction_prompt(self, prompt: str) -> str:
        """Optimize information extraction prompts"""
        return f"Extract main points in bullet format. Max 5 points:\n\n{prompt[:800]}"
    
    def _optimize_synthesis_prompt(self, prompt: str) -> str:
        """Optimize synthesis prompts"""
        return f"Summarize key insights in 2-3 sentences:\n\n{prompt[:600]}"
    
    def _optimize_planning_prompt(self, prompt: str) -> str:
        """Optimize planning prompts"""
        return f"Create 3-4 research phases. Be specific:\n\n{prompt[:500]}"
    
    def _optimize_general_prompt(self, prompt: str) -> str:
        """General prompt optimization"""
        # Remove excessive whitespace and redundant instructions
        optimized = ' '.join(prompt.split())
        
        # Truncate if too long
        if len(optimized) > 1000:
            optimized = optimized[:1000] + "..."
        
        return optimized
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'cached_responses': len(self.response_cache),
            'cache_hit_rate': 0.0,  # Would track in production
            'avg_prompt_length': 500,  # Would calculate from usage
            'fallback_extractions': 0  # Would track usage
        }