# Configuration file for Sphinx-Gallery
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
