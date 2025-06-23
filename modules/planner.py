"""
Planner Module

Creates and manages research execution plans using CloudGROQ-powered planning.
Handles task sequencing, dependency management, and dynamic re-planning.
"""

from typing import Dict, List, Any, Optional
from .llm_tools import LLMTools
from utils.logger import get_logger
import json
import re

logger = get_logger(__name__)

class Planner:
    """Plan and sequence research tasks using AI-powered planning"""
    
    def __init__(self, config):
        self.config = config
        self.llm_tools = LLMTools(config)
    
    def create_execution_plan(self, parsed_goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed execution plan from parsed research goal
        
        Args:
            parsed_goal: Structured goal from GoalParser
            
        Returns:
            Detailed execution plan
        """
        logger.info("Creating execution plan")
        
        try:
            # Generate the main execution plan
            plan_prompt = self._create_planning_prompt(parsed_goal)
            plan_response = self.llm_tools.generate_text(
                prompt=plan_prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            # Extract structured plan
            execution_plan = self._extract_execution_plan(plan_response)
            
            # Enhance plan with additional details
            enhanced_plan = self._enhance_plan(execution_plan, parsed_goal)
            
            logger.info(f"Created execution plan with {len(enhanced_plan.get('phases', []))} phases")
            return enhanced_plan
            
        except Exception as e:
            logger.error(f"Failed to create execution plan: {str(e)}")
            return self._create_fallback_plan(parsed_goal)
    
    def update_plan(self, current_plan: Dict[str, Any], new_findings: List[str], completed_phases: List[str]) -> Dict[str, Any]:
        """
        Update execution plan based on new findings and completed phases
        
        Args:
            current_plan: Current execution plan
            new_findings: List of new findings discovered
            completed_phases: List of completed phase IDs
            
        Returns:
            Updated execution plan
        """
        logger.info("Updating execution plan based on new findings")
        
        try:
            update_prompt = self._create_update_prompt(current_plan, new_findings, completed_phases)
            update_response = self.llm_tools.generate_text(
                prompt=update_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse update instructions
            updates = self._parse_plan_updates(update_response)
            
            # Apply updates to current plan
            updated_plan = self._apply_plan_updates(current_plan, updates)
            
            logger.info("Successfully updated execution plan")
            return updated_plan
            
        except Exception as e:
            logger.error(f"Failed to update execution plan: {str(e)}")
            return current_plan  # Return unchanged plan on failure
    
    def get_next_phase(self, plan: Dict[str, Any], completed_phases: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get the next phase to execute from the plan
        
        Args:
            plan: Execution plan
            completed_phases: List of completed phase IDs
            
        Returns:
            Next phase to execute or None if plan is complete
        """
        phases = plan.get('phases', [])
        
        for phase in phases:
            phase_id = phase.get('id', '')
            dependencies = phase.get('dependencies', [])
            
            # Skip if already completed
            if phase_id in completed_phases:
                continue
            
            # Check if all dependencies are satisfied
            if all(dep in completed_phases for dep in dependencies):
                logger.info(f"Next phase to execute: {phase.get('title', phase_id)}")
                return phase
        
        logger.info("No more phases to execute - plan complete")
        return None
    
    def estimate_plan_duration(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate duration and resource requirements for plan
        
        Args:
            plan: Execution plan
            
        Returns:
            Duration and resource estimates
        """
        phases = plan.get('phases', [])
        
        total_searches = 0
        total_sources = 0
        estimated_minutes = 0
        
        for phase in phases:
            # Estimate based on phase type and search terms
            search_terms = phase.get('search_terms', [])
            expected_sources = phase.get('expected_sources', [])
            
            total_searches += len(search_terms)
            total_sources += len(search_terms) * self.config.max_sources // len(search_terms) if search_terms else 0
            
            # Estimate time: 1-2 minutes per search term + processing time
            phase_time = len(search_terms) * 1.5 + 2  # Base processing time
            estimated_minutes += phase_time
        
        return {
            'total_phases': len(phases),
            'total_searches': total_searches,
            'estimated_sources': total_sources,
            'estimated_duration_minutes': int(estimated_minutes),
            'complexity': plan.get('estimated_complexity', 'moderate')
        }
    
    def _create_planning_prompt(self, parsed_goal: Dict[str, Any]) -> str:
        """Create prompt for execution planning"""
        subgoals_text = "\n".join([
            f"{i+1}. {subgoal['title']}: {subgoal['description']}"
            for i, subgoal in enumerate(parsed_goal.get('subgoals', []))
        ])
        
        return f"""
Create a detailed execution plan for the following research project:

Main Goal: {parsed_goal.get('main_goal', '')}
Research Domain: {parsed_goal.get('research_domain', '')}
Time Scope: {parsed_goal.get('time_scope', '')}

Subgoals:
{subgoals_text}

Create an execution plan with the following JSON structure:
{{
    "plan_id": "unique_plan_identifier",
    "strategy": "research strategy description",
    "phases": [
        {{
            "id": "phase_1",
            "title": "Phase title",
            "description": "Detailed description of what this phase accomplishes",
            "type": "research|analysis|synthesis|validation",
            "search_terms": ["term1", "term2", "term3"],
            "expected_sources": ["academic", "web", "reports"],
            "dependencies": [],
            "success_criteria": ["criterion 1", "criterion 2"],
            "priority": "high|medium|low"
        }}
    ],
    "quality_gates": [
        "Quality checkpoint 1",
        "Quality checkpoint 2"
    ],
    "risk_factors": [
        "Potential risk 1",
        "Potential risk 2"
    ]
}}

Requirements:
- Create 3-6 logical phases that build upon each other
- Each phase should have specific, actionable search terms
- Include dependencies between phases where appropriate
- Focus on comprehensive coverage of the research goal
- Include validation and synthesis phases
"""

    def _extract_execution_plan(self, response: str) -> Dict[str, Any]:
        """Extract structured execution plan from LLM response"""
        try:
            # Try to find JSON in the response - look for complete JSON blocks
            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            
            for json_str in json_matches:
                try:
                    parsed = json.loads(json_str)
                    # Validate that this looks like a plan
                    if 'phases' in parsed and isinstance(parsed['phases'], list):
                        return parsed
                except json.JSONDecodeError:
                    continue
            
            # If no valid JSON found, try extracting from code blocks
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if code_block_match:
                return json.loads(code_block_match.group(1))
            
            raise ValueError("No valid JSON structure found in response")
                
        except Exception as e:
            logger.warning(f"Failed to extract JSON plan: {str(e)}")
            return self._manual_parse_plan(response)
    
    def _manual_parse_plan(self, response: str) -> Dict[str, Any]:
        """Manually parse plan when JSON extraction fails"""
        lines = response.split('\n')
        
        phases = []
        current_phase = {}
        
        # Extract the main research goal from the response for generating search terms
        main_goal = "research topic"
        for line in lines[:10]:  # Check first few lines
            if "goal" in line.lower() or "research" in line.lower():
                main_goal = line.strip()
                break
        
        phase_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for phase indicators with more specific patterns
            if any(indicator in line.lower() for indicator in ['phase', 'step', 'stage']) and any(char.isdigit() for char in line):
                if current_phase:
                    phases.append(current_phase)
                
                phase_count += 1
                # Extract phase title more carefully
                title = line
                if ':' in line:
                    title = line.split(':', 1)[1].strip()
                
                # Generate search terms based on the phase title and description
                search_terms = self._generate_search_terms_from_text(title + " " + main_goal)
                
                current_phase = {
                    'id': f"phase_{phase_count}",
                    'title': title,
                    'description': title,
                    'type': 'research',
                    'search_terms': search_terms,
                    'expected_sources': ['web', 'academic'],
                    'dependencies': [f"phase_{phase_count - 1}"] if phase_count > 1 else [],
                    'success_criteria': ['Relevant information found'],
                    'priority': 'medium'
                }
        
        # Add final phase
        if current_phase:
            phases.append(current_phase)
        
        # If no phases were extracted, create a default research phase
        if not phases:
            phases = [{
                'id': 'phase_1',
                'title': 'Primary Research',
                'description': f'Research the main topic: {main_goal}',
                'type': 'research',
                'search_terms': self._generate_search_terms_from_text(main_goal),
                'expected_sources': ['web', 'academic'],
                'dependencies': [],
                'success_criteria': ['Relevant information found'],
                'priority': 'high'
            }]
        
        return {
            'plan_id': 'manual_plan',
            'strategy': 'Sequential research and analysis',
            'phases': phases,
            'quality_gates': ['Source validation', 'Content review'],
            'risk_factors': ['Information quality', 'Source availability']
        }
    
    def _enhance_plan(self, plan: Dict[str, Any], parsed_goal: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance plan with additional details"""
        # Add metadata
        plan['created_at'] = self._get_timestamp()
        plan['research_goal'] = parsed_goal.get('main_goal', '')
        plan['estimated_complexity'] = parsed_goal.get('estimated_complexity', 'moderate')
        
        # Enhance phases with search terms from subgoals
        subgoals = parsed_goal.get('subgoals', [])
        
        for i, phase in enumerate(plan.get('phases', [])):
            # If phase doesn't have search terms, derive from subgoals
            if not phase.get('search_terms') and i < len(subgoals):
                phase['search_terms'] = subgoals[i].get('search_terms', [])
                phase['expected_sources'] = subgoals[i].get('expected_sources', ['web', 'academic'])
        
        return plan
    
    def _create_update_prompt(self, current_plan: Dict[str, Any], new_findings: List[str], completed_phases: List[str]) -> str:
        """Create prompt for plan updates"""
        findings_text = "\n".join([f"- {finding}" for finding in new_findings[:5]])
        completed_text = ", ".join(completed_phases)
        
        return f"""
Based on new research findings, analyze if the current execution plan needs updates.

Current Plan Summary:
- Research Goal: {current_plan.get('research_goal', '')}
- Total Phases: {len(current_plan.get('phases', []))}
- Completed Phases: {completed_text}

New Findings:
{findings_text}

Analyze whether these findings suggest:
1. New research directions to explore
2. Phases that should be modified or added
3. Search terms that should be updated
4. Priorities that should be adjusted

Provide recommendations in JSON format:
{{
    "update_needed": true/false,
    "new_phases": [
        {{
            "title": "New phase title",
            "description": "Description",
            "search_terms": ["term1", "term2"],
            "priority": "high|medium|low"
        }}
    ],
    "modify_phases": [
        {{
            "phase_id": "existing_phase_id",
            "updates": {{
                "search_terms": ["updated", "terms"],
                "priority": "new_priority"
            }}
        }}
    ],
    "reasoning": "Explanation of why updates are needed"
}}
"""

    def _parse_plan_updates(self, response: str) -> Dict[str, Any]:
        """Parse plan update instructions"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'update_needed': False, 'new_phases': [], 'modify_phases': []}
        except Exception as e:
            logger.error(f"Failed to parse plan updates: {str(e)}")
            return {'update_needed': False, 'new_phases': [], 'modify_phases': []}
    
    def _apply_plan_updates(self, current_plan: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply updates to current plan"""
        if not updates.get('update_needed', False):
            return current_plan
        
        updated_plan = current_plan.copy()
        
        # Add new phases
        new_phases = updates.get('new_phases', [])
        for new_phase in new_phases:
            phase_id = f"phase_{len(updated_plan['phases']) + 1}"
            phase = {
                'id': phase_id,
                'title': new_phase.get('title', ''),
                'description': new_phase.get('description', ''),
                'type': 'research',
                'search_terms': new_phase.get('search_terms', []),
                'expected_sources': ['web', 'academic'],
                'dependencies': [],
                'success_criteria': [],
                'priority': new_phase.get('priority', 'medium')
            }
            updated_plan['phases'].append(phase)
        
        # Modify existing phases
        modifications = updates.get('modify_phases', [])
        for mod in modifications:
            phase_id = mod.get('phase_id', '')
            phase_updates = mod.get('updates', {})
            
            # Find and update the phase
            for phase in updated_plan['phases']:
                if phase['id'] == phase_id:
                    phase.update(phase_updates)
                    break
        
        # Update metadata
        updated_plan['last_updated'] = self._get_timestamp()
        updated_plan['update_reason'] = updates.get('reasoning', 'Plan updated based on new findings')
        
        return updated_plan
    
    def _create_fallback_plan(self, parsed_goal: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic fallback plan when planning fails"""
        subgoals = parsed_goal.get('subgoals', [])
        main_goal = parsed_goal.get('main_goal', '')
        
        phases = []
        for i, subgoal in enumerate(subgoals):
            # Ensure search terms exist
            search_terms = subgoal.get('search_terms', [])
            if not search_terms:
                # Generate from subgoal description and main goal
                text_to_analyze = f"{subgoal.get('description', '')} {main_goal}"
                search_terms = self._generate_search_terms_from_text(text_to_analyze)
            
            phases.append({
                'id': f"phase_{i+1}",
                'title': subgoal.get('title', f'Research Phase {i+1}'),
                'description': subgoal.get('description', f'Research aspect {i+1} of: {main_goal}'),
                'type': 'research',
                'search_terms': search_terms,
                'expected_sources': subgoal.get('expected_sources', ['web', 'academic']),
                'dependencies': [f"phase_{i}"] if i > 0 else [],
                'success_criteria': ['Relevant information found'],
                'priority': subgoal.get('priority', 'medium')
            })
        
        # If no phases created, create a default one
        if not phases:
            phases = [{
                'id': 'phase_1',
                'title': 'Primary Research',
                'description': f'Comprehensive research on: {main_goal}',
                'type': 'research',
                'search_terms': self._generate_search_terms_from_text(main_goal),
                'expected_sources': ['web', 'academic'],
                'dependencies': [],
                'success_criteria': ['Relevant information found'],
                'priority': 'high'
            }]
        
        return {
            'plan_id': 'fallback_plan',
            'strategy': 'Sequential research of identified subgoals',
            'phases': phases,
            'quality_gates': ['Source validation'],
            'risk_factors': ['Limited planning capability'],
            'created_at': self._get_timestamp(),
            'research_goal': main_goal,
            'estimated_complexity': parsed_goal.get('estimated_complexity', 'moderate')
        }
    
    def _generate_search_terms_from_text(self, text: str) -> List[str]:
        """Generate search terms from text content"""
        if not text:
            return ["research", "information"]
        
        # Clean and extract keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 
            'boy', 'did', 'she', 'use', 'find', 'any', 'work', 'part', 'take', 
            'know', 'back', 'good', 'give', 'most', 'very', 'phase', 'research',
            'description', 'type', 'analysis', 'step', 'stage'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates and limit to top 5
        unique_keywords = list(dict.fromkeys(keywords))[:5]
        
        # Ensure we have at least some search terms
        if not unique_keywords:
            if 'morocco' in text.lower():
                return ['morocco', 'location', 'geography', 'africa', 'country']
            else:
                return ['information', 'research', 'data', 'facts', 'details']
        
        return unique_keywords
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
