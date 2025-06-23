"""
Retriever Module

Handles information retrieval from multiple sources including web search,
PDF documents, and academic papers.
"""

import re
import requests
import trafilatura
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import time
from duckduckgo_search import DDGS
import arxiv
from utils.logger import get_logger

logger = get_logger(__name__)

class Retriever:
    """Retrieve information from multiple sources"""
    
    def __init__(self, config):
        self.config = config
        self.ddgs = DDGS()
        
    def search_web(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with metadata
        """
        logger.info(f"Searching web for: {query}")
        
        try:
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                try:
                    # Extract clean content from the webpage
                    content = self._extract_web_content(result['href'])
                    
                    if content:
                        results.append({
                            'title': result.get('title', ''),
                            'url': result.get('href', ''),
                            'snippet': result.get('body', ''),
                            'content': content,
                            'source_type': 'web',
                            'retrieved_at': self._get_timestamp()
                        })
                        
                        # Small delay to be respectful
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract content from {result.get('href', '')}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(results)} web results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {str(e)}")
            return []
    
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search arXiv for academic papers
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of academic paper results
        """
        logger.info(f"Searching arXiv for: {query}")
        
        try:
            results = []
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for paper in client.results(search):
                results.append({
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'abstract': paper.summary,
                    'url': paper.entry_id,
                    'pdf_url': paper.pdf_url,
                    'published': paper.published.isoformat() if paper.published else None,
                    'categories': paper.categories,
                    'content': paper.summary,  # Using abstract as content
                    'source_type': 'academic',
                    'retrieved_at': self._get_timestamp()
                })
            
            logger.info(f"Retrieved {len(results)} arXiv results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"arXiv search failed for query '{query}': {str(e)}")
            return []
    
    def retrieve_from_sources(self, search_terms: List[str], source_types: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve information from multiple sources based on search terms
        
        Args:
            search_terms: List of search terms/queries
            source_types: Types of sources to search ('web', 'academic')
            
        Returns:
            Combined list of results from all sources
        """
        all_results = []
        
        for term in search_terms:
            if 'web' in source_types:
                web_results = self.search_web(term, max_results=self.config.max_sources // len(search_terms))
                all_results.extend(web_results)
            
            if 'academic' in source_types:
                arxiv_results = self.search_arxiv(term, max_results=3)
                all_results.extend(arxiv_results)
        
        # Deduplicate results based on URL
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        logger.info(f"Retrieved {len(unique_results)} unique results from {len(search_terms)} search terms")
        return unique_results
    
    def _extract_web_content(self, url: str) -> Optional[str]:
        """
        Extract clean text content from a webpage
        
        Args:
            url: URL to extract content from
            
        Returns:
            Clean text content or None if extraction fails
        """
        try:
            # Download the webpage
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            
            # Extract clean text
            text = trafilatura.extract(downloaded)
            
            if text and len(text) > 100:  # Ensure we have substantial content
                return text
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/]', '', text)
        
        return text.strip()
    
    def _get_timestamp(self) -> str:
       """Get current timestamp"""
       from datetime import datetime
       return datetime.now().isoformat()
    
    def get_content_summary(self, content: str, max_length: int = 500) -> str:
        """
        Get a summary of content for preview purposes
        
        Args:
            content: Full content text
            max_length: Maximum length of summary
            
        Returns:
            Summarized content
        """
        if not content:
            return ""
        
        if len(content) <= max_length:
            return content
        
        # Find a good breaking point near the max length
        summary = content[:max_length]
        last_sentence = summary.rfind('.')
        
        if last_sentence > max_length * 0.7:  # If we find a sentence end in the last 30%
            summary = summary[:last_sentence + 1]
        
        return summary + "..."
    
    def validate_source_quality(self, source: Dict[str, Any]) -> float:
        """
        Validate the quality of a retrieved source
        
        Args:
            source: Source dictionary
            
        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        
        # Check content length
        content_length = len(source.get('content', ''))
        if content_length > 1000:
            score += 0.3
        elif content_length > 500:
            score += 0.2
        elif content_length > 100:
            score += 0.1
        
        # Check if it's an academic source
        if source.get('source_type') == 'academic':
            score += 0.3
        
        # Check for title and URL
        if source.get('title'):
            score += 0.2
        if source.get('url'):
            score += 0.2
        
        return min(score, 1.0)
