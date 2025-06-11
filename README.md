# PyHC Gallery Automation System

An automated system for scraping, processing, and curating code examples from PyHC (Python in Heliophysics Community) package documentation to keep the PyHC Gallery up-to-date.

## Problem Statement

The current PyHC Gallery (https://heliopython.org/gallery/) has very few examples because:
- Package developers must manually create examples in a specific format
- Examples become outdated when packages change their APIs
- No systematic way to discover new examples from package documentation
- Manual maintenance is time-consuming and inconsistent

## Solution

This automated system:
1. **Scrapes** code examples from PyHC package documentation (SunPy, PlasmaPy, etc.)
2. **Processes** examples using LLM (Claude) to improve quality and format
3. **Generates** gallery-compatible Python files
4. **Automates** weekly updates via scheduled workflow

## System Architecture

### Components

1. **`pyhc_gallery_scraper.py`** - Main scraping engine
   - Handles different documentation types (Sphinx-Gallery, nbsphinx, Sphinx)
   - Extracts code examples from HTML pages and notebooks
   - Supports multiple PyHC packages with custom parsing logic

2. **`llm_processor.py`** - LLM-powered example improvement
   - Uses Claude API to clean up and standardize code
   - Improves comments, variable names, and structure
   - Ensures compatibility with gallery format

3. **`automation_workflow.py`** - Complete automation workflow
   - Orchestrates scraping → processing → PR creation
   - Handles git operations and repository management
   - Generates summary reports

### Supported Documentation Types

- **Sphinx-Gallery** (e.g., SunPy): Extracts from generated gallery pages
- **nbsphinx** (e.g., PlasmaPy): Processes Jupyter notebook documentation
- **Sphinx** (e.g., SpacePy, pysat): Parses standard Sphinx documentation

## Installation

```bash
git clone <repository-url>
cd pyhc-gallery-automation
pip install -r requirements.txt
```

### Optional: LLM Processing
For LLM-powered example improvement:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Quick Test & Demo
```bash
# View the beautiful demo in your browser
python simple_demo.py

# Run system functionality tests
python test_scraper.py
```

### Manual Scraping
```bash
python -c "
import asyncio
from pyhc_gallery_scraper import DocumentationScraper

async def main():
    async with DocumentationScraper() as scraper:
        examples = await scraper.scrape_all_packages()
        await scraper.save_examples(examples)

asyncio.run(main())
"
```

### Full Automation Workflow
```bash
# Dry run (no PR creation)
python automation_workflow.py --dry-run

# Full run with PR creation
python automation_workflow.py

# Force run (ignore weekly schedule)
python automation_workflow.py --force
```

## Configuration

### Adding New Packages

Edit `PyHCPackageRegistry.PACKAGES` in `pyhc_gallery_scraper.py`:

```python
PackageInfo(
    name="new_package",
    docs_url="https://new-package.readthedocs.io",
    repo_url="https://github.com/org/new-package",
    description="Description of package",
    doc_type="sphinx-gallery",  # or "nbsphinx", "sphinx"
    example_patterns=[
        "/en/stable/gallery/*/plot_*.html"
    ],
    priority=1  # Higher = scraped first
)
```

### Customizing LLM Processing

Modify the prompt in `llm_processor.py` `_create_processing_prompt()` method to adjust how Claude processes examples.

## Example Output

The system generates gallery-compatible Python files like:

```python
# coding: utf-8
"""
========================================
Basic Solar Data Visualization
========================================

This example shows how to load and visualize solar data using SunPy.

This example was automatically scraped from sunpy documentation and
improved using LLM processing.

Source: https://docs.sunpy.org/en/stable/generated/gallery/map/plot_example.html
Processing confidence: 0.85
"""

##############################################################################
# This example demonstrates sunpy functionality
# 
# Auto-generated and improved for the PyHC Gallery

import sunpy.map
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
```

## Automation Schedule

The system is designed to run weekly:
- Checks for new/updated documentation
- Processes examples with confidence scoring
- Only creates PR if significant changes detected
- Maintains processing metadata and reports

## Package Support

### Currently Supported:
- **SunPy** - Full Sphinx-Gallery support
- **PlasmaPy** - Jupyter notebook extraction  
- **pysat** - Basic Sphinx documentation
- **pySPEDAS** - Code block extraction
- **SpacePy** - Module documentation parsing

### Easy to Add:
Any package with online documentation can be added by:
1. Adding package info to registry
2. Customizing URL patterns
3. Testing with sample scraping

## Quality Control

### LLM Processing Features:
- Code syntax validation
- Comment improvement  
- Variable name standardization
- Gallery format compliance
- Dependency extraction
- Confidence scoring

### Filtering Criteria:
- Minimum confidence score (>0.7)
- New package coverage priority
- Duplicate detection
- Error handling

## Development

### Running Tests
```bash
python test_scraper.py
```

### Code Style
```bash
pip install black flake8
black *.py
flake8 *.py
```

### Adding New Documentation Parsers

1. Create parser method in `DocumentationScraper`
2. Add doc_type to `PackageInfo`
3. Update `scrape_package()` dispatcher
4. Test with sample package

## Deployment

### GitHub Actions (Recommended)
```yaml
name: Weekly Gallery Update
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM UTC
  workflow_dispatch:

jobs:
  update-gallery:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run automation
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python automation_workflow.py
```

### Local Cron
```bash
# Add to crontab for weekly Monday runs
0 9 * * 1 cd /path/to/pyhc-gallery-automation && python automation_workflow.py
```

## Monitoring

The system generates:
- **Processing logs** - Detailed execution information
- **Summary reports** - JSON metadata about each run  
- **Confidence metrics** - Quality scores for generated examples
- **Error tracking** - Failed scraping attempts and warnings

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure existing tests pass
5. Submit pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- PyHC Community for package ecosystem
- Anthropic for Claude API
- Sphinx-Gallery for documentation inspiration