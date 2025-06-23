"""
Report Compiler Module

Compiles comprehensive research reports from findings, citations, and analysis.
Formats reports in Markdown with proper citation integration.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from .llm_tools import LLMTools
from .citation_engine import CitationEngine
from utils.logger import get_logger

logger = get_logger(__name__)

class ReportCompiler:
    """Compile comprehensive research reports from research results"""
    
    def __init__(self, config):
        self.config = config
        self.llm_tools = LLMTools(config)
        self.citation_engine = CitationEngine(config)
    
    def compile_report(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile a comprehensive research report from all results
        
        Args:
            research_results: Complete research execution results
            
        Returns:
            Compiled report with formatted content and metadata
        """
        logger.info("Compiling comprehensive research report")
        
        try:
            start_time = datetime.now()
            
            # Extract key components
            research_goal = research_results.get('research_goal', '')
            findings = research_results.get('findings', [])
            citations = research_results.get('citations', [])
            synthesis = research_results.get('synthesis', {})
            quality_check = research_results.get('quality_check', {})
            execution_plan = research_results.get('execution_plan', {})
            
            # Generate report sections
            executive_summary = self._generate_executive_summary(research_goal, synthesis, quality_check)
            methodology_section = self._generate_methodology_section(execution_plan, research_results)
            findings_section = self._generate_findings_section(findings, synthesis)
            analysis_section = self._generate_analysis_section(synthesis, findings)
            conclusions_section = self._generate_conclusions_section(synthesis, quality_check)
            bibliography = self.citation_engine.create_bibliography(citations)
            appendices = self._generate_appendices(research_results)
            
            # Compile full report
            report_content = self._assemble_report(
                research_goal,
                executive_summary,
                methodology_section,
                findings_section,
                analysis_section,
                conclusions_section,
                bibliography,
                appendices
            )
            
            # Add citation links to content
            report_content = self.citation_engine.link_claims_to_sources(report_content, citations)
            
            # Generate report metadata
            compilation_time = datetime.now()
            duration = (compilation_time - start_time).total_seconds()
            
            metadata = self._generate_report_metadata(
                research_results,
                start_time,
                compilation_time,
                duration
            )
            
            compiled_report = {
                'content': report_content,
                'metadata': metadata,
                'source_count': len(set(f.get('source_title', '') for f in findings)),
                'citation_count': len(citations),
                'duration': f"{duration:.1f}s",
                'quality_grade': quality_check.get('quality_grade', 'C'),
                'compilation_timestamp': compilation_time.isoformat(),
                'sections': {
                    'executive_summary': executive_summary,
                    'methodology': methodology_section,
                    'findings': findings_section,
                    'analysis': analysis_section,
                    'conclusions': conclusions_section,
                    'bibliography': bibliography,
                    'appendices': appendices
                }
            }
            
            logger.info(f"Report compilation completed in {duration:.1f} seconds")
            return compiled_report
            
        except Exception as e:
            logger.error(f"Report compilation failed: {str(e)}")
            return self._create_fallback_report(research_results)
    
    def export_report(self, compiled_report: Dict[str, Any], format_type: str = 'markdown') -> str:
        """
        Export report in specified format
        
        Args:
            compiled_report: Compiled report data
            format_type: Export format ('markdown', 'html', 'json')
            
        Returns:
            Formatted report string
        """
        if format_type == 'markdown':
            return compiled_report.get('content', '')
        elif format_type == 'html':
            return self._convert_to_html(compiled_report.get('content', ''))
        elif format_type == 'json':
            return json.dumps(compiled_report, indent=2, default=str)
        else:
            return compiled_report.get('content', '')
    
    def _generate_executive_summary(self, research_goal: str, synthesis: Dict[str, Any], quality_check: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        try:
            summary_prompt = f"""
Create an executive summary for a research report with the following information:

Research Goal: {research_goal}

Key Findings Summary: {synthesis.get('summary', 'No synthesis available')[:500]}

Research Quality: {quality_check.get('quality_grade', 'Unknown')} grade

Total Sources: {synthesis.get('unique_sources', 0)}

Create a professional executive summary (2-3 paragraphs) that:
- Clearly states the research objective
- Highlights the most important findings
- Provides key insights and conclusions
- Mentions the scope and quality of research conducted
- Is accessible to both technical and non-technical audiences

Executive Summary:
"""
            
            return self.llm_tools.generate_text(
                prompt=summary_prompt,
                max_tokens=800,
                temperature=0.3
            )
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {str(e)}")
            return f"""
## Executive Summary

This report presents research findings on: {research_goal}

The research was conducted using an autonomous research agent that analyzed {synthesis.get('unique_sources', 0)} sources and compiled {synthesis.get('total_findings', 0)} key findings. The research achieved a quality grade of {quality_check.get('quality_grade', 'Unknown')}.

Key findings and conclusions are presented in the following sections with full citations and analysis.
"""
    
    def _generate_methodology_section(self, execution_plan: Dict[str, Any], research_results: Dict[str, Any]) -> str:
        """Generate methodology section"""
        phases = execution_plan.get('phases', [])
        phase_results = research_results.get('phase_results', [])
        execution_time = research_results.get('execution_time', 0)
        
        methodology = f"""
## Research Methodology

### Approach
This research was conducted using an autonomous research agent following a systematic, multi-phase approach. The research strategy was: {execution_plan.get('strategy', 'Sequential research and analysis')}.

### Research Phases
The research was executed in {len(phases)} planned phases:

"""
        
        for i, phase in enumerate(phases, 1):
            phase_result = next((pr for pr in phase_results if pr.get('phase_id') == phase.get('id')), {})
            docs_retrieved = phase_result.get('documents_retrieved', 0)
            
            methodology += f"""
**Phase {i}: {phase.get('title', 'Unknown Phase')}**
- Objective: {phase.get('description', 'No description available')}
- Search Terms: {', '.join(phase.get('search_terms', []))}
- Sources Targeted: {', '.join(phase.get('expected_sources', []))}
- Documents Retrieved: {docs_retrieved}
- Status: {'Completed' if phase_result.get('success') else 'Failed'}

"""
        
        methodology += f"""
### Quality Assurance
- Self-critique and validation at each phase
- Source credibility assessment
- Citation verification and formatting
- Final quality review with overall score

### Research Duration
Total execution time: {execution_time:.1f} seconds

### Limitations
- Research conducted using automated web search and document retrieval
- Quality dependent on source availability and accessibility
- Analysis performed using AI inference with CloudGROQ
"""
        
        return methodology
    
    def _generate_findings_section(self, findings: List[Dict[str, Any]], synthesis: Dict[str, Any]) -> str:
        """Generate detailed findings section"""
        if not findings:
            return "## Key Findings\n\nNo significant findings were identified during the research process."
        
        try:
            # Group findings by source or theme
            findings_by_source = {}
            for finding in findings:
                source = finding.get('source_title', 'Unknown Source')
                if source not in findings_by_source:
                    findings_by_source[source] = []
                findings_by_source[source].append(finding)
            
            findings_section = "## Key Findings\n\n"
            
            # Add summary of findings
            findings_section += f"The research identified {len(findings)} key findings from {len(findings_by_source)} unique sources. "
            findings_section += f"These findings provide comprehensive coverage of the research topic with an average relevance score of {self._calculate_average_relevance(findings):.2f}.\n\n"
            
            # Add thematic groupings if available
            thematic_groups = synthesis.get('thematic_groups', {})
            if thematic_groups:
                findings_section += "### Key Themes Identified\n\n"
                for theme, theme_findings in list(thematic_groups.items())[:5]:  # Top 5 themes
                    findings_section += f"**{theme.title()}**: {len(theme_findings)} related findings\n"
                findings_section += "\n"
            
            # Add top findings
            findings_section += "### Most Significant Findings\n\n"
            
            # Sort findings by relevance
            sorted_findings = sorted(findings, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            for i, finding in enumerate(sorted_findings[:10], 1):  # Top 10 findings
                source_title = finding.get('source_title', 'Unknown Source')
                key_findings = finding.get('key_findings', [])
                relevant_facts = finding.get('relevant_facts', [])
                statistics = finding.get('statistics', [])
                
                findings_section += f"**Finding {i}: {source_title}**\n\n"
                
                if key_findings:
                    findings_section += "Key Points:\n"
                    for point in key_findings[:3]:  # Top 3 points
                        findings_section += f"- {point}\n"
                    findings_section += "\n"
                
                if relevant_facts:
                    findings_section += "Supporting Facts:\n"
                    for fact in relevant_facts[:2]:  # Top 2 facts
                        findings_section += f"- {fact}\n"
                    findings_section += "\n"
                
                if statistics:
                    findings_section += "Statistics:\n"
                    for stat in statistics[:2]:  # Top 2 statistics
                        findings_section += f"- {stat}\n"
                    findings_section += "\n"
                
                findings_section += f"*Relevance Score: {finding.get('relevance_score', 0):.2f}*\n\n"
            
            return findings_section
            
        except Exception as e:
            logger.error(f"Failed to generate findings section: {str(e)}")
            return f"## Key Findings\n\nResearch identified {len(findings)} findings from multiple sources. Detailed analysis available in raw data."
    
    def _generate_analysis_section(self, synthesis: Dict[str, Any], findings: List[Dict[str, Any]]) -> str:
        """Generate analysis and discussion section"""
        try:
            analysis_prompt = f"""
Create a comprehensive analysis section for a research report based on the following information:

Research Summary: {synthesis.get('summary', 'No synthesis available')}

Key Conclusions: {'; '.join(synthesis.get('key_conclusions', [])[:5])}

Total Findings: {len(findings)}
Unique Sources: {synthesis.get('unique_sources', 0)}

Create an analysis section that:
- Discusses patterns and trends identified in the research
- Compares and contrasts different findings
- Identifies areas of agreement and disagreement among sources
- Discusses implications of the findings
- Notes any limitations or gaps in the research
- Provides context for understanding the results

Write in a scholarly tone with clear section headers.

Analysis:
"""
            
            analysis_content = self.llm_tools.generate_text(
                prompt=analysis_prompt,
                max_tokens=1500,
                temperature=0.4
            )
            
            return f"## Analysis and Discussion\n\n{analysis_content}"
            
        except Exception as e:
            logger.error(f"Failed to generate analysis section: {str(e)}")
            return f"""
## Analysis and Discussion

### Overview
The research analysis reveals several key patterns and insights from {len(findings)} findings across {synthesis.get('unique_sources', 0)} sources.

### Key Patterns
{synthesis.get('summary', 'Analysis synthesis not available.')}

### Implications
The findings suggest important implications for understanding the research topic and may inform future research directions.

### Limitations
This analysis is based on automated research and may benefit from additional expert review and validation.
"""
    
    def _generate_conclusions_section(self, synthesis: Dict[str, Any], quality_check: Dict[str, Any]) -> str:
        """Generate conclusions and recommendations section"""
        key_conclusions = synthesis.get('key_conclusions', [])
        
        conclusions_section = "## Conclusions and Recommendations\n\n"
        
        if key_conclusions:
            conclusions_section += "### Primary Conclusions\n\n"
            for i, conclusion in enumerate(key_conclusions[:7], 1):  # Top 7 conclusions
                conclusions_section += f"{i}. {conclusion}\n\n"
        
        # Add quality assessment
        quality_score = quality_check.get('overall_score', 0)
        quality_grade = quality_check.get('quality_grade', 'Unknown')
        
        conclusions_section += f"""
### Research Quality Assessment
This research achieved an overall quality score of {quality_score:.2f} (Grade: {quality_grade}).

Quality Breakdown:
- Content Quality: {quality_check.get('content_quality', {}).get('score', 0):.2f}
- Citation Quality: {quality_check.get('citation_quality', {}).get('score', 0):.2f}
- Coverage Assessment: {quality_check.get('coverage_assessment', {}).get('score', 0):.2f}
- Methodology: {quality_check.get('methodology_review', {}).get('score', 0):.2f}

"""
        
        # Add recommendations if available
        recommendations = quality_check.get('final_recommendations', [])
        if recommendations:
            conclusions_section += "### Recommendations for Future Research\n\n"
            for i, rec in enumerate(recommendations, 1):
                conclusions_section += f"{i}. {rec}\n\n"
        
        return conclusions_section
    
    def _generate_appendices(self, research_results: Dict[str, Any]) -> str:
        """Generate appendices with supplementary information"""
        appendices = "## Appendices\n\n"
        
        # Appendix A: Research Plan
        execution_plan = research_results.get('execution_plan', {})
        appendices += "### Appendix A: Research Execution Plan\n\n"
        appendices += f"**Plan ID**: {execution_plan.get('plan_id', 'Unknown')}\n\n"
        appendices += f"**Strategy**: {execution_plan.get('strategy', 'Not specified')}\n\n"
        appendices += f"**Total Phases**: {len(execution_plan.get('phases', []))}\n\n"
        
        # Appendix B: Source Summary
        findings = research_results.get('findings', [])
        unique_sources = set(f.get('source_title', '') for f in findings)
        
        appendices += "### Appendix B: Source Summary\n\n"
        appendices += f"**Total Sources Analyzed**: {len(unique_sources)}\n\n"
        
        if unique_sources:
            appendices += "**Source List**:\n"
            for i, source in enumerate(sorted(unique_sources)[:20], 1):  # Top 20 sources
                appendices += f"{i}. {source}\n"
            appendices += "\n"
        
        # Appendix C: Research Statistics
        appendices += "### Appendix C: Research Statistics\n\n"
        appendices += f"- Total Research Findings: {len(findings)}\n"
        appendices += f"- Total Citations: {len(research_results.get('citations', []))}\n"
        appendices += f"- Execution Time: {research_results.get('execution_time', 0):.1f} seconds\n"
        appendices += f"- Phases Completed: {len(research_results.get('phase_results', []))}\n"
        appendices += f"- Average Relevance Score: {self._calculate_average_relevance(findings):.2f}\n\n"
        
        return appendices
    
    def _assemble_report(self, research_goal: str, executive_summary: str, methodology: str, 
                        findings: str, analysis: str, conclusions: str, bibliography: str, appendices: str) -> str:
        """Assemble all sections into final report"""
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        report = f"""# Autonomous Research Report

**Research Topic**: {research_goal}

**Generated**: {timestamp}

**Powered by**: CloudGROQ Autonomous Research Agent

---

{executive_summary}

---

{methodology}

---

{findings}

---

{analysis}

---

{conclusions}

---

{bibliography}

---

{appendices}

---

*This report was generated by an autonomous research agent using CloudGROQ AI inference. All findings have been systematically researched, analyzed, and cited. For questions about methodology or to verify sources, please refer to the citations and appendices.*
"""
        
        return report
    
    def _generate_report_metadata(self, research_results: Dict[str, Any], start_time: datetime, 
                                 end_time: datetime, duration: float) -> Dict[str, Any]:
        """Generate comprehensive report metadata"""
        findings = research_results.get('findings', [])
        citations = research_results.get('citations', [])
        
        return {
            'generation_timestamp': end_time.isoformat(),
            'generation_duration': duration,
            'research_goal': research_results.get('research_goal', ''),
            'total_findings': len(findings),
            'unique_sources': len(set(f.get('source_title', '') for f in findings)),
            'total_citations': len(citations),
            'quality_grade': research_results.get('quality_check', {}).get('quality_grade', 'Unknown'),
            'overall_quality_score': research_results.get('quality_check', {}).get('overall_score', 0),
            'research_duration': research_results.get('execution_time', 0),
            'phases_completed': len(research_results.get('phase_results', [])),
            'average_relevance_score': self._calculate_average_relevance(findings),
            'citation_style': self.config.citation_style,
            'agent_version': '1.0.0'
        }
    
    def _calculate_average_relevance(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate average relevance score across all findings"""
        if not findings:
            return 0.0
        
        relevance_scores = [f.get('relevance_score', 0) for f in findings]
        return sum(relevance_scores) / len(relevance_scores)
    
    def _convert_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML (basic conversion)"""
        # Basic markdown to HTML conversion
        html_content = markdown_content
        
        # Headers
        html_content = html_content.replace('# ', '<h1>').replace('\n', '</h1>\n', html_content.count('# '))
        html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>\n', html_content.count('## '))
        html_content = html_content.replace('### ', '<h3>').replace('\n', '</h3>\n', html_content.count('### '))
        
        # Bold text
        import re
        html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
        
        # Italic text
        html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
        
        # Line breaks
        html_content = html_content.replace('\n\n', '</p><p>')
        html_content = f'<html><body><p>{html_content}</p></body></html>'
        
        return html_content
    
    def _create_fallback_report(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic fallback report when compilation fails"""
        research_goal = research_results.get('research_goal', 'Unknown research goal')
        findings = research_results.get('findings', [])
        citations = research_results.get('citations', [])
        
        fallback_content = f"""# Research Report

**Topic**: {research_goal}

**Generated**: {datetime.now().strftime("%B %d, %Y")}

## Summary
Research was conducted on the specified topic. The automated system encountered issues during report compilation, but basic findings are available.

## Findings
- Total findings collected: {len(findings)}
- Sources analyzed: {len(set(f.get('source_title', '') for f in findings))}
- Citations generated: {len(citations)}

## Note
This is a simplified report due to compilation issues. Full analysis may require manual review of the collected data.

## Raw Data
Detailed findings and citations are available in the system data structures for further analysis.
"""
        
        return {
            'content': fallback_content,
            'source_count': len(set(f.get('source_title', '') for f in findings)),
            'citation_count': len(citations),
            'duration': '0.0s',
            'quality_grade': 'Incomplete',
            'compilation_timestamp': datetime.now().isoformat(),
            'metadata': {
                'generation_timestamp': datetime.now().isoformat(),
                'total_findings': len(findings),
                'status': 'fallback_report'
            }
        }
