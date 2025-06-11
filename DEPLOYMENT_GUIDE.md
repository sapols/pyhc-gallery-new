# PyHC Gallery Automation - Deployment Guide

## 🎉 System Complete!

Your automated PyHC Gallery system is now fully implemented and ready for deployment. The demo is currently running in your browser at `http://localhost:8000`.

## 📁 System Files Created

### Core Components
- **`pyhc_gallery_scraper.py`** - Main scraping engine (supports SunPy, PlasmaPy, etc.)
- **`llm_processor.py`** - LLM-powered code improvement using Claude
- **`automation_workflow.py`** - Complete weekly automation workflow
- **`requirements.txt`** - Python dependencies

### Testing & Demo
- **`test_scraper.py`** - Comprehensive testing suite
- **`simple_demo.py`** - Browser demo (currently running)
- **`local_gallery_setup.py`** - Full local gallery builder

### Documentation
- **`README.md`** - Complete documentation
- **`setup.py`** - Package installation script
- **`DEPLOYMENT_GUIDE.md`** - This file

## 🚀 Next Steps for Production Deployment

### 1. Environment Setup
```bash
# Set up API key for LLM processing
export ANTHROPIC_API_KEY="your-api-key-here"

# Install dependencies
pip install -r requirements.txt
```

### 2. Test the System
```bash
# Run basic functionality test
python test_scraper.py

# Test full workflow (dry run)
python automation_workflow.py --dry-run
```

### 3. GitHub Actions Setup
Create `.github/workflows/gallery-update.yml`:

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

### 4. GitHub Secrets Configuration
Add these secrets to your GitHub repository:
- `ANTHROPIC_API_KEY` - Your Claude API key
- `GITHUB_TOKEN` - For creating pull requests (automatically available)

### 5. Initial Deployment
```bash
# Clone the gallery repository
git clone https://github.com/heliophysicsPy/gallery.git

# Run first automation
python automation_workflow.py --force
```

## 🔧 Configuration Options

### Adding New Packages
Edit `PyHCPackageRegistry.PACKAGES` in `pyhc_gallery_scraper.py`:

```python
PackageInfo(
    name="new_package",
    docs_url="https://new-package.readthedocs.io",
    repo_url="https://github.com/org/new-package", 
    description="Package description",
    doc_type="sphinx-gallery",  # or "nbsphinx", "sphinx"
    example_patterns=["/en/stable/gallery/*/plot_*.html"],
    priority=1
)
```

### Customizing LLM Processing
Modify the prompt in `llm_processor.py` `_create_processing_prompt()` to adjust how Claude processes examples.

### Workflow Scheduling
- Default: Weekly on Mondays
- Modify cron schedule in GitHub Actions
- Run manually: `python automation_workflow.py --force`

## 📊 Expected Results

### Before Automation
- ~8 manually created examples
- Infrequent updates
- Package developers must create examples manually
- Examples become outdated

### After Automation  
- **50+ automatically curated examples**
- **Weekly updates** as packages evolve
- **High-quality code** improved by LLM
- **Zero maintenance** for package developers

## 🔍 Monitoring & Quality Control

### Automatic Quality Features
- **Confidence scoring** - Only high-quality examples included
- **Dependency detection** - Automatic requirements management
- **Duplicate filtering** - Prevents redundant examples
- **Error handling** - Robust failure recovery

### Manual Review
- All changes come via pull requests
- LLM processing notes included
- Confidence scores provided
- Source URLs maintained for verification

## 🐛 Troubleshooting

### Common Issues

**"No examples found"**
- Check package documentation URL is accessible
- Verify doc_type matches package structure
- Review example_patterns for correct paths

**"LLM processing failed"**
- Verify ANTHROPIC_API_KEY is set
- Check API rate limits
- Fallback to original content if processing fails

**"Build errors"**
- Ensure all dependencies in requirements.txt
- Check Sphinx-Gallery configuration
- Review generated code syntax

### Debugging Commands
```bash
# Test specific package
python -c "
import asyncio
from pyhc_gallery_scraper import DocumentationScraper, PyHCPackageRegistry

async def test():
    async with DocumentationScraper() as scraper:
        package = PyHCPackageRegistry.PACKAGES[0]  # SunPy
        examples = await scraper.scrape_package(package)
        print(f'Found {len(examples)} examples')
        
asyncio.run(test())
"

# Test LLM processing
python -c "
import asyncio
from llm_processor import BatchProcessor

async def test():
    processor = BatchProcessor()
    result = await processor.process_examples([{
        'package': 'test', 'title': 'Test', 'description': 'Test',
        'category': 'test', 'source_url': 'test', 'code': 'print(\"hello\")'
    }])
    print(f'Processing result: {result[0].confidence_score}')
    
asyncio.run(test())
"
```

## 📈 Success Metrics

Track these metrics to measure system success:
- **Number of examples** in gallery (target: 50+)
- **Update frequency** (target: weekly)
- **Package coverage** (target: all major PyHC packages)
- **Community engagement** (downloads, usage)

## 🎯 Future Enhancements

### Phase 2 Features
- **Interactive examples** with Binder integration
- **Example categorization** by difficulty level
- **Multi-language support** (R, Julia, etc.)
- **Tutorial generation** from example sequences

### Community Features
- **User-requested examples** via GitHub issues
- **Quality voting system** for community feedback
- **Package recommendation** based on usage patterns

## ✅ Deployment Checklist

- [ ] API keys configured
- [ ] Dependencies installed
- [ ] Test suite passes
- [ ] GitHub Actions workflow created
- [ ] Repository secrets added
- [ ] Initial run completed successfully
- [ ] Gallery builds and displays correctly
- [ ] Weekly automation scheduled
- [ ] Monitoring/alerting configured

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `pyhc_gallery_automation.log`
3. Run tests with `python test_scraper.py`
4. Open an issue in the PyHC gallery repository

---

**🎉 Congratulations! Your PyHC Gallery automation system is ready to revolutionize the community's access to code examples.**