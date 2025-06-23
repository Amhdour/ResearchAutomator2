"""
Batch Processor Module

Processes research tasks in smaller batches to manage API rate limits
and provide better progress feedback to users.
"""

import time
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class BatchProcessor:
    """Process research tasks in manageable batches"""
    
    def __init__(self, config, batch_size: int = 2, delay_between_batches: float = 5.0):
        self.config = config
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        
    def process_sources_in_batches(self, sources: List[Dict[str, Any]], processor_func, progress_callback=None) -> List[Dict[str, Any]]:
        """Process sources in batches with delays"""
        results = []
        total_batches = (len(sources) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(sources), self.batch_size):
            batch = sources[batch_idx:batch_idx + self.batch_size]
            batch_num = (batch_idx // self.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} sources)")
            
            # Process batch
            batch_results = []
            for source in batch:
                try:
                    result = processor_func(source)
                    if result:
                        batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process source {source.get('title', 'Unknown')}: {str(e)}")
                    continue
            
            results.extend(batch_results)
            
            # Update progress if callback provided
            if progress_callback:
                progress = min(100, (batch_num / total_batches) * 100)
                progress_callback(progress, f"Processed batch {batch_num}/{total_batches}")
            
            # Delay between batches (except for last batch)
            if batch_idx + self.batch_size < len(sources):
                logger.debug(f"Waiting {self.delay_between_batches}s before next batch")
                time.sleep(self.delay_between_batches)
        
        return results
    
    def process_phases_incrementally(self, phases: List[Dict[str, Any]], executor_func, progress_callback=None) -> List[Dict[str, Any]]:
        """Process research phases with incremental progress updates"""
        results = []
        
        for i, phase in enumerate(phases):
            logger.info(f"Processing phase {i+1}/{len(phases)}: {phase.get('title', 'Unknown')}")
            
            try:
                # Process phase with extended timeout for rate limits
                result = executor_func(phase)
                results.append(result)
                
                # Update progress
                if progress_callback:
                    progress = ((i + 1) / len(phases)) * 100
                    progress_callback(progress, f"Completed phase: {phase.get('title', 'Unknown')}")
                
                # Longer delay between phases
                if i < len(phases) - 1:
                    logger.debug(f"Waiting {self.delay_between_batches * 2}s before next phase")
                    time.sleep(self.delay_between_batches * 2)
                    
            except Exception as e:
                logger.error(f"Phase {i+1} failed: {str(e)}")
                results.append({
                    'phase_id': phase.get('id', f'phase_{i+1}'),
                    'success': False,
                    'error': str(e)
                })
        
        return results