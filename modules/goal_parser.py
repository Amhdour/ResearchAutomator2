"""
Goal Parser Module

Responsible for parsing user research goals and breaking them down into
manageable subtasks using CloudGROQ inference.
"""

import json
import re
from typing import Dict, List, Any
from .llm_tools import LLMTools
from utils.logger import get_logger

logger = get_logger(__name__)

class GoalParser:
    """Parse and decompose research goals into structured subtasks"""
    
    def __init__(self, config):
        self.config = config
        self.llm_tools = LLMTools(config)
        
    def parse_goal(self, goal: str) -> Dict[str, Any]:
        """
        Parse a research goal into structured subtasks
        
        Args:
            goal: Raw research goal string
            
        Returns:
            Dictionary containing parsed goal structure
        """
        logger.info(f"Parsing research goal: {goal[:100]}...")
        
        try:
            # Create prompt for goal parsing
            parsing_prompt = self._create_parsing_prompt(goal)
            
            # Get structured breakdown from LLM
            response = self.llm_tools.generate_text(
                prompt=parsing_prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse the response into structured format
            parsed_goal = self._extract_structured_goal(response)
            
            # Validate and enhance the parsed goal
            validated_goal = self._validate_and_enhance(parsed_goal, goal)
            
            logger.info(f"Successfully parsed goal into {len(validated_goal.get('subgoals', []))} subtasks")
            return validated_goal
            
        except Exception as e:
            logger.error(f"Failed to parse goal: {str(e)}")
            # Return fallback structure
            return self._create_fallback_structure(goal)
    
    def _create_parsing_prompt(self, goal: str) -> str:
        """Create a structured prompt for goal parsing"""
        return f"""
You are an expert research assistant. Break down the following research goal into specific, actionable subtasks.

Research Goal: {goal}

Please provide a structured breakdown in the following JSON format:
{{
    "main_goal": "Brief restatement of the main research objective",
    "research_domain": "Primary field/domain of research",
    "time_scope": "Time period if specified (e.g., 'last 5 years', 'recent', etc.)",
    "subgoals": [
        {{
            "id": 1,
            "title": "Brief title of subtask",
            "description": "Detailed description of what needs to be researched",
            "search_terms": ["keyword1", "keyword2", "keyword3"],
            "priority": "high|medium|low",
            "expected_sources": ["academic papers", "news articles", "reports", "websites"]
        }}
    ],
    "success_criteria": [
        "Specific criterion 1",
        "Specific criterion 2"
    ],
    "estimated_complexity": "simple|moderate|complex"
}}

Focus on creating 3-7 specific, non-overlapping subtasks that together comprehensively address the main goal.
Each subtask should be specific enough to guide targeted information retrieval.
"""

    def _extract_structured_goal(self, response: str) -> Dict[str, Any]:
        """Extract structured goal from LLM response"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                raise ValueError("No JSON structure found in response")
                
        except Exception as e:
            logger.warning(f"Failed to extract JSON structure: {str(e)}")
            # Try to parse key information manually
            return self._manual_parse(response)
    
    def _manual_parse(self, response: str) -> Dict[str, Any]:
        """Manually parse response when JSON extraction fails"""
        lines = response.split('\n')
        
        # Extract main components
        main_goal = ""
        subgoals = []
        
        current_subgoal = {}
        in_subgoal = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for main goal indicators
            if any(indicator in line.lower() for indicator in ['main goal', 'objective', 'research goal']):
                main_goal = line.split(':', 1)[-1].strip() if ':' in line else line
            
            # Look for subgoal indicators
            elif any(indicator in line.lower() for indicator in ['subtask', 'subgoal', 'task']):
                if current_subgoal:
                    subgoals.append(current_subgoal)
                current_subgoal = {
                    'id': len(subgoals) + 1,
                    'title': line,
                    'description': '',
                    'search_terms': [],
                    'priority': 'medium',
                    'expected_sources': ['academic papers', 'websites']
                }
                in_subgoal = True
            
            elif in_subgoal and line:
                # Add to current subgoal description
                if current_subgoal['description']:
                    current_subgoal['description'] += ' ' + line
                else:
                    current_subgoal['description'] = line
        
        # Add final subgoal
        if current_subgoal:
            subgoals.append(current_subgoal)
        
        return {
            'main_goal': main_goal or "Research the specified topic",
            'research_domain': "General",
            'time_scope': "recent",
            'subgoals': subgoals,
            'success_criteria': ["Comprehensive coverage", "Accurate citations"],
            'estimated_complexity': "moderate"
        }
    
    def _validate_and_enhance(self, parsed_goal: Dict[str, Any], original_goal: str) -> Dict[str, Any]:
        """Validate and enhance the parsed goal structure"""
        # Ensure required fields exist
        if 'subgoals' not in parsed_goal:
            parsed_goal['subgoals'] = []
        
        if 'main_goal' not in parsed_goal:
            parsed_goal['main_goal'] = original_goal
        
        # Enhance subgoals with missing information
        for i, subgoal in enumerate(parsed_goal['subgoals']):
            if 'id' not in subgoal:
                subgoal['id'] = i + 1
            
            if 'search_terms' not in subgoal or not subgoal['search_terms']:
                subgoal['search_terms'] = self._generate_search_terms(subgoal.get('description', ''))
            
            if 'priority' not in subgoal:
                subgoal['priority'] = 'medium'
            
            if 'expected_sources' not in subgoal:
                subgoal['expected_sources'] = ['academic papers', 'websites', 'reports']
        
        # Add metadata
        parsed_goal['created_at'] = self._get_timestamp()
        parsed_goal['total_subgoals'] = len(parsed_goal['subgoals'])
        
        return parsed_goal
    
    def _generate_search_terms(self, description: str) -> List[str]:
        """Generate search terms from description"""
        if not description:
            return ["research", "information"]
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 
            'boy', 'did', 'she', 'use', 'find', 'any', 'work', 'part', 'take', 
            'know', 'back', 'good', 'give', 'most', 'very', 'research', 'comprehensive',
            'conduct', 'information', 'data'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates while preserving order
        unique_keywords = list(dict.fromkeys(keywords))
        
        # Ensure we have at least some search terms
        if not unique_keywords:
            # Try to identify specific topics from the description
            if 'morocco' in description.lower():
                return ['morocco', 'location', 'geography', 'africa', 'country']
            elif any(geo_term in description.lower() for geo_term in ['where', 'location', 'place', 'country', 'city']):
                # Extract the main subject
                words_clean = [w for w in words if len(w) > 3]
                if words_clean:
                    return words_clean[:3] + ['location', 'geography']
                else:
                    return ['location', 'geography', 'place']
            else:
                return ['information', 'research', 'facts']
        
        # Return top 5 unique keywords
        return unique_keywords[:5]
    
    def _create_fallback_structure(self, goal: str) -> Dict[str, Any]:
        """Create a basic fallback structure when parsing fails"""
        return {
            'main_goal': goal,
            'research_domain': 'General',
            'time_scope': 'recent',
            'subgoals': [
                {
                    'id': 1,
                    'title': 'Primary Research',
                    'description': f'Conduct comprehensive research on: {goal}',
                    'search_terms': self._generate_search_terms(goal),
                    'priority': 'high',
                    'expected_sources': ['academic papers', 'websites', 'reports']
                }
            ],
            'success_criteria': ['Comprehensive coverage', 'Accurate information', 'Proper citations'],
            'estimated_complexity': 'moderate',
            'created_at': self._get_timestamp(),
            'total_subgoals': 1
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
