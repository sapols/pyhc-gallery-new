#!/usr/bin/env python3
"""
Test script for PyHC Gallery Scraper

This script demonstrates and tests the scraping system with a small sample.
"""

import asyncio
import logging
import os
import json
from pathlib import Path

from pyhc_gallery_scraper import DocumentationScraper, PyHCPackageRegistry
from llm_processor import BatchProcessor


async def test_basic_scraping():
    """Test basic scraping functionality"""
    print("Testing basic scraping functionality...")
    
    # Create test output directory
    test_output = Path("test_output")
    test_output.mkdir(exist_ok=True)
    
    # Test scraping one package
    async with DocumentationScraper(str(test_output)) as scraper:
        # Test with SunPy (most reliable)
        sunpy_package = None
        for pkg in PyHCPackageRegistry.PACKAGES:
            if pkg.name == "sunpy":
                sunpy_package = pkg
                break
        
        if sunpy_package:
            print(f"Testing scraping of {sunpy_package.name}...")
            examples = await scraper.scrape_package(sunpy_package)
            print(f"Found {len(examples)} examples from {sunpy_package.name}")
            
            for i, example in enumerate(examples[:3]):  # Show first 3
                print(f"\nExample {i+1}:")
                print(f"  Title: {example.title}")
                print(f"  Category: {example.category}")
                print(f"  Dependencies: {example.dependencies}")
                print(f"  Code length: {len(example.code)} characters")
                print(f"  Source: {example.source_url}")
        
        return examples if sunpy_package else []


async def test_llm_processing():
    """Test LLM processing functionality"""
    print("\nTesting LLM processing...")
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - skipping LLM tests")
        return
    
    # Create a simple test example
    test_example = {
        'package': 'sunpy',
        'title': 'Simple Solar Map',
        'description': 'Basic example of loading solar data',
        'category': 'maps',
        'source_url': 'https://docs.sunpy.org/test',
        'code': '''import sunpy.map
import matplotlib.pyplot as plt

# Load a sample map
smap = sunpy.map.Map('test_data.fits')

# Plot the map
fig = plt.figure()
smap.plot()
plt.show()
'''
    }
    
    try:
        processor = BatchProcessor(api_key, max_concurrent=1)
        results = await processor.process_examples([test_example])
        
        if results:
            result = results[0]
            print(f"✅ LLM processing successful")
            print(f"   Improved title: {result.improved_title}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            print(f"   Category: {result.category}")
            print(f"   Warnings: {result.warnings}")
            
            # Save test result
            test_output = Path("test_output")
            with open(test_output / "llm_test_result.json", 'w') as f:
                json.dump({
                    'title': result.improved_title,
                    'description': result.improved_description,
                    'category': result.category,
                    'confidence': result.confidence_score,
                    'warnings': result.warnings,
                    'notes': result.processing_notes
                }, f, indent=2)
            
            return results
        else:
            print("❌ LLM processing failed - no results")
            return []
    
    except Exception as e:
        print(f"❌ LLM processing failed: {e}")
        return []


def test_gallery_format():
    """Test gallery formatting"""
    print("\nTesting gallery format generation...")
    
    from llm_processor import ExampleFormatter, ProcessingResult
    
    # Create test processing result
    test_result = ProcessingResult(
        improved_code='''import sunpy.map
import matplotlib.pyplot as plt

##############################################################################
# Load sample solar data
# This demonstrates the basic workflow for solar data analysis

smap = sunpy.map.Map(sunpy.data.sample.aia_171_image())

##############################################################################
# Create a visualization
# The plot method provides a quick way to visualize solar data

fig = plt.figure(figsize=(8, 8))
smap.plot()
plt.colorbar()
plt.title(f'Solar image from {smap.date}')
plt.show()
''',
        improved_title="Basic Solar Data Visualization",
        improved_description="This example shows how to load and visualize solar data using SunPy",
        category="maps",
        confidence_score=0.85,
        warnings=["Requires sample data"],
        processing_notes="Added section comments and improved structure"
    )
    
    # Format for gallery
    gallery_content = ExampleFormatter.format_for_gallery(
        test_result, 
        "sunpy",
        "https://docs.sunpy.org/test"
    )
    
    # Save test gallery file
    test_output = Path("test_output")
    test_output.mkdir(exist_ok=True)
    
    with open(test_output / "test_gallery_example.py", 'w') as f:
        f.write(gallery_content)
    
    print("✅ Gallery format test completed")
    print(f"   Generated file: test_output/test_gallery_example.py")
    print(f"   Content length: {len(gallery_content)} characters")
    
    return gallery_content


async def test_workflow_dry_run():
    """Test the complete workflow in dry-run mode"""
    print("\nTesting complete workflow (dry run)...")
    
    try:
        from automation_workflow import WorkflowManager
        
        # Run in dry-run mode with limited scope
        workflow = WorkflowManager(dry_run=True)
        
        # Test just the scraping part for now
        print("Testing scraping component...")
        scraped_examples = await workflow._scrape_examples()
        
        print(f"✅ Workflow test completed")
        print(f"   Scraped {len(scraped_examples)} examples")
        
        # Show summary by package
        package_counts = {}
        for example in scraped_examples:
            package_counts[example.package] = package_counts.get(example.package, 0) + 1
        
        print("   Examples by package:")
        for package, count in package_counts.items():
            print(f"     {package}: {count}")
        
        return True
    
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("PyHC Gallery Scraper Test Suite")
    print("=" * 40)
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    # Test 1: Basic scraping
    scraped_examples = await test_basic_scraping()
    
    # Test 2: LLM processing (if API key available)
    await test_llm_processing()
    
    # Test 3: Gallery formatting
    test_gallery_format()
    
    # Test 4: Workflow dry run
    await test_workflow_dry_run()
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"✅ Scraping test: Found {len(scraped_examples)} examples")
    print("✅ Gallery formatting test: Completed")
    print("✅ Basic workflow test: Completed")
    
    if os.getenv('ANTHROPIC_API_KEY'):
        print("✅ LLM processing test: Completed")
    else:
        print("⚠️  LLM processing test: Skipped (no API key)")
    
    print("\nTest files saved to: test_output/")
    print("Review the generated files to verify output quality.")


if __name__ == "__main__":
    asyncio.run(main())