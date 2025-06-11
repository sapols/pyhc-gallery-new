#!/usr/bin/env python3
"""
LLM-powered example processor for PyHC Gallery

This module uses Claude to improve, standardize, and format scraped code examples
for inclusion in the PyHC gallery.
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
import re

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class ProcessingResult:
    """Result of LLM processing"""
    improved_code: str
    improved_title: str
    improved_description: str
    category: str
    confidence_score: float
    warnings: List[str]
    processing_notes: str


class ClaudeExampleProcessor:
    """Process examples using Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        if anthropic is None:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
    
    async def process_example(self, example: Dict[str, Any]) -> ProcessingResult:
        """Process a single code example using Claude"""
        
        prompt = self._create_processing_prompt(example)
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            result_text = response.content[0].text
            return self._parse_claude_response(result_text, example)
            
        except Exception as e:
            self.logger.error(f"Failed to process example with Claude: {e}")
            return self._create_fallback_result(example)
    
    def _create_processing_prompt(self, example: Dict[str, Any]) -> str:
        """Create a detailed prompt for Claude to process the example"""
        
        return f"""You are helping improve a Python code example for the PyHC (Python in Heliophysics Community) Gallery. The gallery showcases examples of how to use various heliophysics Python packages.

CURRENT EXAMPLE:
Package: {example.get('package', 'unknown')}
Title: {example.get('title', 'Untitled')}
Description: {example.get('description', 'No description')}
Category: {example.get('category', 'general')}
Source URL: {example.get('source_url', 'unknown')}

CODE:
```python
{example.get('code', '')}
```

TASK: Please improve this example to meet PyHC Gallery standards:

1. **Code Quality:**
   - Fix any syntax errors or issues
   - Improve variable names for clarity
   - Add helpful comments explaining key steps
   - Ensure imports are at the top
   - Remove unnecessary code or combine redundant sections
   - Make sure the code follows Python best practices

2. **Gallery Format:**
   - Structure should alternate between comment blocks and code blocks
   - Comment blocks start with "##############################################################################"
   - Each comment block should explain what the next code section does
   - Remove any duplicate import statements
   - Ensure compatibility with the gallery's execution environment

3. **Educational Value:**
   - Make the example easy to understand for newcomers
   - Add comments explaining domain-specific concepts
   - Include brief explanations of key functions/methods used
   - Ensure the example demonstrates something meaningful

4. **Title and Description:**
   - Create a clear, descriptive title (keep it concise)
   - Write a helpful description that explains what the example demonstrates
   - Suggest an appropriate category (maps, time_series, plotting, data_acquisition, coordinates, basic, diagnostics, general)

5. **Dependencies:**
   - Ensure all required packages are imported
   - Flag any packages that might not be commonly available

IMPORTANT CONSTRAINTS:
- Keep the core functionality of the original example
- Don't add features that weren't in the original
- Ensure the code can run independently
- Don't change the fundamental purpose of the example
- Maintain compatibility with matplotlib for any plotting

Please respond in this JSON format:
```json
{{
    "improved_title": "Clear, descriptive title here",
    "improved_description": "Helpful description explaining what this example demonstrates and why it's useful",
    "category": "appropriate_category_name",
    "improved_code": "Complete improved Python code here",
    "confidence_score": 0.85,
    "warnings": ["Any warnings about dependencies, compatibility, etc."],
    "processing_notes": "Brief notes about what changes were made"
}}
```"""
    
    def _parse_claude_response(self, response_text: str, original_example: Dict[str, Any]) -> ProcessingResult:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            result_data = json.loads(json_match.group(1))
            
            return ProcessingResult(
                improved_code=result_data.get('improved_code', original_example.get('code', '')),
                improved_title=result_data.get('improved_title', original_example.get('title', 'Untitled')),
                improved_description=result_data.get('improved_description', original_example.get('description', '')),
                category=result_data.get('category', original_example.get('category', 'general')),
                confidence_score=result_data.get('confidence_score', 0.5),
                warnings=result_data.get('warnings', []),
                processing_notes=result_data.get('processing_notes', 'Processed by Claude')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Claude response: {e}")
            return self._create_fallback_result(original_example)
    
    def _create_fallback_result(self, example: Dict[str, Any]) -> ProcessingResult:
        """Create fallback result when Claude processing fails"""
        return ProcessingResult(
            improved_code=example.get('code', ''),
            improved_title=example.get('title', 'Untitled Example'),
            improved_description=example.get('description', 'No description available'),
            category=example.get('category', 'general'),
            confidence_score=0.1,
            warnings=["LLM processing failed - using original content"],
            processing_notes="Fallback result due to processing failure"
        )


class ExampleFormatter:
    """Format processed examples for PyHC gallery"""
    
    @staticmethod
    def format_for_gallery(result: ProcessingResult, package_name: str, source_url: str) -> str:
        """Format the processed example for PyHC gallery"""
        
        # Create the gallery header
        title_line = "=" * max(len(result.improved_title) + 4, 40)
        
        header = f'''# coding: utf-8
"""
{title_line}
{result.improved_title}
{title_line}

{result.improved_description}

This example was automatically scraped from {package_name} documentation and
improved using LLM processing.

Source: {source_url}
Processing confidence: {result.confidence_score:.2f}
"""

##############################################################################
# This example demonstrates {package_name} functionality
# 
# Auto-generated and improved for the PyHC Gallery
# {result.processing_notes}

'''
        
        # Add any warnings as comments
        if result.warnings:
            header += f"# Warnings:\n"
            for warning in result.warnings:
                header += f"# - {warning}\n"
            header += "\n"
        
        return header + result.improved_code
    
    @staticmethod
    def create_metadata_file(results: List[ProcessingResult], output_path: str):
        """Create metadata file with processing information"""
        metadata = {
            "processing_date": "2024-01-01",  # Would use actual date
            "total_examples": len(results),
            "average_confidence": sum(r.confidence_score for r in results) / len(results) if results else 0,
            "categories": list(set(r.category for r in results)),
            "warnings_summary": {},
            "examples": []
        }
        
        # Collect warning statistics
        all_warnings = []
        for result in results:
            all_warnings.extend(result.warnings)
        
        warning_counts = {}
        for warning in all_warnings:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
        
        metadata["warnings_summary"] = warning_counts
        
        # Add example metadata
        for i, result in enumerate(results):
            metadata["examples"].append({
                "index": i,
                "title": result.improved_title,
                "category": result.category,
                "confidence": result.confidence_score,
                "warnings_count": len(result.warnings)
            })
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)


class BatchProcessor:
    """Process multiple examples in batch"""
    
    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 3):
        self.processor = ClaudeExampleProcessor(api_key)
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
    
    async def process_examples(self, examples: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """Process multiple examples with rate limiting"""
        results = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(examples), self.max_concurrent):
            batch = examples[i:i + self.max_concurrent]
            self.logger.info(f"Processing batch {i//self.max_concurrent + 1}/{(len(examples) + self.max_concurrent - 1)//self.max_concurrent}")
            
            # Process batch concurrently
            batch_tasks = []
            for example in batch:
                # Add delay between requests
                await asyncio.sleep(1)
                task = asyncio.create_task(self.processor.process_example(example))
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to process example: {result}")
                    # Create fallback result
                    results.append(ProcessingResult(
                        improved_code="# Error processing this example",
                        improved_title="Processing Error",
                        improved_description="This example could not be processed",
                        category="error",
                        confidence_score=0.0,
                        warnings=["Processing failed"],
                        processing_notes="Failed to process"
                    ))
                else:
                    results.append(result)
        
        return results
    
    async def save_processed_examples(self, results: List[ProcessingResult], 
                                    original_examples: List[Dict[str, Any]], 
                                    output_dir: str):
        """Save processed examples to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for i, (result, original) in enumerate(zip(results, original_examples)):
            # Create filename
            package = original.get('package', 'unknown')
            safe_title = re.sub(r'[^a-zA-Z0-9\s]', '', result.improved_title)
            safe_title = re.sub(r'\s+', '_', safe_title).lower()[:50]
            filename = f"{package}_{i+1:03d}_{safe_title}.py"
            
            # Format for gallery
            gallery_content = ExampleFormatter.format_for_gallery(
                result, 
                package, 
                original.get('source_url', 'unknown')
            )
            
            # Save file
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w') as f:
                f.write(gallery_content)
            
            self.logger.info(f"Saved processed example: {filename}")
        
        # Save metadata
        metadata_path = os.path.join(output_dir, 'processing_metadata.json')
        ExampleFormatter.create_metadata_file(results, metadata_path)
        self.logger.info(f"Saved processing metadata: {metadata_path}")


async def main():
    """Test the LLM processor"""
    # Example test data
    test_example = {
        'package': 'sunpy',
        'title': 'Solar Map Example',
        'description': 'Shows how to create a solar map',
        'category': 'maps',
        'source_url': 'https://docs.sunpy.org/example',
        'code': '''import sunpy
import matplotlib.pyplot as plt
from sunpy.net import Fido, attrs

# Download some data
result = Fido.search(attrs.Time('2023-01-01', '2023-01-02'), attrs.Instrument('AIA'))
print(result)
'''
    }
    
    processor = BatchProcessor()
    results = await processor.process_examples([test_example])
    
    print("Processing complete!")
    for result in results:
        print(f"Title: {result.improved_title}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Warnings: {result.warnings}")


if __name__ == "__main__":
    asyncio.run(main())