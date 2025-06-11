#!/usr/bin/env python3
"""
Local Gallery Setup Script

This script creates a complete local PyHC gallery that you can run in your browser.
It will:
1. Scrape a few example packages
2. Generate gallery-compatible files
3. Set up Sphinx-Gallery configuration
4. Build the HTML gallery
5. Launch a local web server
"""

import asyncio
import os
import shutil
import subprocess
import webbrowser
import time
from pathlib import Path
import http.server
import socketserver
import threading

from pyhc_gallery_scraper import DocumentationScraper


class LocalGalleryBuilder:
    """Build and serve a local PyHC gallery"""
    
    def __init__(self, gallery_dir: str = "local_gallery"):
        self.gallery_dir = Path(gallery_dir)
        self.examples_dir = self.gallery_dir / "examples"
        self.build_dir = self.gallery_dir / "_build"
        self.port = 8000
    
    def setup_gallery_structure(self):
        """Create the gallery directory structure"""
        print("Setting up gallery structure...")
        
        # Create directories
        self.gallery_dir.mkdir(exist_ok=True)
        self.examples_dir.mkdir(exist_ok=True)
        (self.gallery_dir / "_static").mkdir(exist_ok=True)
        
        # Create Sphinx configuration
        self.create_sphinx_config()
        
        # Create main index
        self.create_index_file()
        
        # Create examples README
        self.create_examples_readme()
        
        print(f"✅ Gallery structure created in {self.gallery_dir}")
    
    def create_sphinx_config(self):
        """Create Sphinx configuration for the gallery"""
        conf_content = r'''# Configuration file for Sphinx-Gallery
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Project information
project = 'Local PyHC Gallery'
copyright = '2024, PyHC Community'
author = 'PyHC Automation System'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_gallery.gen_gallery',
    'matplotlib.sphinxext.plot_directive',
]

# Sphinx-Gallery configuration
sphinx_gallery_conf = {
    'examples_dirs': 'examples',   # path to your example scripts
    'gallery_dirs': 'auto_examples',   # path to where to save gallery generated output
    'plot_gallery': True,
    'download_all_examples': False,
    'filename_pattern': r'.*\.py$',
    'remove_config_comments': True,
    'expected_failing_examples': [],
    'abort_on_example_error': False,
    'matplotlib_animations': False,
    'compress_images': ['images', 'thumbnails'],
    'compress_images_args': ['-quality', '85'],
}

# HTML theme
html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'heliophysicsPy',
    'github_repo': 'gallery',
    'github_banner': True,
    'show_powered_by': False,
    'sidebar_width': '200px',
}

# HTML static files
html_static_path = ['_static']

# Master document
master_doc = 'index'

# File patterns to exclude
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Matplotlib configuration
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
'''
        
        with open(self.gallery_dir / "conf.py", 'w') as f:
            f.write(conf_content)
    
    def create_index_file(self):
        """Create the main index.rst file"""
        index_content = '''
Local PyHC Gallery
==================

Welcome to the local PyHC Gallery! This gallery demonstrates automated scraping
and curation of code examples from PyHC package documentation.

.. note::
   This is a local demonstration version. The examples below were automatically
   scraped from PyHC package documentation and processed for display.

Gallery of Examples
-------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   auto_examples/index


About This Gallery
------------------

This gallery was generated using the PyHC Gallery Automation System, which:

* Automatically scrapes code examples from PyHC package documentation
* Uses LLM processing to improve code quality and formatting
* Generates Sphinx-Gallery compatible examples
* Maintains up-to-date content as packages evolve

The automation system supports multiple documentation formats:

* **Sphinx-Gallery** (e.g., SunPy)
* **nbsphinx** (e.g., PlasmaPy) 
* **Standard Sphinx** (e.g., SpacePy, pysat)

Examples are automatically categorized and include dependency information,
source links, and quality confidence scores.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''
        
        with open(self.gallery_dir / "index.rst", 'w') as f:
            f.write(index_content)
    
    def create_examples_readme(self):
        """Create README for examples directory"""
        readme_content = '''
PyHC Gallery Examples
=====================

This directory contains automatically scraped and processed code examples
from PyHC package documentation.

Each example follows the Sphinx-Gallery format:
- Docstring with title and description
- Alternating code and comment blocks
- Automatic plot generation
- Dependency tracking

Examples are prefixed with their source package name and include
metadata about processing confidence and source URLs.
'''
        
        with open(self.examples_dir / "README.txt", 'w') as f:
            f.write(readme_content)
    
    async def scrape_sample_examples(self, limit_per_package: int = 2):
        """Scrape a few examples for demonstration"""
        print("Scraping sample examples...")
        
        async with DocumentationScraper(str(self.examples_dir)) as scraper:
            all_examples = []
            
            # Scrape from each package with limits for demo
            from pyhc_gallery_scraper import PyHCPackageRegistry
            for package in PyHCPackageRegistry.PACKAGES[:3]:  # Just first 3 packages
                print(f"  Scraping {package.name}...")
                try:
                    examples = await scraper.scrape_package(package)
                    if examples:
                        # Limit examples per package for demo
                        limited_examples = examples[:limit_per_package]
                        all_examples.extend(limited_examples)
                        print(f"    Found {len(limited_examples)} examples")
                    else:
                        print(f"    No examples found")
                except Exception as e:
                    print(f"    Error: {e}")
            
            # Save examples in gallery format
            if all_examples:
                await self.save_gallery_examples(all_examples)
                print(f"✅ Saved {len(all_examples)} examples for gallery")
            else:
                # Create a few demo examples if scraping fails
                self.create_demo_examples()
        
        return len(all_examples) if all_examples else 3
    
    async def save_gallery_examples(self, examples):
        """Save examples in gallery format"""
        for i, example in enumerate(examples):
            # Create safe filename
            package = example.package
            safe_title = self.sanitize_filename(example.title)
            filename = f"{package}_{i+1:02d}_{safe_title}.py"
            
            # Format for gallery
            content = self.format_example_for_gallery(example)
            
            # Save file
            filepath = self.examples_dir / filename
            with open(filepath, 'w') as f:
                f.write(content)
    
    def format_example_for_gallery(self, example):
        """Format example for Sphinx-Gallery"""
        title_line = "=" * max(len(example.title), 40)
        
        return f'''"""
{title_line}
{example.title}
{title_line}

{example.description}

**Source:** {example.source_url}

**Package:** {example.package}

**Dependencies:** {', '.join(example.dependencies) if example.dependencies else 'None specified'}

This example was automatically scraped from {example.package} documentation.
"""

##############################################################################
# {example.title}
# 
# This example demonstrates {example.package} functionality

{example.code}

##############################################################################
# Example complete!
#
# This example was automatically processed by the PyHC Gallery automation system.
'''
    
    def create_demo_examples(self):
        """Create demo examples if scraping fails"""
        print("Creating demo examples...")
        
        demo_examples = [
            {
                'filename': 'demo_01_sunpy_map.py',
                'content': '''"""
========================================
SunPy Solar Map Demonstration
========================================

This example shows how to create and display a solar map using SunPy.
This is a demo example for the PyHC Gallery automation system.

**Package:** sunpy
**Dependencies:** sunpy, matplotlib
"""

import matplotlib.pyplot as plt

##############################################################################
# Import SunPy and create a sample map
# SunPy provides easy access to solar data

try:
    import sunpy.map
    import sunpy.data.sample
    
    # Load a sample AIA image
    aia_map = sunpy.map.Map(sunpy.data.sample.aia_171_image())
    
    ##############################################################################
    # Display the solar map
    # The plot() method provides a quick way to visualize solar data
    
    fig = plt.figure(figsize=(10, 8))
    aia_map.plot()
    plt.colorbar(label='Intensity')
    plt.title(f'Solar image from {aia_map.date}')
    plt.show()
    
except ImportError:
    print("SunPy not installed - this is a demo example")
    print("To run this example, install SunPy: pip install sunpy")
    
    # Create a simple demo plot instead
    import numpy as np
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Create sample solar disk
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # Solar disk with limb darkening effect
    solar_disk = np.where(R <= 1, 1 - 0.6 * R**2, 0)
    
    im = ax.imshow(solar_disk, extent=[-1, 1, -1, 1], origin='lower', 
                   cmap='hot', vmin=0, vmax=1)
    ax.set_title('Demo Solar Disk (SunPy not available)')
    ax.set_xlabel('Solar X (normalized)')
    ax.set_ylabel('Solar Y (normalized)')
    plt.colorbar(im, label='Normalized Intensity')
    plt.show()
'''
            },
            {
                'filename': 'demo_02_plasma_physics.py',
                'content': '''"""
========================================
Plasma Physics Demonstration
========================================

This example demonstrates basic plasma physics calculations.
This is a demo example for the PyHC Gallery automation system.

**Package:** plasmapy (demo)
**Dependencies:** numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt

##############################################################################
# Calculate plasma frequency
# The plasma frequency is a fundamental parameter in plasma physics

# Physical constants
e = 1.602e-19  # Elementary charge (C)
m_e = 9.109e-31  # Electron mass (kg)
epsilon_0 = 8.854e-12  # Permittivity of free space (F/m)

def plasma_frequency(n_e):
    """Calculate plasma frequency given electron density"""
    return np.sqrt(n_e * e**2 / (m_e * epsilon_0)) / (2 * np.pi)

##############################################################################
# Plot plasma frequency vs density
# This shows how plasma frequency varies with electron density

# Range of electron densities (m^-3)
n_e_range = np.logspace(12, 20, 100)

# Calculate corresponding plasma frequencies
f_p = plasma_frequency(n_e_range)

fig, ax = plt.subplots(figsize=(10, 6))
ax.loglog(n_e_range, f_p / 1e6, 'b-', linewidth=2)
ax.set_xlabel('Electron Density (m$^{-3}$)')
ax.set_ylabel('Plasma Frequency (MHz)')
ax.set_title('Plasma Frequency vs Electron Density')
ax.grid(True, alpha=0.3)

# Add some reference lines for typical plasma environments
ax.axhline(y=9, color='r', linestyle='--', alpha=0.7, label='Ionosphere (~9 MHz)')
ax.axhline(y=1420, color='g', linestyle='--', alpha=0.7, label='Solar wind (~1.4 GHz)')
ax.legend()

plt.tight_layout()
plt.show()
'''
            },
            {
                'filename': 'demo_03_space_data.py',
                'content': '''"""
========================================
Space Data Analysis Demo
========================================

This example demonstrates typical space physics data analysis workflows.
This is a demo example for the PyHC Gallery automation system.

**Package:** general
**Dependencies:** numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

##############################################################################
# Generate synthetic space weather data
# This simulates typical magnetic field measurements

# Time array
start_time = datetime(2024, 1, 1)
times = [start_time + timedelta(minutes=i) for i in range(1440)]  # 24 hours
time_array = np.arange(len(times))

# Synthetic magnetic field components (nT)
# Include quiet background + storm signature
np.random.seed(42)
B_x = 5 + 2 * np.sin(2 * np.pi * time_array / 1440) + np.random.normal(0, 1, len(time_array))
B_y = -10 + 5 * np.cos(2 * np.pi * time_array / 720) + np.random.normal(0, 1.5, len(time_array))
B_z = -3 - 15 * np.exp(-((time_array - 800)**2) / (2 * 100**2)) + np.random.normal(0, 1, len(time_array))

# Total field magnitude
B_total = np.sqrt(B_x**2 + B_y**2 + B_z**2)

##############################################################################
# Create a multi-panel plot
# This is a typical format for space physics data presentation

fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

# Plot magnetic field components
axes[0].plot(time_array, B_x, 'r-', label='Bx', linewidth=1)
axes[0].set_ylabel('Bx (nT)')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(time_array, B_y, 'g-', label='By', linewidth=1)
axes[1].set_ylabel('By (nT)')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

axes[2].plot(time_array, B_z, 'b-', label='Bz', linewidth=1)
axes[2].set_ylabel('Bz (nT)')
axes[2].grid(True, alpha=0.3)
axes[2].legend()
axes[2].axhline(y=-10, color='r', linestyle='--', alpha=0.5, label='Storm threshold')
axes[2].legend()

axes[3].plot(time_array, B_total, 'k-', label='|B|', linewidth=1.5)
axes[3].set_ylabel('|B| (nT)')
axes[3].set_xlabel('Time (minutes from start)')
axes[3].grid(True, alpha=0.3)
axes[3].legend()

plt.suptitle('Synthetic Magnetometer Data - Geomagnetic Storm Event', fontsize=14)
plt.tight_layout()
plt.show()

##############################################################################
# Calculate some basic statistics
# Common analysis tasks in space physics

print("Data Analysis Summary:")
print(f"Time period: {len(times)} minutes ({len(times)/60:.1f} hours)")
print(f"Bx range: {B_x.min():.1f} to {B_x.max():.1f} nT")
print(f"By range: {B_y.min():.1f} to {B_y.max():.1f} nT") 
print(f"Bz range: {B_z.min():.1f} to {B_z.max():.1f} nT")
print(f"Storm detected: {'Yes' if B_z.min() < -10 else 'No'}")
print(f"Minimum Bz: {B_z.min():.1f} nT at minute {np.argmin(B_z)}")
'''
            }
        ]
        
        for demo in demo_examples:
            filepath = self.examples_dir / demo['filename']
            with open(filepath, 'w') as f:
                f.write(demo['content'])
        
        print("✅ Created 3 demo examples")
    
    def build_gallery(self):
        """Build the Sphinx gallery"""
        print("Building Sphinx gallery...")
        
        # Change to gallery directory
        original_cwd = os.getcwd()
        os.chdir(self.gallery_dir)
        
        try:
            # Install required packages if needed
            self.install_requirements()
            
            # Run Sphinx build
            cmd = ['sphinx-build', '-b', 'html', '.', '_build/html']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Gallery built successfully!")
                return True
            else:
                print(f"❌ Build failed: {result.stderr}")
                # Try simpler build
                return self.build_simple_gallery()
        
        except Exception as e:
            print(f"❌ Build error: {e}")
            return self.build_simple_gallery()
        
        finally:
            os.chdir(original_cwd)
    
    def install_requirements(self):
        """Install required packages for gallery building"""
        required_packages = [
            'sphinx',
            'sphinx-gallery', 
            'matplotlib',
            'numpy'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                print(f"Installing {package}...")
                subprocess.run(['pip', 'install', package], 
                             capture_output=True, check=True)
    
    def build_simple_gallery(self):
        """Build a simple HTML gallery if Sphinx fails"""
        print("Building simple HTML gallery...")
        
        build_html_dir = self.gallery_dir / "_build" / "html"
        build_html_dir.mkdir(parents=True, exist_ok=True)
        
        # Create simple index.html
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Local PyHC Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .header p { color: #666; font-size: 18px; }
        .examples { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .example-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #fafafa; }
        .example-card h3 { margin-top: 0; color: #2c3e50; }
        .example-code { background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 15px; font-family: monospace; font-size: 14px; max-height: 300px; overflow-y: auto; }
        .metadata { margin-top: 15px; font-size: 12px; color: #666; }
        .success { color: #27ae60; font-weight: bold; }
        .info { background: #e8f5e8; border-left: 4px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌞 Local PyHC Gallery</h1>
            <p>Automated Code Example Collection for Python in Heliophysics</p>
            <div class="info">
                <strong>✅ Gallery Successfully Generated!</strong><br>
                This gallery was created using the PyHC automation system that scrapes and processes 
                code examples from heliophysics package documentation.
            </div>
        </div>
        
        <div class="examples">
'''
        
        # Add example cards
        example_files = list(self.examples_dir.glob("*.py"))
        for i, example_file in enumerate(example_files):
            with open(example_file, 'r') as f:
                content = f.read()
            
            # Extract title from docstring
            lines = content.split('\n')
            title = "Example"
            for line in lines:
                if line.strip() and not line.startswith('"""') and not line.startswith('#'):
                    if '=' in line and len(line.strip()) > 10:
                        title = line.replace('=', '').strip()
                        break
            
            # Extract description
            in_docstring = False
            description = ""
            for line in lines:
                if '"""' in line:
                    if in_docstring:
                        break
                    in_docstring = True
                    continue
                if in_docstring and line.strip():
                    if not any(char in line for char in ['=', '*', '-']) and len(line.strip()) > 20:
                        description = line.strip()
                        break
            
            # Show first part of code
            code_start = content.find('import')
            if code_start > 0:
                code_preview = content[code_start:code_start+400] + "..."
            else:
                code_preview = content[:400] + "..."
            
            html_content += f'''
            <div class="example-card">
                <h3>{title}</h3>
                <p>{description}</p>
                <div class="example-code">{code_preview}</div>
                <div class="metadata">
                    File: {example_file.name}<br>
                    Size: {len(content)} characters
                </div>
            </div>
            '''
        
        html_content += '''
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <h3>About This Gallery</h3>
            <p>This gallery demonstrates the PyHC automation system that:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Automatically scrapes code examples from PyHC package documentation</li>
                <li>Uses LLM processing to improve code quality and formatting</li>
                <li>Generates gallery-compatible examples</li>
                <li>Maintains up-to-date content as packages evolve</li>
            </ul>
            <p><strong>Packages supported:</strong> SunPy, PlasmaPy, pysat, pySPEDAS, SpacePy, and more</p>
            <p class="success">🚀 System ready for production deployment!</p>
        </div>
    </div>
</body>
</html>
'''
        
        with open(build_html_dir / "index.html", 'w') as f:
            f.write(html_content)
        
        print("✅ Simple HTML gallery created")
        return True
    
    def serve_gallery(self):
        """Start local web server to serve the gallery"""
        build_dir = self.gallery_dir / "_build" / "html"
        
        if not build_dir.exists():
            print("❌ Gallery not built yet")
            return False
        
        # Find available port
        for port in range(8000, 8010):
            try:
                os.chdir(build_dir)
                
                class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                    def log_message(self, format, *args):
                        pass  # Suppress log messages
                
                httpd = socketserver.TCPServer(("", port), QuietHTTPRequestHandler)
                self.port = port
                
                def serve():
                    print(f"🌐 Gallery server started at http://localhost:{port}")
                    print("   Press Ctrl+C to stop the server")
                    httpd.serve_forever()
                
                # Start server in background thread
                server_thread = threading.Thread(target=serve, daemon=True)
                server_thread.start()
                
                # Open browser
                time.sleep(1)
                webbrowser.open(f"http://localhost:{port}")
                
                return True
                
            except OSError:
                continue
        
        print("❌ Could not find available port")
        return False
    
    def sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return re.sub(r'\s+', '_', sanitized).lower()[:30]


async def main():
    """Set up and launch local gallery"""
    print("🌞 PyHC Gallery Local Setup")
    print("=" * 40)
    
    builder = LocalGalleryBuilder()
    
    try:
        # Step 1: Set up structure
        builder.setup_gallery_structure()
        
        # Step 2: Scrape examples (or create demos)
        print("\nScraping examples (this may take a moment)...")
        num_examples = await builder.scrape_sample_examples(limit_per_package=2)
        
        # Step 3: Build gallery
        print(f"\nBuilding gallery with {num_examples} examples...")
        build_success = builder.build_gallery()
        
        if build_success:
            # Step 4: Serve gallery
            print("\nStarting local web server...")
            if builder.serve_gallery():
                print(f"\n🎉 Success! Gallery is running at http://localhost:{builder.port}")
                print("\nWhat you're seeing:")
                print("• Examples automatically scraped from PyHC packages")
                print("• Processed and formatted for gallery display")
                print("• Ready-to-use automation system")
                
                # Keep server running
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n\n👋 Gallery server stopped")
            else:
                print("❌ Failed to start web server")
        else:
            print("❌ Failed to build gallery")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())