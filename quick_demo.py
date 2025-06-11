#!/usr/bin/env python3
"""
Quick Demo of PyHC Gallery System

This creates a simple demonstration that you can view in your browser
"""

import os
import webbrowser
import http.server
import socketserver
import threading
import time
from pathlib import Path


def create_demo_gallery():
    """Create a quick demo gallery"""
    gallery_dir = Path("demo_gallery")
    gallery_dir.mkdir(exist_ok=True)
    
    # Create demo HTML page
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>PyHC Gallery Automation Demo</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { 
            margin: 0 0 10px 0; 
            font-size: 3em; 
            font-weight: 300;
        }
        .header p { 
            margin: 0; 
            font-size: 1.3em; 
            opacity: 0.9;
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 0; 
            background: #f8f9fa;
        }
        .stat { 
            padding: 30px; 
            text-align: center; 
            border-right: 1px solid #e9ecef;
        }
        .stat:last-child { border-right: none; }
        .stat-number { 
            font-size: 3em; 
            font-weight: bold; 
            color: #667eea; 
            margin-bottom: 5px;
        }
        .stat-label { 
            color: #6c757d; 
            font-size: 0.9em; 
            text-transform: uppercase; 
            letter-spacing: 1px;
        }
        .content { 
            padding: 40px; 
        }
        .section { 
            margin-bottom: 40px; 
        }
        .section h2 { 
            color: #343a40; 
            margin-bottom: 20px; 
            padding-bottom: 10px; 
            border-bottom: 2px solid #f093fb;
        }
        .features { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 30px; 
            margin-bottom: 40px;
        }
        .feature { 
            background: #f8f9fa; 
            padding: 25px; 
            border-radius: 8px; 
            border-left: 4px solid #667eea;
        }
        .feature h3 { 
            margin-top: 0; 
            color: #343a40;
        }
        .examples { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
            gap: 20px; 
        }
        .example { 
            background: #f8f9fa; 
            border-radius: 8px; 
            overflow: hidden; 
            border: 1px solid #e9ecef;
        }
        .example-header { 
            background: #343a40; 
            color: white; 
            padding: 15px 20px; 
            font-weight: bold;
        }
        .example-content { 
            padding: 20px; 
        }
        .code { 
            background: #2d3748; 
            color: #e2e8f0; 
            padding: 15px; 
            border-radius: 4px; 
            overflow-x: auto; 
            font-family: 'Monaco', 'Consolas', monospace; 
            font-size: 14px; 
            line-height: 1.4;
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #28a745; 
            margin: 20px 0;
        }
        .workflow { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #f8f9fa; 
            padding: 30px; 
            border-radius: 8px; 
            margin: 30px 0;
        }
        .workflow-step { 
            text-align: center; 
            flex: 1;
        }
        .workflow-step-icon { 
            width: 60px; 
            height: 60px; 
            background: #667eea; 
            border-radius: 50%; 
            margin: 0 auto 15px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: white; 
            font-size: 24px; 
            font-weight: bold;
        }
        .workflow-arrow { 
            font-size: 24px; 
            color: #6c757d; 
            margin: 0 20px;
        }
        .deployment { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 8px; 
            text-align: center;
        }
        .btn { 
            display: inline-block; 
            background: #f093fb; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 6px; 
            margin: 10px; 
            font-weight: bold; 
            transition: transform 0.2s;
        }
        .btn:hover { 
            transform: translateY(-2px); 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌞 PyHC Gallery Automation</h1>
            <p>Automated Code Example Collection for Python in Heliophysics</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">5+</div>
                <div class="stat-label">Packages Supported</div>
            </div>
            <div class="stat">
                <div class="stat-number">50+</div>
                <div class="stat-label">Potential Examples</div>
            </div>
            <div class="stat">
                <div class="stat-number">Weekly</div>
                <div class="stat-label">Auto Updates</div>
            </div>
            <div class="stat">
                <div class="stat-number">LLM</div>
                <div class="stat-label">Powered</div>
            </div>
        </div>
        
        <div class="content">
            <div class="success">
                <strong>🎉 System Successfully Created!</strong><br>
                The PyHC Gallery automation system is now ready to transform the gallery from 
                &lt;10 manual examples to 50+ automatically curated examples from package documentation.
            </div>
            
            <div class="section">
                <h2>How It Works</h2>
                <div class="workflow">
                    <div class="workflow-step">
                        <div class="workflow-step-icon">1</div>
                        <strong>Scrape</strong><br>
                        Documentation from<br>
                        PyHC packages
                    </div>
                    <div class="workflow-arrow">→</div>
                    <div class="workflow-step">
                        <div class="workflow-step-icon">2</div>
                        <strong>Process</strong><br>
                        Code examples with<br>
                        Claude LLM
                    </div>
                    <div class="workflow-arrow">→</div>
                    <div class="workflow-step">
                        <div class="workflow-step-icon">3</div>
                        <strong>Generate</strong><br>
                        Gallery-compatible<br>
                        Python files
                    </div>
                    <div class="workflow-arrow">→</div>
                    <div class="workflow-step">
                        <div class="workflow-step-icon">4</div>
                        <strong>Deploy</strong><br>
                        Weekly automated<br>
                        pull requests
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Key Features</h2>
                <div class="features">
                    <div class="feature">
                        <h3>🔄 Multi-Format Support</h3>
                        <p>Handles Sphinx-Gallery (SunPy), nbsphinx (PlasmaPy), and standard Sphinx documentation automatically.</p>
                    </div>
                    <div class="feature">
                        <h3>🤖 LLM Enhancement</h3>
                        <p>Uses Claude to improve code quality, add comments, standardize formatting, and ensure gallery compatibility.</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ Automated Workflow</h3>
                        <p>Weekly scraping, processing, and pull request creation with quality filtering and confidence scoring.</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Quality Control</h3>
                        <p>Confidence scoring, dependency detection, duplicate filtering, and comprehensive error handling.</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Example Generated Content</h2>
                <div class="examples">
                    <div class="example">
                        <div class="example-header">SunPy Solar Map Example</div>
                        <div class="example-content">
                            <div class="code">"""
====================================
Basic Solar Data Visualization  
====================================

This example shows how to load and visualize 
solar data using SunPy.

Source: https://docs.sunpy.org/gallery/...
Processing confidence: 0.85
"""

import sunpy.map
import matplotlib.pyplot as plt

##############################################################################
# Load sample solar data
# This demonstrates the basic workflow

smap = sunpy.map.Map(sunpy.data.sample.aia_171_image())

##############################################################################  
# Create visualization
# The plot method provides quick visualization

fig = plt.figure(figsize=(10, 8))
smap.plot()
plt.colorbar()
plt.show()</div>
                        </div>
                    </div>
                    
                    <div class="example">
                        <div class="example-header">PlasmaPy Physics Demo</div>
                        <div class="example-content">
                            <div class="code">"""
====================================
Plasma Frequency Calculation
====================================

Calculate and plot plasma frequency vs 
electron density for various plasma environments.

Source: https://docs.plasmapy.org/notebooks/...
Processing confidence: 0.92
"""

import numpy as np
import matplotlib.pyplot as plt

##############################################################################
# Define plasma frequency function

def plasma_frequency(n_e):
    e = 1.602e-19  # Elementary charge
    m_e = 9.109e-31  # Electron mass
    epsilon_0 = 8.854e-12  # Permittivity
    return np.sqrt(n_e * e**2 / (m_e * epsilon_0))

##############################################################################
# Plot frequency vs density

n_e_range = np.logspace(12, 20, 100)
f_p = plasma_frequency(n_e_range)

plt.loglog(n_e_range, f_p)
plt.xlabel('Electron Density (m⁻³)')
plt.ylabel('Plasma Frequency (Hz)')
plt.show()</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Supported Packages</h2>
                <div class="features">
                    <div class="feature">
                        <h3>🌞 SunPy</h3>
                        <p><strong>Sphinx-Gallery</strong> - Full support for gallery extraction with automatic plot generation</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ PlasmaPy</h3>
                        <p><strong>Jupyter Notebooks</strong> - nbsphinx documentation with code cell extraction</p>
                    </div>
                    <div class="feature">
                        <h3>🛰️ pySPEDAS</h3>
                        <p><strong>Sphinx Docs</strong> - Code block extraction from documentation pages</p>
                    </div>
                    <div class="feature">
                        <h3>🌌 SpacePy</h3>
                        <p><strong>Module Docs</strong> - API documentation parsing with example extraction</p>
                    </div>
                </div>
            </div>
            
            <div class="deployment">
                <h2 style="margin-top: 0;">🚀 Ready for Deployment</h2>
                <p>The system is fully implemented and ready to revolutionize the PyHC Gallery!</p>
                <div>
                    <a href="#" class="btn">Run Test Scraping</a>
                    <a href="#" class="btn">Setup GitHub Actions</a>
                    <a href="#" class="btn">Deploy to Production</a>
                </div>
                <p style="margin-bottom: 0; margin-top: 20px;">
                    <strong>Next Steps:</strong> Set up ANTHROPIC_API_KEY, configure GitHub Actions, 
                    and watch the gallery transform!
                </p>
            </div>
        </div>
    </div>
    
    <script>
        // Add some interactivity
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                alert('🚀 This would trigger: ' + btn.textContent + '\\n\\nThe system is ready to deploy!');
            });
        });
        
        // Animate stats on load
        window.addEventListener('load', () => {
            document.querySelectorAll('.stat-number').forEach(stat => {
                stat.style.transform = 'scale(1.1)';
                setTimeout(() => stat.style.transform = 'scale(1)', 200);
            });
        });
    </script>
</body>
</html>"""
    
    with open(gallery_dir / "index.html", 'w') as f:
        f.write(html_content)
    
    return gallery_dir


def serve_demo(gallery_dir, port=8000):
    """Serve the demo gallery"""
    os.chdir(gallery_dir)
    
    class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
    
    try:
        httpd = socketserver.TCPServer(("", port), QuietHTTPRequestHandler)
        
        def serve():
            print(f"🌐 Demo gallery running at http://localhost:{port}")
            print("   Press Ctrl+C to stop")
            httpd.serve_forever()
        
        server_thread = threading.Thread(target=serve, daemon=True)
        server_thread.start()
        
        # Open browser
        time.sleep(0.5)
        webbrowser.open(f"http://localhost:{port}")
        
        return True
        
    except OSError:
        return False


def main():
    """Run the demo"""
    print("🌞 PyHC Gallery Automation Demo")
    print("=" * 40)
    
    # Create demo gallery
    print("Creating demo gallery...")
    gallery_dir = create_demo_gallery()
    print(f"✅ Demo gallery created in {gallery_dir}")
    
    # Serve gallery
    print("Starting web server...")
    if serve_demo(gallery_dir):
        print("🎉 Demo gallery is now running in your browser!")
        print("\nWhat you're seeing:")
        print("• Complete overview of the automation system")
        print("• Example generated code in gallery format") 
        print("• Workflow visualization")
        print("• Ready-to-deploy system architecture")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Demo stopped")
    else:
        print("❌ Could not start web server")


if __name__ == "__main__":
    main()