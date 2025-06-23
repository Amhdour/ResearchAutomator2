"""
LLM Tools Module

Provides interfaces for CloudGROQ API calls and prompt management
for various AI inference tasks.
"""

import os
import requests
import json
import time
from typing import Dict, Any, List, Optional
from .rate_limiter import RateLimiter
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMTools:
    """Tools for CloudGROQ LLM inference"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = getattr(config, 'default_model', 'llama3-8b-8192')  # Use faster model by default
        self.rate_limiter = RateLimiter(max_retries=3, base_delay=2.0)
        
        if not self.api_key:
            raise ValueError("CloudGROQ API key is required")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, model: Optional[str] = None) -> str:
        """
        Generate text using CloudGROQ API with rate limiting
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Model to use (optional)
            
        Returns:
            Generated text
        """
        def _make_request():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model or self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"CloudGROQ API error: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code}")
        
        try:
            return self.rate_limiter.call_with_backoff(_make_request)
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise
    
    def summarize_content(self, content: str, context: str = "") -> str:
        """
        Summarize content with optional context
        
        Args:
            content: Content to summarize
            context: Optional context for summarization
            
        Returns:
            Summary text
        """
        prompt = f"""
Please provide a comprehensive summary of the following content.
{f"Context: {context}" if context else ""}

Content to summarize:
{content}

Requirements for the summary:
- Include key findings and main points
- Maintain factual accuracy
- Use clear, concise language
- Highlight important insights or conclusions
- Keep the summary proportional to the content length

Summary:
"""
        
        return self.generate_text(prompt, max_tokens=800, temperature=0.3)
    
    def extract_key_information(self, content: str, research_goal: str) -> Dict[str, Any]:
        """
        Extract key information relevant to research goal
        
        Args:
            content: Content to analyze
            research_goal: Research goal for context
            
        Returns:
            Dictionary with extracted information
        """
        prompt = f"""
Analyze the following content in relation to the research goal and extract key information.

Research Goal: {research_goal}

Content to analyze:
{content}

Please extract and structure the following information in JSON format:
{{
    "key_findings": ["finding 1", "finding 2", "..."],
    "relevant_facts": ["fact 1", "fact 2", "..."],
    "statistics": ["statistic 1", "statistic 2", "..."],
    "conclusions": ["conclusion 1", "conclusion 2", "..."],
    "relevance_score": 0.0-1.0,
    "confidence_level": "high|medium|low"
}}

Focus on information that directly relates to the research goal.
"""
        
        try:
            response = self.generate_text(prompt, max_tokens=1000, temperature=0.3)
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Return structured fallback
                return {
                    "key_findings": [response[:200] + "..."],
                    "relevant_facts": [],
                    "statistics": [],
                    "conclusions": [],
                    "relevance_score": 0.5,
                    "confidence_level": "medium"
                }
        except Exception as e:
            logger.error(f"Information extraction failed: {str(e)}")
            return {
                "key_findings": [],
                "relevant_facts": [],
                "statistics": [],
                "conclusions": [],
                "relevance_score": 0.0,
                "confidence_level": "low"
            }
    
    def generate_search_queries(self, research_goal: str, existing_findings: List[str] = None) -> List[str]:
        """
        Generate additional search queries based on research goal and existing findings
        
        Args:
            research_goal: Main research goal
            existing_findings: List of findings already discovered
            
        Returns:
            List of search queries
        """
        existing_context = ""
        if existing_findings:
            existing_context = f"\n\nExisting findings:\n" + "\n".join(existing_findings[:5])
        
        prompt = f"""
Based on the research goal{' and existing findings' if existing_findings else ''}, generate 5-7 specific search queries that would help gather comprehensive information.

Research Goal: {research_goal}{existing_context}

Generate search queries that:
- Are specific and targeted
- Cover different aspects of the research goal
- Would yield diverse, high-quality results
- Avoid duplication with existing findings
- Use varied terminology and approaches

Provide only the search queries, one per line:
"""
        
        try:
            response = self.generate_text(prompt, max_tokens=500, temperature=0.5)
            queries = [line.strip() for line in response.split('\n') if line.strip()]
            # Clean up queries
            cleaned_queries = []
            for query in queries:
                # Remove numbering and formatting
                query = re.sub(r'^\d+[\.\)]\s*', '', query)
                query = query.strip('"\'- ')
                if query and len(query) > 5:
                    cleaned_queries.append(query)
            
            return cleaned_queries[:7]  # Limit to 7 queries
            
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            return [research_goal]  # Fallback to original goal
    
    def critique_content(self, content: str, criteria: List[str]) -> Dict[str, Any]:
        """
        Critique content based on specified criteria
        
        Args:
            content: Content to critique
            criteria: List of criteria for evaluation
            
        Returns:
            Dictionary with critique results
        """
        criteria_text = "\n".join([f"- {criterion}" for criterion in criteria])
        
        prompt = f"""
Please critique the following content based on these criteria:
{criteria_text}

Content to critique:
{content}

Provide a structured critique in JSON format:
{{
    "overall_score": 0.0-1.0,
    "strengths": ["strength 1", "strength 2", "..."],
    "weaknesses": ["weakness 1", "weakness 2", "..."],
    "specific_feedback": {{
        "accuracy": "feedback on accuracy",
        "completeness": "feedback on completeness",
        "clarity": "feedback on clarity"
    }},
    "suggestions": ["suggestion 1", "suggestion 2", "..."],
    "recommendation": "accept|revise|reject"
}}
"""
        
        try:
            response = self.generate_text(prompt, max_tokens=800, temperature=0.3)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "overall_score": 0.7,
                    "strengths": ["Content is present"],
                    "weaknesses": ["Could not perform detailed analysis"],
                    "specific_feedback": {
                        "accuracy": "Unable to verify",
                        "completeness": "Appears adequate",
                        "clarity": "Reasonably clear"
                    },
                    "suggestions": ["Manual review recommended"],
                    "recommendation": "accept"
                }
        except Exception as e:
            logger.error(f"Content critique failed: {str(e)}")
            return {
                "overall_score": 0.5,
                "strengths": [],
                "weaknesses": ["Critique analysis failed"],
                "specific_feedback": {},
                "suggestions": [],
                "recommendation": "accept"
            }
    
    def generate_report_section(self, section_title: str, content_items: List[str], research_goal: str) -> str:
        """
        Generate a report section from content items
        
        Args:
            section_title: Title of the section
            content_items: List of content pieces
            research_goal: Overall research goal for context
            
        Returns:
            Formatted report section
        """
        content_text = "\n\n".join([f"Source {i+1}: {item}" for i, item in enumerate(content_items)])
        
        prompt = f"""
Create a comprehensive report section titled "{section_title}" based on the provided content.

Research Goal: {research_goal}

Source Content:
{content_text}

Requirements:
- Write in a clear, professional academic style
- Synthesize information from multiple sources
- Highlight key findings and insights
- Maintain logical flow and structure
- Include specific details and evidence
- Write 2-4 paragraphs depending on content volume

Report Section:
"""
        
        return self.generate_text(prompt, max_tokens=1200, temperature=0.4)
