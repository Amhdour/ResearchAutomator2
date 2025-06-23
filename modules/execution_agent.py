"""
Execution Agent Module

Orchestrates the research execution process, coordinating between all modules
to conduct autonomous research based on the generated plan.
"""

import time
from typing import Dict, List, Any, Optional
from .planner import Planner
from .retriever import Retriever
from .memory_manager import MemoryManager
from .llm_tools import LLMTools
from .citation_engine import CitationEngine
from .self_critique import SelfCritique
from .batch_processor import BatchProcessor
from .emergency_mode import EmergencyMode
from database.operations import DatabaseOperations
from utils.logger import get_logger

logger = get_logger(__name__)

class ExecutionAgent:
    """Main execution agent that orchestrates research process"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize all modules
        self.planner = Planner(config)
        self.retriever = Retriever(config)
        self.memory_manager = MemoryManager(config)
        self.llm_tools = LLMTools(config)
        self.citation_engine = CitationEngine(config)
        self.self_critique = SelfCritique(config)
        self.batch_processor = BatchProcessor(config, batch_size=1, delay_between_batches=10.0)  # More conservative
        self.emergency_mode = EmergencyMode(config)
        self.db_ops = DatabaseOperations()
        self.rate_limit_mode = False
        
        # Execution state
        self.current_plan = None
        self.completed_phases = []
        self.all_findings = []
        self.all_citations = []
        self.execution_log = []
        self.current_session_id = None
        
    def execute_research(self, parsed_goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete research process
        
        Args:
            parsed_goal: Parsed research goal from GoalParser
            
        Returns:
            Complete research results
        """
        logger.info("Starting research execution")
        start_time = time.time()
        
        try:
            # Create database session
            self.current_session_id = self.db_ops.create_research_session(
                research_goal=parsed_goal.get('main_goal', ''),
                config=self.config.to_dict()
            )
            
            # Step 1: Create execution plan
            self._log_step("Creating execution plan")
            self.current_plan = self.planner.create_execution_plan(parsed_goal)
            
            # Step 2: Execute phases
            self._log_step("Beginning research phases")
            phase_results = self._execute_phases()
            
            # Step 3: Synthesize findings
            self._log_step("Synthesizing research findings")
            synthesis_results = self._synthesize_findings()
            
            # Step 4: Final quality check
            self._log_step("Conducting final quality review")
            quality_results = self._final_quality_check()
            
            # Compile final results
            execution_time = time.time() - start_time
            
            # Save findings and citations to database
            if self.current_session_id:
                self.db_ops.save_findings(self.current_session_id, self.all_findings)
                self.db_ops.save_citations(self.current_session_id, self.all_citations)
                
                # Update session with final results
                self.db_ops.update_session_status(
                    self.current_session_id,
                    'completed',
                    total_sources=len(set(f.get('source_title', '') for f in self.all_findings)),
                    total_findings=len(self.all_findings),
                    total_citations=len(self.all_citations),
                    quality_score=quality_results.get('overall_score', 0.0),
                    execution_time=execution_time
                )
            
            results = {
                'success': True,
                'research_goal': parsed_goal.get('main_goal', ''),
                'execution_plan': self.current_plan,
                'phase_results': phase_results,
                'synthesis': synthesis_results,
                'quality_check': quality_results,
                'findings': self.all_findings,
                'citations': self.all_citations,
                'execution_log': self.execution_log,
                'execution_time': execution_time,
                'steps': self._get_execution_steps(),
                'metadata': {
                    'total_sources': len(self.all_findings),
                    'total_citations': len(self.all_citations),
                    'phases_completed': len(self.completed_phases),
                    'quality_score': quality_results.get('overall_score', 0.0)
                },
                'session_id': self.current_session_id
            }
            
            logger.info(f"Research execution completed successfully in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Research execution failed: {str(e)}")
            
            # Update database with failure
            if self.current_session_id:
                self.db_ops.update_session_status(self.current_session_id, 'failed')
            
            return {
                'success': False,
                'error': str(e),
                'execution_log': self.execution_log,
                'partial_results': {
                    'findings': self.all_findings,
                    'citations': self.all_citations
                },
                'session_id': self.current_session_id
            }
    
    def _execute_phases(self) -> List[Dict[str, Any]]:
        """Execute all phases in the research plan"""
        phase_results = []
        
        while True:
            # Get next phase to execute
            next_phase = self.planner.get_next_phase(self.current_plan, self.completed_phases)
            
            if not next_phase:
                logger.info("All phases completed")
                break
            
            logger.info(f"Executing phase: {next_phase.get('title', 'Unknown')}")
            
            try:
                # Execute single phase
                result = self._execute_single_phase(next_phase)
                phase_results.append(result)
                
                # Mark phase as completed
                self.completed_phases.append(next_phase['id'])
                
                # Save phase to database
                if self.current_session_id:
                    self.db_ops.save_research_phase(self.current_session_id, result)
                
                # Check if we should update plan based on new findings
                if result.get('new_insights'):
                    self._consider_plan_updates(result['new_insights'])
                
            except Exception as e:
                logger.error(f"Phase execution failed: {str(e)}")
                phase_results.append({
                    'phase_id': next_phase['id'],
                    'success': False,
                    'error': str(e)
                })
        
        return phase_results
    
    def _execute_single_phase(self, phase: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single research phase"""
        phase_id = phase.get('id', 'unknown')
        phase_title = phase.get('title', 'Unknown Phase')
        
        self._log_step(f"Executing phase: {phase_title}")
        
        # Step 1: Retrieve information based on search terms
        search_terms = phase.get('search_terms', [])
        expected_sources = phase.get('expected_sources', ['web'])
        
        retrieved_docs = self.retriever.retrieve_from_sources(search_terms, expected_sources)
        
        if not retrieved_docs:
            logger.warning(f"No documents retrieved for phase {phase_id}")
            return {
                'phase_id': phase_id,
                'success': False,
                'error': 'No documents retrieved'
            }
        
        # Step 2: Store documents in memory
        stored_ids = self.memory_manager.store_documents(retrieved_docs)
        
        # Step 3: Extract key information from documents
        phase_findings = []
        phase_citations = []
        
        for doc in retrieved_docs:
            try:
                # Extract key information using LLM
                key_info = self.llm_tools.extract_key_information(
                    doc.get('content', ''),
                    self.current_plan.get('research_goal', '')
                )
                
                if key_info.get('relevance_score', 0) > 0.3:  # Only include relevant findings
                    finding = {
                        'source_title': doc.get('title', ''),
                        'source_url': doc.get('url', ''),
                        'key_findings': key_info.get('key_findings', []),
                        'relevant_facts': key_info.get('relevant_facts', []),
                        'statistics': key_info.get('statistics', []),
                        'conclusions': key_info.get('conclusions', []),
                        'relevance_score': key_info.get('relevance_score', 0),
                        'phase_id': phase_id
                    }
                    phase_findings.append(finding)
                    self.all_findings.append(finding)
                
                # Extract citations
                citations = self.citation_engine.extract_citations_from_content(
                    doc.get('content', ''),
                    doc
                )
                phase_citations.extend(citations)
                self.all_citations.extend(citations)
                
            except Exception as e:
                logger.warning(f"Failed to process document {doc.get('title', 'Unknown')}: {str(e)}")
                continue
        
        # Step 4: Synthesize phase findings
        phase_summary = self._synthesize_phase_findings(phase_findings, phase)
        
        # Step 5: Self-critique phase results
        critique_result = self.self_critique.critique_phase_results({
            'phase': phase,
            'findings': phase_findings,
            'summary': phase_summary
        })
        
        return {
            'phase_id': phase_id,
            'phase_title': phase_title,
            'success': True,
            'documents_retrieved': len(retrieved_docs),
            'documents_stored': len(stored_ids),
            'findings': phase_findings,
            'citations': phase_citations,
            'summary': phase_summary,
            'critique': critique_result,
            'new_insights': self._extract_new_insights(phase_findings)
        }
    
    def _synthesize_phase_findings(self, findings: List[Dict[str, Any]], phase: Dict[str, Any]) -> str:
        """Synthesize findings from a single phase"""
        if not findings:
            return "No significant findings in this phase."
        
        # Prepare content for synthesis
        findings_text = "\n\n".join([
            f"Source: {finding.get('source_title', 'Unknown')}\n" +
            "Key Findings: " + "; ".join(finding.get('key_findings', [])) + "\n" +
            "Facts: " + "; ".join(finding.get('relevant_facts', [])) + "\n" +
            "Statistics: " + "; ".join(finding.get('statistics', []))
            for finding in findings[:5]  # Limit to top 5 findings
        ])
        
        # Generate synthesis using LLM
        synthesis_prompt = f"""
Synthesize the following research findings for the phase: {phase.get('title', '')}

Phase Description: {phase.get('description', '')}

Research Findings:
{findings_text}

Create a comprehensive synthesis that:
- Summarizes the key discoveries
- Identifies patterns and themes
- Highlights important statistics or facts
- Notes any contradictions or gaps
- Draws preliminary conclusions

Synthesis:
"""
        
        try:
            synthesis = self.llm_tools.generate_text(
                prompt=synthesis_prompt,
                max_tokens=1000,
                temperature=0.4
            )
            return synthesis
        except Exception as e:
            logger.error(f"Phase synthesis failed: {str(e)}")
            return f"Phase completed with {len(findings)} findings from {len(set(f.get('source_title', '') for f in findings))} sources."
    
    def _synthesize_findings(self) -> Dict[str, Any]:
        """Synthesize all research findings"""
        logger.info("Synthesizing all research findings")
        
        if not self.all_findings:
            return {'summary': 'No findings to synthesize', 'key_themes': [], 'conclusions': []}
        
        # Group findings by themes
        thematic_groups = self._group_findings_by_theme()
        
        # Generate overall synthesis
        overall_synthesis = self._generate_overall_synthesis()
        
        # Extract key conclusions
        key_conclusions = self._extract_key_conclusions()
        
        return {
            'summary': overall_synthesis,
            'thematic_groups': thematic_groups,
            'key_conclusions': key_conclusions,
            'total_findings': len(self.all_findings),
            'unique_sources': len(set(f.get('source_title', '') for f in self.all_findings))
        }
    
    def _final_quality_check(self) -> Dict[str, Any]:
        """Conduct final quality review of research"""
        logger.info("Conducting final quality review")
        
        # Compile all content for review
        research_content = {
            'goal': self.current_plan.get('research_goal', ''),
            'findings': self.all_findings,
            'citations': self.all_citations,
            'phases_completed': len(self.completed_phases)
        }
        
        # Use self-critique module for comprehensive review
        quality_result = self.self_critique.final_quality_review(research_content)
        
        return quality_result
    
    def _consider_plan_updates(self, new_insights: List[str]) -> None:
        """Consider updating the research plan based on new insights"""
        if not new_insights:
            return
        
        try:
            # Check if plan should be updated
            updated_plan = self.planner.update_plan(
                self.current_plan,
                new_insights,
                self.completed_phases
            )
            
            if updated_plan != self.current_plan:
                logger.info("Research plan updated based on new insights")
                self.current_plan = updated_plan
                self._log_step("Plan updated based on new discoveries")
        
        except Exception as e:
            logger.warning(f"Failed to update plan: {str(e)}")
    
    def _extract_new_insights(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Extract new insights that might warrant plan updates"""
        insights = []
        
        for finding in findings:
            # Look for high-relevance findings
            if finding.get('relevance_score', 0) > 0.8:
                insights.extend(finding.get('key_findings', []))
            
            # Look for unexpected conclusions
            conclusions = finding.get('conclusions', [])
            insights.extend(conclusions)
        
        return insights[:5]  # Limit to top 5 insights
    
    def _group_findings_by_theme(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group findings by thematic similarity"""
        # Simple thematic grouping based on keywords
        themes = {}
        
        for finding in self.all_findings:
            # Extract themes from key findings
            for key_finding in finding.get('key_findings', []):
                # Simple keyword-based grouping
                words = key_finding.lower().split()
                theme_candidates = [word for word in words if len(word) > 5]
                
                if theme_candidates:
                    theme = theme_candidates[0]  # Use first significant word as theme
                    if theme not in themes:
                        themes[theme] = []
                    themes[theme].append(finding)
        
        return themes
    
    def _generate_overall_synthesis(self) -> str:
        """Generate overall synthesis of all findings"""
        # Prepare summary of all findings
        findings_summary = []
        
        for finding in self.all_findings[:10]:  # Top 10 findings
            summary = f"From {finding.get('source_title', 'Unknown source')}: "
            summary += "; ".join(finding.get('key_findings', [])[:3])  # Top 3 key findings
            findings_summary.append(summary)
        
        synthesis_prompt = f"""
Create a comprehensive synthesis of the research findings for the goal: {self.current_plan.get('research_goal', '')}

Key Findings Summary:
{chr(10).join(findings_summary)}

Total sources analyzed: {len(set(f.get('source_title', '') for f in self.all_findings))}

Create a synthesis that:
- Provides an executive summary of key discoveries
- Identifies major trends and patterns
- Highlights the most significant findings
- Addresses the original research goal
- Notes any limitations or gaps in the research

Synthesis:
"""
        
        try:
            return self.llm_tools.generate_text(
                prompt=synthesis_prompt,
                max_tokens=1500,
                temperature=0.4
            )
        except Exception as e:
            logger.error(f"Overall synthesis failed: {str(e)}")
            return f"Research completed with {len(self.all_findings)} findings from {len(set(f.get('source_title', '') for f in self.all_findings))} unique sources."
    
    def _extract_key_conclusions(self) -> List[str]:
        """Extract key conclusions from all findings"""
        conclusions = []
        
        for finding in self.all_findings:
            conclusions.extend(finding.get('conclusions', []))
        
        # Remove duplicates and return top conclusions
        unique_conclusions = list(set(conclusions))
        return unique_conclusions[:10]
    
    def _log_step(self, description: str) -> None:
        """Log an execution step"""
        log_entry = {
            'timestamp': time.time(),
            'description': description,
            'completed_phases': len(self.completed_phases)
        }
        self.execution_log.append(log_entry)
        logger.info(f"Step: {description}")
    
    def _get_execution_steps(self) -> List[Dict[str, Any]]:
        """Get formatted execution steps for display"""
        steps = []
        
        for entry in self.execution_log:
            steps.append({
                'description': entry['description'],
                'completed': True,
                'timestamp': entry['timestamp']
            })
        
        return steps
