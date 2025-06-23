"""
Citation Engine Module

Manages citation extraction, formatting, and source attribution
for research content using various academic citation styles.
"""

import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from .llm_tools import LLMTools
from .optimization_manager import OptimizationManager
from utils.logger import get_logger

logger = get_logger(__name__)

class CitationEngine:
    """Handle citation extraction and formatting"""
    
    def __init__(self, config):
        self.config = config
        self.llm_tools = LLMTools(config)
        self.optimizer = OptimizationManager(config)
        self.citation_style = config.citation_style.lower()
        
    def extract_citations_from_content(self, content: str, source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract citation-worthy information from content
        
        Args:
            content: Text content to analyze
            source_metadata: Metadata about the source
            
        Returns:
            List of citation entries
        """
        logger.info(f"Extracting citations from content: {source_metadata.get('title', 'Unknown')[:50]}...")
        
        try:
            # Create citation extraction prompt
            extraction_prompt = self._create_citation_prompt(content, source_metadata)
            
            # Extract citation information using LLM
            response = self.llm_tools.generate_text(
                prompt=extraction_prompt,
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse the response
            citations = self._parse_citation_response(response, source_metadata)
            
            logger.info(f"Extracted {len(citations)} citations from source")
            return citations
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {str(e)}")
            return [self._create_basic_citation(source_metadata)]
    
    def format_citation(self, citation_data: Dict[str, Any]) -> str:
        """
        Format citation according to specified style
        
        Args:
            citation_data: Citation information
            
        Returns:
            Formatted citation string
        """
        try:
            if self.citation_style == 'apa':
                return self._format_apa_citation(citation_data)
            elif self.citation_style == 'mla':
                return self._format_mla_citation(citation_data)
            elif self.citation_style == 'chicago':
                return self._format_chicago_citation(citation_data)
            else:
                return self._format_apa_citation(citation_data)  # Default to APA
                
        except Exception as e:
            logger.error(f"Citation formatting failed: {str(e)}")
            return f"Source: {citation_data.get('title', 'Unknown source')}"
    
    def create_bibliography(self, citations: List[Dict[str, Any]]) -> str:
        """
        Create a formatted bibliography from citations
        
        Args:
            citations: List of citation data
            
        Returns:
            Formatted bibliography string
        """
        logger.info(f"Creating bibliography with {len(citations)} citations")
        
        # Remove duplicates based on URL or title
        unique_citations = self._deduplicate_citations(citations)
        
        # Sort citations alphabetically by title or author
        sorted_citations = sorted(unique_citations, key=lambda x: x.get('title', '').lower())
        
        # Format each citation
        formatted_citations = []
        for citation in sorted_citations:
            formatted = self.format_citation(citation)
            if formatted:
                formatted_citations.append(formatted)
        
        # Create bibliography header
        style_name = self.citation_style.upper()
        bibliography = f"## References ({style_name} Style)\n\n"
        
        # Add citations
        for i, citation in enumerate(formatted_citations, 1):
            bibliography += f"{i}. {citation}\n\n"
        
        return bibliography
    
    def link_claims_to_sources(self, content: str, citations: List[Dict[str, Any]]) -> str:
        """
        Link specific claims in content to their sources
        
        Args:
            content: Content with claims to link
            citations: Available citations
            
        Returns:
            Content with citation links added
        """
        try:
            # Create linking prompt
            linking_prompt = self._create_linking_prompt(content, citations)
            
            # Get linked content from LLM
            linked_content = self.llm_tools.generate_text(
                prompt=linking_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            return linked_content
            
        except Exception as e:
            logger.error(f"Citation linking failed: {str(e)}")
            return content  # Return original content on failure
    
    def validate_citation_quality(self, citation: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate the quality and completeness of a citation
        
        Args:
            citation: Citation data to validate
            
        Returns:
            Validation results with issues and suggestions
        """
        issues = []
        suggestions = []
        
        # Check required fields
        required_fields = ['title', 'url']
        for field in required_fields:
            if not citation.get(field):
                issues.append(f"Missing {field}")
                suggestions.append(f"Add {field} information")
        
        # Check URL validity
        url = citation.get('url', '')
        if url and not self._is_valid_url(url):
            issues.append("Invalid URL format")
            suggestions.append("Verify URL is correct and accessible")
        
        # Check date format
        date = citation.get('date', '')
        if date and not self._is_valid_date(date):
            issues.append("Invalid date format")
            suggestions.append("Use standard date format (YYYY-MM-DD)")
        
        # Check for academic source indicators
        if citation.get('source_type') == 'academic':
            if not citation.get('authors'):
                issues.append("Academic source missing author information")
                suggestions.append("Add author names for academic credibility")
        
        return {
            'quality_score': max(0, 1.0 - len(issues) * 0.2),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _create_citation_prompt(self, content: str, source_metadata: Dict[str, Any]) -> str:
        """Create prompt for citation extraction"""
        return f"""
Analyze the following content and extract citation-worthy information.

Source Metadata:
- Title: {source_metadata.get('title', 'Unknown')}
- URL: {source_metadata.get('url', 'Unknown')}
- Source Type: {source_metadata.get('source_type', 'web')}
- Retrieved: {source_metadata.get('retrieved_at', 'Unknown')}

Content to analyze:
{content[:2000]}

Extract key quotable claims, statistics, and findings that should be cited. Format as JSON:
{{
    "key_claims": [
        {{
            "claim": "Specific claim or finding",
            "context": "Surrounding context",
            "quote": "Direct quote if applicable",
            "page_section": "Section where found"
        }}
    ],
    "statistics": [
        {{
            "statistic": "Numerical finding",
            "context": "What it measures",
            "source_detail": "Specific source within the document"
        }}
    ],
    "author_insights": [
        {{
            "insight": "Author's conclusion or opinion",
            "quote": "Direct quote"
        }}
    ]
}}

Focus on factual, verifiable information that adds value to research.
"""

    def _parse_citation_response(self, response: str, source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse citation extraction response"""
        citations = []
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Process key claims
                for claim in data.get('key_claims', []):
                    citations.append({
                        'type': 'claim',
                        'content': claim.get('claim', ''),
                        'context': claim.get('context', ''),
                        'quote': claim.get('quote', ''),
                        'title': source_metadata.get('title', ''),
                        'url': source_metadata.get('url', ''),
                        'authors': source_metadata.get('authors', []),
                        'date': self._extract_date(source_metadata),
                        'source_type': source_metadata.get('source_type', 'web'),
                        'page_section': claim.get('page_section', '')
                    })
                
                # Process statistics
                for stat in data.get('statistics', []):
                    citations.append({
                        'type': 'statistic',
                        'content': stat.get('statistic', ''),
                        'context': stat.get('context', ''),
                        'title': source_metadata.get('title', ''),
                        'url': source_metadata.get('url', ''),
                        'authors': source_metadata.get('authors', []),
                        'date': self._extract_date(source_metadata),
                        'source_type': source_metadata.get('source_type', 'web')
                    })
                
                # Process insights
                for insight in data.get('author_insights', []):
                    citations.append({
                        'type': 'insight',
                        'content': insight.get('insight', ''),
                        'quote': insight.get('quote', ''),
                        'title': source_metadata.get('title', ''),
                        'url': source_metadata.get('url', ''),
                        'authors': source_metadata.get('authors', []),
                        'date': self._extract_date(source_metadata),
                        'source_type': source_metadata.get('source_type', 'web')
                    })
        
        except Exception as e:
            logger.warning(f"Failed to parse citation JSON: {str(e)}")
        
        # If no citations extracted, create basic citation
        if not citations:
            citations.append(self._create_basic_citation(source_metadata))
        
        return citations
    
    def _create_basic_citation(self, source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic citation from source metadata"""
        return {
            'type': 'source',
            'title': source_metadata.get('title', 'Unknown Source'),
            'url': source_metadata.get('url', ''),
            'authors': source_metadata.get('authors', []),
            'date': self._extract_date(source_metadata),
            'source_type': source_metadata.get('source_type', 'web'),
            'content': source_metadata.get('title', 'Unknown Source')
        }
    
    def _format_apa_citation(self, citation: Dict[str, Any]) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            if len(authors) == 1:
                parts.append(f"{authors[0]}")
            elif len(authors) <= 3:
                parts.append(", ".join(authors[:-1]) + f", & {authors[-1]}")
            else:
                parts.append(f"{authors[0]}, et al.")
        
        # Date
        date = citation.get('date', '')
        if date:
            parts.append(f"({date})")
        
        # Title
        title = citation.get('title', '')
        if title:
            if citation.get('source_type') == 'academic':
                parts.append(f"{title}.")
            else:
                parts.append(f"{title}.")
        
        # URL and access date
        url = citation.get('url', '')
        if url:
            parts.append(f"Retrieved from {url}")
        
        return " ".join(parts)
    
    def _format_mla_citation(self, citation: Dict[str, Any]) -> str:
        """Format citation in MLA style"""
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            parts.append(f"{authors[0]}.")
        
        # Title
        title = citation.get('title', '')
        if title:
            parts.append(f'"{title}."')
        
        # Web/Date
        url = citation.get('url', '')
        date = citation.get('date', '')
        
        if url:
            domain = urlparse(url).netloc
            parts.append(f"{domain},")
            
        if date:
            parts.append(f"{date}.")
        
        if url:
            parts.append(f"Web. {datetime.now().strftime('%d %b %Y')}.")
        
        return " ".join(parts)
    
    def _format_chicago_citation(self, citation: Dict[str, Any]) -> str:
        """Format citation in Chicago style"""
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            parts.append(f"{authors[0]}.")
        
        # Title
        title = citation.get('title', '')
        if title:
            parts.append(f'"{title}."')
        
        # URL and access date
        url = citation.get('url', '')
        if url:
            access_date = datetime.now().strftime('%B %d, %Y')
            parts.append(f"Accessed {access_date}. {url}.")
        
        return " ".join(parts)
    
    def _create_linking_prompt(self, content: str, citations: List[Dict[str, Any]]) -> str:
        """Create prompt for linking claims to citations"""
        citations_summary = "\n".join([
            f"[{i+1}] {cite.get('title', 'Unknown')}: {cite.get('content', '')[:100]}..."
            for i, cite in enumerate(citations[:10])
        ])
        
        return f"""
Add appropriate citation links to the following content using the available citations.

Content:
{content}

Available Citations:
{citations_summary}

Instructions:
- Add citation numbers in square brackets [1], [2], etc. after claims that need attribution
- Only cite claims that can be directly supported by the available sources
- Use the citation number that corresponds to the most relevant source
- Don't add citations to general statements or common knowledge
- Maintain the original content structure and flow

Return the content with citation links added:
"""

    def _deduplicate_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate citations"""
        seen_urls = set()
        seen_titles = set()
        unique_citations = []
        
        for citation in citations:
            url = citation.get('url', '')
            title = citation.get('title', '').lower()
            
            # Check for URL duplicates
            if url and url in seen_urls:
                continue
            
            # Check for title duplicates
            if title and title in seen_titles:
                continue
            
            if url:
                seen_urls.add(url)
            if title:
                seen_titles.add(title)
            
            unique_citations.append(citation)
        
        return unique_citations
    
    def _extract_date(self, source_metadata: Dict[str, Any]) -> str:
        """Extract and format date from source metadata"""
        # Try published date first
        if source_metadata.get('published'):
            return source_metadata['published'][:10]  # YYYY-MM-DD format
        
        # Try retrieved date
        if source_metadata.get('retrieved_at'):
            return source_metadata['retrieved_at'][:10]
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is valid"""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except:
            return False
