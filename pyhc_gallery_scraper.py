#!/usr/bin/env python3
"""
PyHC Gallery Automated Scraper

This system automatically scrapes code examples from PyHC package documentation
and converts them to the gallery format for inclusion in the PyHC gallery.
"""

import asyncio
import logging
import re
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import nbformat
from nbconvert import PythonExporter
import requests
from urllib.parse import urljoin, urlparse


@dataclass
class PackageInfo:
    """Information about a PyHC package"""
    name: str
    docs_url: str
    repo_url: str
    description: str
    doc_type: str  # 'sphinx-gallery', 'nbsphinx', 'sphinx', 'mkdocs'
    example_patterns: List[str]  # URL patterns for finding examples
    priority: int = 1  # Higher priority packages scraped first


@dataclass
class CodeExample:
    """A scraped code example"""
    title: str
    description: str
    code: str
    package: str
    source_url: str
    category: str
    dependencies: List[str]
    plots_generated: bool = False
    last_updated: str = ""


class PyHCPackageRegistry:
    """Registry of PyHC packages and their documentation patterns"""
    
    PACKAGES = [
        PackageInfo(
            name="sunpy",
            docs_url="https://docs.sunpy.org",
            repo_url="https://github.com/sunpy/sunpy",
            description="Python for Solar Physics",
            doc_type="sphinx-gallery",
            example_patterns=[
                "/en/stable/generated/gallery/*/plot_*.html",
                "/en/stable/generated/gallery/index.html"
            ],
            priority=1
        ),
        PackageInfo(
            name="plasmapy",
            docs_url="https://docs.plasmapy.org",
            repo_url="https://github.com/PlasmaPy/PlasmaPy",
            description="Plasma research and education package",
            doc_type="nbsphinx",
            example_patterns=[
                "/en/stable/notebooks/*/*.ipynb",
                "/en/stable/notebooks/*/index.html"
            ],
            priority=1
        ),
        PackageInfo(
            name="pyspedas",
            docs_url="https://pyspedas.readthedocs.io",
            repo_url="https://github.com/spedas/pyspedas",
            description="Heliophysics mission data tools",
            doc_type="sphinx",
            example_patterns=[
                "/en/latest/*.html"
            ],
            priority=2
        ),
        PackageInfo(
            name="spacepy",
            docs_url="https://spacepy.github.io",
            repo_url="https://github.com/spacepy/spacepy",
            description="Space science library",
            doc_type="sphinx",
            example_patterns=[
                "/autosummary/spacepy.*.html"
            ],
            priority=2
        ),
        PackageInfo(
            name="pysat",
            docs_url="https://pysat.readthedocs.io",
            repo_url="https://github.com/pysat/pysat",
            description="Satellite and radar data management tool",
            doc_type="sphinx",
            example_patterns=[
                "/en/latest/examples/*.html"
            ],
            priority=2
        )
    ]


class DocumentationScraper:
    """Main scraper class for extracting examples from documentation"""
    
    def __init__(self, output_dir: str = "scraped_examples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = None
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'PyHC-Gallery-Scraper/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_all_packages(self) -> List[CodeExample]:
        """Scrape examples from all registered packages"""
        all_examples = []
        
        for package in sorted(PyHCPackageRegistry.PACKAGES, key=lambda p: p.priority):
            self.logger.info(f"Scraping {package.name}...")
            try:
                examples = await self.scrape_package(package)
                all_examples.extend(examples)
                self.logger.info(f"Found {len(examples)} examples from {package.name}")
            except Exception as e:
                self.logger.error(f"Failed to scrape {package.name}: {e}")
        
        return all_examples
    
    async def scrape_package(self, package: PackageInfo) -> List[CodeExample]:
        """Scrape examples from a specific package"""
        if package.doc_type == "sphinx-gallery":
            return await self._scrape_sphinx_gallery(package)
        elif package.doc_type == "nbsphinx":
            return await self._scrape_nbsphinx(package)
        elif package.doc_type == "sphinx":
            return await self._scrape_sphinx_docs(package)
        else:
            self.logger.warning(f"Unknown doc type: {package.doc_type}")
            return []
    
    async def _scrape_sphinx_gallery(self, package: PackageInfo) -> List[CodeExample]:
        """Scrape Sphinx-Gallery style documentation (like SunPy)"""
        examples = []
        
        # First, get the gallery index to find all examples
        gallery_url = f"{package.docs_url}/en/stable/generated/gallery/index.html"
        
        try:
            async with self.session.get(gallery_url) as response:
                if response.status != 200:
                    self.logger.warning(f"Could not access gallery index: {gallery_url}")
                    return []
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all example links in the gallery
                example_links = soup.find_all('a', href=True)
                example_urls = []
                
                for link in example_links:
                    href = link.get('href', '')
                    if 'plot_' in href and href.endswith('.html'):
                        full_url = urljoin(gallery_url, href)
                        example_urls.append(full_url)
                
                # Scrape individual examples
                for url in example_urls[:10]:  # Limit for testing
                    try:
                        example = await self._extract_sphinx_gallery_example(package, url)
                        if example:
                            examples.append(example)
                    except Exception as e:
                        self.logger.error(f"Failed to extract example from {url}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to scrape gallery index: {e}")
        
        return examples
    
    async def _extract_sphinx_gallery_example(self, package: PackageInfo, url: str) -> Optional[CodeExample]:
        """Extract code example from a Sphinx-Gallery page"""
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else "Untitled Example"
            
            # Extract description (first paragraph)
            desc_elem = soup.find('p')
            description = desc_elem.text.strip() if desc_elem else ""
            
            # Extract Python code blocks
            code_blocks = soup.find_all('div', class_='highlight-python')
            if not code_blocks:
                code_blocks = soup.find_all('pre', class_='literal-block')
            
            code_parts = []
            for block in code_blocks:
                code_elem = block.find('code') or block
                if code_elem:
                    code_parts.append(code_elem.text.strip())
            
            if not code_parts:
                return None
            
            # Combine code blocks
            code = '\n\n##############################################################################\n# \n\n'.join(code_parts)
            
            # Extract dependencies from imports
            dependencies = self._extract_dependencies(code)
            
            # Determine category from URL
            category = self._extract_category_from_url(url)
            
            return CodeExample(
                title=title,
                description=description,
                code=code,
                package=package.name,
                source_url=url,
                category=category,
                dependencies=dependencies,
                plots_generated=True,  # Sphinx-Gallery typically generates plots
                last_updated=datetime.now().isoformat()
            )
    
    async def _scrape_nbsphinx(self, package: PackageInfo) -> List[CodeExample]:
        """Scrape nbsphinx documentation (like PlasmaPy)"""
        examples = []
        
        # Try to find notebook directory listing
        notebook_urls = [
            f"{package.docs_url}/en/stable/notebooks/getting_started/",
            f"{package.docs_url}/en/stable/notebooks/diagnostics/",
            f"{package.docs_url}/en/stable/notebooks/dispersion/"
        ]
        
        for base_url in notebook_urls:
            try:
                async with self.session.get(base_url) as response:
                    if response.status != 200:
                        continue
                    
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find notebook links
                    notebook_links = soup.find_all('a', href=True)
                    for link in notebook_links:
                        href = link.get('href', '')
                        if href.endswith('.html') and not href.startswith('http'):
                            notebook_url = urljoin(base_url, href)
                            try:
                                example = await self._extract_notebook_example(package, notebook_url)
                                if example:
                                    examples.append(example)
                            except Exception as e:
                                self.logger.error(f"Failed to extract notebook from {notebook_url}: {e}")
            
            except Exception as e:
                self.logger.error(f"Failed to access notebook directory {base_url}: {e}")
        
        return examples[:5]  # Limit for testing
    
    async def _extract_notebook_example(self, package: PackageInfo, url: str) -> Optional[CodeExample]:
        """Extract code example from an nbsphinx-generated page"""
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else "Untitled Notebook"
            
            # Extract description from first text paragraph
            paragraphs = soup.find_all('p')
            description = ""
            for p in paragraphs:
                if p.text.strip() and not p.text.startswith('This page was generated'):
                    description = p.text.strip()
                    break
            
            # Extract code cells
            code_blocks = soup.find_all('div', class_='highlight-python')
            if not code_blocks:
                code_blocks = soup.find_all('div', class_='input')
            
            code_parts = []
            for block in code_blocks:
                code_elem = block.find('code') or block.find('pre')
                if code_elem:
                    code_text = code_elem.text.strip()
                    if code_text and not code_text.startswith('['):  # Skip output cells
                        code_parts.append(code_text)
            
            if not code_parts:
                return None
            
            # Combine code blocks
            code = '\n\n##############################################################################\n# \n\n'.join(code_parts)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(code)
            
            # Determine category
            category = self._extract_category_from_url(url)
            
            return CodeExample(
                title=title,
                description=description,
                code=code,
                package=package.name,
                source_url=url,
                category=category,
                dependencies=dependencies,
                plots_generated=True,
                last_updated=datetime.now().isoformat()
            )
    
    async def _scrape_sphinx_docs(self, package: PackageInfo) -> List[CodeExample]:
        """Scrape regular Sphinx documentation for code examples"""
        examples = []
        
        # This is a simplified implementation - in practice, you'd need
        # more sophisticated logic for each package's specific structure
        main_page = f"{package.docs_url}/en/latest/"
        
        try:
            async with self.session.get(main_page) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for code blocks in the documentation
                code_blocks = soup.find_all('div', class_='highlight-python')
                if code_blocks:
                    # Extract a simple example from the main page
                    first_block = code_blocks[0]
                    code_elem = first_block.find('code')
                    
                    if code_elem:
                        code = code_elem.text.strip()
                        dependencies = self._extract_dependencies(code)
                        
                        example = CodeExample(
                            title=f"{package.name.title()} Basic Example",
                            description=f"Basic usage example from {package.name} documentation",
                            code=code,
                            package=package.name,
                            source_url=main_page,
                            category="basic",
                            dependencies=dependencies,
                            plots_generated=False,
                            last_updated=datetime.now().isoformat()
                        )
                        examples.append(example)
        
        except Exception as e:
            self.logger.error(f"Failed to scrape Sphinx docs for {package.name}: {e}")
        
        return examples
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract package dependencies from import statements"""
        dependencies = set()
        
        # Find import statements
        import_pattern = r'^(?:from\s+(\S+)|import\s+(\S+))'
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            match = re.match(import_pattern, line)
            if match:
                package = match.group(1) or match.group(2)
                if package:
                    # Get the top-level package name
                    base_package = package.split('.')[0]
                    dependencies.add(base_package)
        
        return sorted(list(dependencies))
    
    def _extract_category_from_url(self, url: str) -> str:
        """Extract category from URL path"""
        path = urlparse(url).path
        
        # Common category mappings
        if 'map' in path.lower():
            return 'maps'
        elif 'time' in path.lower():
            return 'time_series'
        elif 'plot' in path.lower():
            return 'plotting'
        elif 'data' in path.lower():
            return 'data_acquisition'
        elif 'coord' in path.lower():
            return 'coordinates'
        elif 'getting_started' in path.lower():
            return 'basic'
        elif 'diagnostic' in path.lower():
            return 'diagnostics'
        else:
            return 'general'
    
    async def save_examples(self, examples: List[CodeExample]):
        """Save scraped examples to files"""
        for i, example in enumerate(examples):
            filename = f"{example.package}_{i+1:03d}_{self._sanitize_filename(example.title)}.py"
            filepath = self.output_dir / filename
            
            # Generate gallery-format content
            gallery_content = self._format_for_gallery(example)
            
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(gallery_content)
            
            self.logger.info(f"Saved: {filepath}")
    
    def _sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return re.sub(r'\s+', '_', sanitized).lower()[:50]
    
    def _format_for_gallery(self, example: CodeExample) -> str:
        """Format example for PyHC gallery"""
        # Create gallery-compatible header
        title_line = "=" * max(len(example.title) + 4, 40)
        
        header = f'''# coding: utf-8
"""
{title_line}
{example.title}
{title_line}

{example.description}

This example was automatically scraped from {example.package} documentation.
Source: {example.source_url}

Dependencies: {', '.join(example.dependencies)}
"""

##############################################################################
# This example demonstrates {example.package} functionality
#
# Auto-generated from: {example.source_url}

'''
        
        # Add the actual code
        return header + example.code


class LLMExampleProcessor:
    """Process and improve scraped examples using LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    
    async def process_example(self, example: CodeExample) -> CodeExample:
        """Use LLM to improve and standardize example"""
        # This would integrate with Anthropic's API to:
        # 1. Clean up the code format
        # 2. Add better comments
        # 3. Standardize variable names
        # 4. Ensure compatibility
        # 5. Generate better descriptions
        
        # For now, return as-is
        return example


async def main():
    """Main scraping workflow"""
    async with DocumentationScraper() as scraper:
        examples = await scraper.scrape_all_packages()
        await scraper.save_examples(examples)
        
        print(f"\nScraping complete! Found {len(examples)} examples:")
        for example in examples:
            print(f"  - {example.package}: {example.title}")


if __name__ == "__main__":
    asyncio.run(main())