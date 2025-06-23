"""
Self-Critique Module

Provides quality assurance and iterative improvement capabilities
by critiquing research outputs and suggesting improvements.
"""

from typing import Dict, List, Any, Optional
from .llm_tools import LLMTools
from utils.logger import get_logger

logger = get_logger(__name__)

class SelfCritique:
    """Self-critique and quality assurance for research outputs"""
    
    def __init__(self, config):
        self.config = config
        self.llm_tools = LLMTools(config)
        
        # Quality criteria for different types of content
        self.quality_criteria = {
            'research_findings': [
                'Factual accuracy and verifiability',
                'Relevance to research goal',
                'Source credibility and authority',
                'Completeness of information',
                'Clear presentation and organization'
            ],
            'citations': [
                'Proper attribution and formatting',
                'Source accessibility and reliability',
                'Appropriate citation style compliance',
                'Complete bibliographic information'
            ],
            'synthesis': [
                'Logical flow and coherence',
                'Comprehensive coverage of findings',
                'Clear conclusions and insights',
                'Balanced perspective and objectivity',
                'Appropriate depth and detail'
            ]
        }
    
    def critique_phase_results(self, phase_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique the results of a single research phase
        
        Args:
            phase_data: Dictionary containing phase results
            
        Returns:
            Critique results with scores and recommendations
        """
        logger.info(f"Critiquing phase: {phase_data.get('phase', {}).get('title', 'Unknown')}")
        
        try:
            # Prepare critique content
            phase = phase_data.get('phase', {})
            findings = phase_data.get('findings', [])
            summary = phase_data.get('summary', '')
            
            # Create critique prompt
            critique_prompt = self._create_phase_critique_prompt(phase, findings, summary)
            
            # Get critique from LLM
            critique_response = self.llm_tools.critique_content(
                content=summary,
                criteria=self.quality_criteria['research_findings']
            )
            
            # Analyze findings quality
            findings_quality = self._analyze_findings_quality(findings)
            
            # Combine critiques
            overall_critique = self._combine_phase_critiques(critique_response, findings_quality)
            
            logger.info(f"Phase critique completed with score: {overall_critique.get('overall_score', 0):.2f}")
            return overall_critique
            
        except Exception as e:
            logger.error(f"Phase critique failed: {str(e)}")
            return self._create_fallback_critique()
    
    def critique_research_synthesis(self, synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique the overall research synthesis
        
        Args:
            synthesis_data: Dictionary containing synthesis results
            
        Returns:
            Critique results for the synthesis
        """
        logger.info("Critiquing research synthesis")
        
        try:
            synthesis_text = synthesis_data.get('summary', '')
            key_conclusions = synthesis_data.get('key_conclusions', [])
            
            # Critique the synthesis content
            synthesis_critique = self.llm_tools.critique_content(
                content=synthesis_text,
                criteria=self.quality_criteria['synthesis']
            )
            
            # Evaluate conclusion quality
            conclusion_quality = self._evaluate_conclusions(key_conclusions)
            
            # Check for research gaps
            gap_analysis = self._identify_research_gaps(synthesis_data)
            
            return {
                'synthesis_critique': synthesis_critique,
                'conclusion_quality': conclusion_quality,
                'gap_analysis': gap_analysis,
                'overall_score': self._calculate_synthesis_score(synthesis_critique, conclusion_quality),
                'recommendations': self._generate_synthesis_recommendations(synthesis_critique, gap_analysis)
            }
            
        except Exception as e:
            logger.error(f"Synthesis critique failed: {str(e)}")
            return self._create_fallback_critique()
    
    def final_quality_review(self, research_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct comprehensive final quality review
        
        Args:
            research_content: All research content and results
            
        Returns:
            Comprehensive quality assessment
        """
        logger.info("Conducting final quality review")
        
        try:
            # Review different aspects
            content_quality = self._review_content_quality(research_content)
            citation_quality = self._review_citation_quality(research_content.get('citations', []))
            coverage_assessment = self._assess_research_coverage(research_content)
            methodology_review = self._review_methodology(research_content)
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_quality_score(
                content_quality,
                citation_quality,
                coverage_assessment,
                methodology_review
            )
            
            # Generate final recommendations
            final_recommendations = self._generate_final_recommendations(
                content_quality,
                citation_quality,
                coverage_assessment,
                methodology_review
            )
            
            return {
                'overall_score': overall_score,
                'content_quality': content_quality,
                'citation_quality': citation_quality,
                'coverage_assessment': coverage_assessment,
                'methodology_review': methodology_review,
                'final_recommendations': final_recommendations,
                'quality_grade': self._assign_quality_grade(overall_score),
                'approval_status': 'approved' if overall_score >= 0.7 else 'needs_revision'
            }
            
        except Exception as e:
            logger.error(f"Final quality review failed: {str(e)}")
            return {
                'overall_score': 0.5,
                'quality_grade': 'C',
                'approval_status': 'needs_revision',
                'error': str(e)
            }
    
    def suggest_improvements(self, critique_results: Dict[str, Any]) -> List[str]:
        """
        Generate specific improvement suggestions based on critique
        
        Args:
            critique_results: Results from quality critique
            
        Returns:
            List of specific improvement suggestions
        """
        suggestions = []
        
        # Extract suggestions from critique results
        if 'suggestions' in critique_results:
            suggestions.extend(critique_results['suggestions'])
        
        # Add suggestions based on scores
        overall_score = critique_results.get('overall_score', 0)
        
        if overall_score < 0.6:
            suggestions.append("Consider expanding research scope to include more diverse sources")
            suggestions.append("Verify factual claims with additional authoritative sources")
        
        if overall_score < 0.7:
            suggestions.append("Improve organization and clarity of findings presentation")
            suggestions.append("Strengthen connections between different research findings")
        
        # Add specific suggestions based on weaknesses
        weaknesses = critique_results.get('weaknesses', [])
        for weakness in weaknesses:
            if 'accuracy' in weakness.lower():
                suggestions.append("Fact-check key claims against primary sources")
            elif 'completeness' in weakness.lower():
                suggestions.append("Conduct additional research to fill identified gaps")
            elif 'clarity' in weakness.lower():
                suggestions.append("Reorganize content for better logical flow")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _create_phase_critique_prompt(self, phase: Dict[str, Any], findings: List[Dict[str, Any]], summary: str) -> str:
        """Create critique prompt for phase results"""
        findings_summary = "\n".join([
            f"- {finding.get('source_title', 'Unknown')}: {len(finding.get('key_findings', []))} findings"
            for finding in findings[:5]
        ])
        
        return f"""
Critique the following research phase results:

Phase: {phase.get('title', 'Unknown')}
Goal: {phase.get('description', 'No description')}

Findings Summary:
{findings_summary}

Phase Summary:
{summary}

Evaluate based on:
1. Relevance to phase objectives
2. Quality and diversity of sources
3. Depth of analysis
4. Clarity of presentation
5. Completeness of coverage

Provide specific feedback on strengths, weaknesses, and areas for improvement.
"""

    def _analyze_findings_quality(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality of research findings"""
        if not findings:
            return {'score': 0.0, 'issues': ['No findings to analyze']}
        
        total_score = 0.0
        issues = []
        strengths = []
        
        # Analyze relevance scores
        relevance_scores = [f.get('relevance_score', 0) for f in findings]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        if avg_relevance < 0.5:
            issues.append("Low average relevance of findings to research goal")
        else:
            strengths.append("Good relevance alignment with research objectives")
        
        total_score += avg_relevance * 0.4
        
        # Analyze source diversity
        unique_sources = len(set(f.get('source_title', '') for f in findings))
        source_diversity_score = min(1.0, unique_sources / max(1, len(findings)))
        
        if source_diversity_score < 0.7:
            issues.append("Limited source diversity")
        else:
            strengths.append("Good diversity of information sources")
        
        total_score += source_diversity_score * 0.3
        
        # Analyze content richness
        avg_findings_per_source = sum(len(f.get('key_findings', [])) for f in findings) / len(findings)
        content_richness = min(1.0, avg_findings_per_source / 3.0)  # Expect ~3 findings per source
        
        if content_richness < 0.5:
            issues.append("Sparse content extraction from sources")
        else:
            strengths.append("Rich content extraction and analysis")
        
        total_score += content_richness * 0.3
        
        return {
            'score': total_score,
            'avg_relevance': avg_relevance,
            'source_diversity': source_diversity_score,
            'content_richness': content_richness,
            'issues': issues,
            'strengths': strengths
        }
    
    def _combine_phase_critiques(self, llm_critique: Dict[str, Any], findings_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine LLM critique with findings analysis"""
        # Weight the scores
        llm_score = llm_critique.get('overall_score', 0.5)
        findings_score = findings_analysis.get('score', 0.5)
        
        combined_score = (llm_score * 0.6) + (findings_score * 0.4)
        
        # Combine strengths and weaknesses
        strengths = llm_critique.get('strengths', []) + findings_analysis.get('strengths', [])
        weaknesses = llm_critique.get('weaknesses', []) + findings_analysis.get('issues', [])
        
        return {
            'overall_score': combined_score,
            'llm_critique_score': llm_score,
            'findings_analysis_score': findings_score,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': llm_critique.get('suggestions', []),
            'detailed_analysis': findings_analysis
        }
    
    def _evaluate_conclusions(self, conclusions: List[str]) -> Dict[str, Any]:
        """Evaluate the quality of research conclusions"""
        if not conclusions:
            return {'score': 0.0, 'issues': ['No conclusions provided']}
        
        # Simple evaluation based on conclusion characteristics
        score = 0.0
        issues = []
        strengths = []
        
        # Check number of conclusions
        if len(conclusions) < 3:
            issues.append("Insufficient number of conclusions")
            score += 0.3
        elif len(conclusions) > 10:
            issues.append("Too many conclusions - may indicate lack of synthesis")
            score += 0.6
        else:
            strengths.append("Appropriate number of conclusions")
            score += 0.8
        
        # Check conclusion length and detail
        avg_length = sum(len(c) for c in conclusions) / len(conclusions)
        if avg_length < 50:
            issues.append("Conclusions appear too brief or superficial")
        elif avg_length > 200:
            issues.append("Conclusions may be too verbose")
        else:
            strengths.append("Well-sized conclusions with appropriate detail")
            score += 0.2
        
        return {
            'score': min(1.0, score),
            'conclusion_count': len(conclusions),
            'avg_length': avg_length,
            'issues': issues,
            'strengths': strengths
        }
    
    def _identify_research_gaps(self, synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify potential gaps in research coverage"""
        gaps = []
        suggestions = []
        
        # Check thematic coverage
        thematic_groups = synthesis_data.get('thematic_groups', {})
        if len(thematic_groups) < 3:
            gaps.append("Limited thematic diversity in research")
            suggestions.append("Explore additional aspects or angles of the research topic")
        
        # Check source types
        findings = synthesis_data.get('findings', [])
        if findings:
            source_types = set()
            for finding in findings:
                # This would need to be extracted from source metadata
                source_types.add('web')  # Placeholder
            
            if len(source_types) < 2:
                gaps.append("Limited diversity in source types")
                suggestions.append("Include academic papers, reports, and other source types")
        
        return {
            'identified_gaps': gaps,
            'gap_count': len(gaps),
            'suggestions': suggestions,
            'coverage_score': max(0.0, 1.0 - len(gaps) * 0.2)
        }
    
    def _calculate_synthesis_score(self, synthesis_critique: Dict[str, Any], conclusion_quality: Dict[str, Any]) -> float:
        """Calculate overall synthesis quality score"""
        synthesis_score = synthesis_critique.get('overall_score', 0.5)
        conclusion_score = conclusion_quality.get('score', 0.5)
        
        return (synthesis_score * 0.7) + (conclusion_score * 0.3)
    
    def _generate_synthesis_recommendations(self, synthesis_critique: Dict[str, Any], gap_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for synthesis improvement"""
        recommendations = []
        
        # Add synthesis-specific recommendations
        recommendations.extend(synthesis_critique.get('suggestions', []))
        
        # Add gap-filling recommendations
        recommendations.extend(gap_analysis.get('suggestions', []))
        
        return recommendations
    
    def _review_content_quality(self, research_content: Dict[str, Any]) -> Dict[str, Any]:
        """Review overall content quality"""
        findings = research_content.get('findings', [])
        
        if not findings:
            return {'score': 0.0, 'issues': ['No research findings available']}
        
        # Analyze content metrics
        total_findings = len(findings)
        unique_sources = len(set(f.get('source_title', '') for f in findings))
        avg_relevance = sum(f.get('relevance_score', 0) for f in findings) / total_findings
        
        # Calculate content quality score
        quantity_score = min(1.0, total_findings / 20.0)  # Expect ~20 findings for good coverage
        diversity_score = min(1.0, unique_sources / 10.0)  # Expect ~10 unique sources
        relevance_score = avg_relevance
        
        overall_score = (quantity_score * 0.3) + (diversity_score * 0.3) + (relevance_score * 0.4)
        
        return {
            'score': overall_score,
            'total_findings': total_findings,
            'unique_sources': unique_sources,
            'avg_relevance': avg_relevance,
            'quantity_score': quantity_score,
            'diversity_score': diversity_score,
            'relevance_score': relevance_score
        }
    
    def _review_citation_quality(self, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review citation quality"""
        if not citations:
            return {'score': 0.0, 'issues': ['No citations provided']}
        
        total_score = 0.0
        issues = []
        
        for citation in citations:
            # Check for required fields
            if citation.get('title') and citation.get('url'):
                total_score += 1.0
            else:
                issues.append(f"Incomplete citation: {citation.get('title', 'Unknown')}")
        
        citation_score = total_score / len(citations) if citations else 0.0
        
        return {
            'score': citation_score,
            'total_citations': len(citations),
            'complete_citations': int(total_score),
            'issues': issues
        }
    
    def _assess_research_coverage(self, research_content: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well the research covers the stated goal"""
        goal = research_content.get('goal', '')
        findings = research_content.get('findings', [])
        
        if not goal or not findings:
            return {'score': 0.0, 'issues': ['Insufficient data for coverage assessment']}
        
        # Simple coverage assessment based on findings relevance
        high_relevance_count = sum(1 for f in findings if f.get('relevance_score', 0) > 0.7)
        coverage_score = min(1.0, high_relevance_count / max(1, len(findings)))
        
        return {
            'score': coverage_score,
            'high_relevance_findings': high_relevance_count,
            'total_findings': len(findings),
            'coverage_percentage': coverage_score * 100
        }
    
    def _review_methodology(self, research_content: Dict[str, Any]) -> Dict[str, Any]:
        """Review research methodology quality"""
        phases_completed = research_content.get('phases_completed', 0)
        
        # Basic methodology review
        methodology_score = min(1.0, phases_completed / 5.0)  # Expect ~5 phases for thorough research
        
        return {
            'score': methodology_score,
            'phases_completed': phases_completed,
            'methodology_assessment': 'systematic' if phases_completed >= 3 else 'basic'
        }
    
    def _calculate_overall_quality_score(self, content_quality: Dict[str, Any], citation_quality: Dict[str, Any], 
                                       coverage_assessment: Dict[str, Any], methodology_review: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        content_score = content_quality.get('score', 0.0)
        citation_score = citation_quality.get('score', 0.0)
        coverage_score = coverage_assessment.get('score', 0.0)
        methodology_score = methodology_review.get('score', 0.0)
        
        # Weighted average
        overall_score = (content_score * 0.4) + (citation_score * 0.2) + (coverage_score * 0.3) + (methodology_score * 0.1)
        
        return overall_score
    
    def _generate_final_recommendations(self, content_quality: Dict[str, Any], citation_quality: Dict[str, Any],
                                      coverage_assessment: Dict[str, Any], methodology_review: Dict[str, Any]) -> List[str]:
        """Generate final improvement recommendations"""
        recommendations = []
        
        if content_quality.get('score', 0) < 0.7:
            recommendations.append("Expand research scope to include more diverse and comprehensive sources")
        
        if citation_quality.get('score', 0) < 0.8:
            recommendations.append("Improve citation completeness and formatting")
        
        if coverage_assessment.get('score', 0) < 0.6:
            recommendations.append("Address research gaps to better cover the stated research goal")
        
        if methodology_review.get('score', 0) < 0.7:
            recommendations.append("Follow a more systematic research methodology with additional phases")
        
        return recommendations
    
    def _assign_quality_grade(self, score: float) -> str:
        """Assign letter grade based on quality score"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _create_fallback_critique(self) -> Dict[str, Any]:
        """Create fallback critique when analysis fails"""
        return {
            'overall_score': 0.5,
            'strengths': ['Research attempt completed'],
            'weaknesses': ['Unable to perform detailed quality analysis'],
            'recommendations': ['Manual review recommended'],
            'quality_grade': 'C',
            'approval_status': 'needs_review'
        }
