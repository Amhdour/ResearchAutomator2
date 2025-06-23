"""
Emergency Mode Module

Provides research capabilities when API limits are reached using local processing.
"""

import re
import requests
from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class EmergencyMode:
    """Provides basic research functionality without LLM when rate limited"""
    
    def __init__(self, config):
        self.config = config
        
    def extract_key_information(self, content: str, source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information using simple text processing"""
        
        # Clean content
        content = self._clean_text(content)
        sentences = self._split_into_sentences(content)
        
        # Extract different types of information
        key_findings = self._extract_key_findings(sentences)
        statistics = self._extract_statistics(sentences)
        conclusions = self._extract_conclusions(sentences)
        
        return {
            'source_title': source_metadata.get('title', 'Unknown Source'),
            'source_url': source_metadata.get('url', ''),
            'source_type': source_metadata.get('type', 'web'),
            'key_findings': key_findings[:3],  # Limit to top 3
            'relevant_facts': sentences[:5],   # First 5 sentences as facts
            'statistics': statistics[:2],
            'conclusions': conclusions[:2],
            'confidence_level': 'basic',
            'relevance_score': 0.6,
            'emergency_extraction': True
        }
    
    def create_basic_citations(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create basic citations without LLM processing"""
        citations = []
        
        for source in sources:
            if source.get('title') and source.get('url'):
                citation = {
                    'type': 'source',
                    'title': source['title'],
                    'url': source['url'],
                    'authors': source.get('authors', ['Unknown']),
                    'date': source.get('published', 'n.d.'),
                    'source_type': source.get('type', 'web'),
                    'content': f"Retrieved from {source['title']}",
                    'context': 'Academic source',
                    'emergency_citation': True
                }
                citations.append(citation)
        
        return citations
    
    def generate_emergency_report(self, research_goal: str, findings: List[Dict[str, Any]]) -> str:
        """Generate a basic report without LLM when rate limited"""
        
        report_sections = []
        
        # Header
        report_sections.append(f"# Research Report: {research_goal}")
        report_sections.append("*Note: This report was generated in emergency mode with limited AI processing*\n")
        
        # Executive Summary
        report_sections.append("## Executive Summary")
        report_sections.append(f"Research conducted on: {research_goal}")
        report_sections.append(f"Sources analyzed: {len(findings)}")
        report_sections.append("Key findings extracted using automated text processing.\n")
        
        # Key Findings
        if findings:
            report_sections.append("## Key Findings")
            for i, finding in enumerate(findings[:5], 1):
                report_sections.append(f"### Finding {i}: {finding.get('source_title', 'Unknown')}")
                
                key_points = finding.get('key_findings', [])
                if key_points:
                    for point in key_points[:2]:
                        report_sections.append(f"- {point}")
                
                report_sections.append(f"Source: {finding.get('source_url', 'N/A')}\n")
        
        # Sources
        report_sections.append("## Sources")
        for i, finding in enumerate(findings, 1):
            title = finding.get('source_title', 'Unknown Source')
            url = finding.get('source_url', 'N/A')
            report_sections.append(f"{i}. {title} - {url}")
        
        return "\n".join(report_sections)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _extract_key_findings(self, sentences: List[str]) -> List[str]:
        """Extract sentences that likely contain key findings"""
        key_indicators = [
            'found that', 'discovered', 'revealed', 'showed', 'demonstrated',
            'indicates', 'suggests', 'evidence', 'research shows', 'study found'
        ]
        
        findings = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                findings.append(sentence)
                if len(findings) >= 5:
                    break
        
        return findings
    
    def _extract_statistics(self, sentences: List[str]) -> List[str]:
        """Extract sentences containing statistical information"""
        statistics = []
        
        for sentence in sentences:
            # Look for numbers with percent signs or numerical patterns
            if re.search(r'\d+\.?\d*\s*%|\d+\.?\d*\s*(percent|million|billion|thousand)', sentence.lower()):
                statistics.append(sentence)
                if len(statistics) >= 3:
                    break
        
        return statistics
    
    def _extract_conclusions(self, sentences: List[str]) -> List[str]:
        """Extract sentences that likely contain conclusions"""
        conclusion_indicators = [
            'conclude', 'in conclusion', 'therefore', 'thus', 'hence',
            'in summary', 'overall', 'finally', 'results show'
        ]
        
        conclusions = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in conclusion_indicators):
                conclusions.append(sentence)
                if len(conclusions) >= 3:
                    break
        
        return conclusions