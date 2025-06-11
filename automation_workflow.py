#!/usr/bin/env python3
"""
Weekly automation workflow for PyHC Gallery

This module coordinates the complete workflow:
1. Scrape examples from PyHC package documentation
2. Process examples with LLM for quality improvement  
3. Generate gallery-compatible files
4. Create pull request with updates
"""

import os
import asyncio
import logging
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import tempfile

from pyhc_gallery_scraper import DocumentationScraper, CodeExample
from llm_processor import BatchProcessor, ProcessingResult


class GitHubIntegration:
    """Handle GitHub repository operations"""
    
    def __init__(self, repo_url: str = "https://github.com/heliophysicsPy/gallery.git"):
        self.repo_url = repo_url
        self.logger = logging.getLogger(__name__)
    
    def clone_gallery_repo(self, target_dir: str) -> bool:
        """Clone the gallery repository"""
        try:
            cmd = ['git', 'clone', self.repo_url, target_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully cloned repository to {target_dir}")
                return True
            else:
                self.logger.error(f"Failed to clone repository: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Exception during git clone: {e}")
            return False
    
    def create_update_branch(self, repo_dir: str, branch_name: str) -> bool:
        """Create a new branch for updates"""
        try:
            # Change to repo directory
            original_cwd = os.getcwd()
            os.chdir(repo_dir)
            
            # Create and checkout new branch
            cmd = ['git', 'checkout', '-b', branch_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Return to original directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                self.logger.info(f"Created branch: {branch_name}")
                return True
            else:
                self.logger.error(f"Failed to create branch: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Exception creating branch: {e}")
            return False
    
    def commit_changes(self, repo_dir: str, message: str) -> bool:
        """Commit changes to the repository"""
        try:
            original_cwd = os.getcwd()
            os.chdir(repo_dir)
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit changes
            cmd = ['git', 'commit', '-m', message]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                self.logger.info("Successfully committed changes")
                return True
            else:
                self.logger.warning(f"Commit failed or no changes: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Exception during commit: {e}")
            return False


class WorkflowManager:
    """Main workflow manager"""
    
    def __init__(self, 
                 anthropic_api_key: Optional[str] = None,
                 github_token: Optional[str] = None,
                 dry_run: bool = True):
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.dry_run = dry_run
        self.logger = self._setup_logging()
        
        # Create work directory
        self.work_dir = Path(tempfile.mkdtemp(prefix='pyhc_gallery_'))
        self.logger.info(f"Work directory: {self.work_dir}")
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pyhc_gallery_automation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def run_weekly_update(self) -> bool:
        """Run the complete weekly update workflow"""
        self.logger.info("Starting weekly PyHC Gallery update workflow")
        
        try:
            # Step 1: Scrape examples from documentation
            self.logger.info("Step 1: Scraping examples from PyHC packages")
            scraped_examples = await self._scrape_examples()
            
            if not scraped_examples:
                self.logger.warning("No examples scraped - aborting workflow")
                return False
            
            # Step 2: Process examples with LLM
            self.logger.info("Step 2: Processing examples with LLM")
            processed_results = await self._process_examples(scraped_examples)
            
            # Step 3: Clone gallery repository
            self.logger.info("Step 3: Cloning gallery repository")
            repo_dir = self.work_dir / "gallery"
            github_integration = GitHubIntegration()
            
            if not github_integration.clone_gallery_repo(str(repo_dir)):
                self.logger.error("Failed to clone repository")
                return False
            
            # Step 4: Update gallery files
            self.logger.info("Step 4: Updating gallery files")
            updated_files = await self._update_gallery_files(
                processed_results, scraped_examples, repo_dir
            )
            
            # Step 5: Create pull request (if not dry run)
            if not self.dry_run and updated_files:
                self.logger.info("Step 5: Creating pull request")
                await self._create_pull_request(github_integration, repo_dir, updated_files)
            else:
                self.logger.info("Step 5: Dry run - skipping pull request creation")
                self.logger.info(f"Updated files: {updated_files}")
            
            # Step 6: Generate summary report
            self.logger.info("Step 6: Generating summary report")
            await self._generate_summary_report(scraped_examples, processed_results, updated_files)
            
            self.logger.info("Weekly update workflow completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            return False
        finally:
            # Cleanup
            self._cleanup()
    
    async def _scrape_examples(self) -> List[CodeExample]:
        """Scrape examples from all PyHC packages"""
        scraper_output_dir = self.work_dir / "scraped"
        scraper_output_dir.mkdir(exist_ok=True)
        
        async with DocumentationScraper(str(scraper_output_dir)) as scraper:
            examples = await scraper.scrape_all_packages()
            
        self.logger.info(f"Scraped {len(examples)} examples from PyHC packages")
        return examples
    
    async def _process_examples(self, examples: List[CodeExample]) -> List[ProcessingResult]:
        """Process examples using LLM"""
        if not self.anthropic_api_key:
            self.logger.warning("No Anthropic API key - skipping LLM processing")
            return []
        
        # Convert CodeExample objects to dictionaries for processing
        example_dicts = []
        for example in examples:
            example_dicts.append({
                'package': example.package,
                'title': example.title,
                'description': example.description,
                'category': example.category,
                'source_url': example.source_url,
                'code': example.code
            })
        
        processor = BatchProcessor(self.anthropic_api_key)
        results = await processor.process_examples(example_dicts)
        
        self.logger.info(f"Processed {len(results)} examples with LLM")
        return results
    
    async def _update_gallery_files(self, 
                                  processed_results: List[ProcessingResult],
                                  original_examples: List[CodeExample],
                                  repo_dir: Path) -> List[str]:
        """Update files in the gallery repository"""
        updated_files = []
        gallery_dir = repo_dir / "gallery"
        
        if not gallery_dir.exists():
            self.logger.error(f"Gallery directory not found: {gallery_dir}")
            return []
        
        # Get current date for prefixing new files
        current_date = datetime.now().strftime("%Y%m%d")
        
        # Process each result
        for i, (result, original) in enumerate(zip(processed_results, original_examples)):
            # Generate filename
            package = original.package
            safe_title = self._sanitize_filename(result.improved_title)
            filename = f"auto_{current_date}_{package}_{i+1:02d}_{safe_title}.py"
            
            # Check if this is a significant update
            if await self._should_update_example(gallery_dir, result, original):
                # Create gallery-formatted content
                from llm_processor import ExampleFormatter
                content = ExampleFormatter.format_for_gallery(
                    result, package, original.source_url
                )
                
                # Write file
                output_path = gallery_dir / filename
                with open(output_path, 'w') as f:
                    f.write(content)
                
                updated_files.append(filename)
                self.logger.info(f"Updated: {filename}")
        
        # Update requirements.txt if needed
        await self._update_requirements(repo_dir, original_examples)
        
        # Update README with generation info
        await self._update_readme(repo_dir, len(updated_files))
        
        return updated_files
    
    async def _should_update_example(self, 
                                   gallery_dir: Path,
                                   result: ProcessingResult,
                                   original: CodeExample) -> bool:
        """Determine if an example should be updated"""
        # Always include if confidence is high
        if result.confidence_score > 0.7:
            return True
        
        # Include if it's a new package we haven't covered
        package_files = list(gallery_dir.glob(f"*{original.package}*"))
        if len(package_files) < 2:  # Less than 2 examples from this package
            return True
        
        # Include if it demonstrates new functionality
        if any(keyword in result.improved_title.lower() 
               for keyword in ['new', 'latest', '2024', '2023']):
            return True
        
        return False
    
    async def _update_requirements(self, repo_dir: Path, examples: List[CodeExample]):
        """Update requirements.txt with new dependencies"""
        requirements_file = repo_dir / "requirements.txt"
        
        if not requirements_file.exists():
            self.logger.warning("requirements.txt not found")
            return
        
        # Read current requirements
        with open(requirements_file, 'r') as f:
            current_reqs = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
        
        # Collect all dependencies from examples
        all_deps = set()
        for example in examples:
            all_deps.update(example.dependencies)
        
        # Common PyHC packages that should be included
        common_packages = {
            'sunpy', 'plasmapy', 'pyspedas', 'spacepy', 'pysat',
            'astropy', 'numpy', 'matplotlib', 'scipy'
        }
        
        new_deps = (all_deps & common_packages) - {req.split('>=')[0].split('==')[0] for req in current_reqs}
        
        if new_deps:
            self.logger.info(f"Adding new dependencies: {new_deps}")
            with open(requirements_file, 'a') as f:
                for dep in sorted(new_deps):
                    f.write(f"\n{dep}")
    
    async def _update_readme(self, repo_dir: Path, num_updated: int):
        """Update README with automation info"""
        readme_file = repo_dir / "gallery" / "README.txt"
        
        if readme_file.exists():
            with open(readme_file, 'r') as f:
                content = f.read()
            
            # Add automation notice if not already present
            automation_notice = f"""

# Automated Examples
Some examples in this gallery are automatically generated from PyHC package
documentation using the automated scraping system. These examples are prefixed
with 'auto_' and include the generation date.

Last automated update: {datetime.now().strftime('%Y-%m-%d')}
Examples updated in this run: {num_updated}
"""
            
            if "Automated Examples" not in content:
                with open(readme_file, 'a') as f:
                    f.write(automation_notice)
    
    async def _create_pull_request(self, 
                                 github_integration: GitHubIntegration,
                                 repo_dir: Path,
                                 updated_files: List[str]):
        """Create a pull request with the updates"""
        branch_name = f"auto-update-{datetime.now().strftime('%Y%m%d')}"
        
        # Create branch
        if not github_integration.create_update_branch(str(repo_dir), branch_name):
            return
        
        # Commit changes
        commit_message = f"""Automated gallery update - {datetime.now().strftime('%Y-%m-%d')}

Added {len(updated_files)} new examples automatically scraped and processed from PyHC package documentation:

{chr(10).join('- ' + f for f in updated_files[:10])}
{f'- ... and {len(updated_files) - 10} more' if len(updated_files) > 10 else ''}

Generated using automated PyHC gallery scraping system.
"""
        
        github_integration.commit_changes(str(repo_dir), commit_message)
        
        # Note: In a real implementation, you would use GitHub API to create the PR
        self.logger.info(f"Created branch {branch_name} with {len(updated_files)} updated files")
        self.logger.info("Manual step required: Create pull request via GitHub web interface")
    
    async def _generate_summary_report(self, 
                                     scraped_examples: List[CodeExample],
                                     processed_results: List[ProcessingResult],
                                     updated_files: List[str]):
        """Generate a summary report of the workflow"""
        report = {
            "workflow_date": datetime.now().isoformat(),
            "total_scraped": len(scraped_examples),
            "total_processed": len(processed_results),
            "total_updated": len(updated_files),
            "packages_scraped": list(set(ex.package for ex in scraped_examples)),
            "categories_covered": list(set(res.category for res in processed_results)),
            "average_confidence": sum(res.confidence_score for res in processed_results) / len(processed_results) if processed_results else 0,
            "updated_files": updated_files,
            "warnings_summary": {}
        }
        
        # Collect warnings
        all_warnings = []
        for result in processed_results:
            all_warnings.extend(result.warnings)
        
        warning_counts = {}
        for warning in all_warnings:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
        
        report["warnings_summary"] = warning_counts
        
        # Save report
        report_file = self.work_dir / "workflow_summary.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Summary report saved: {report_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("PYHC GALLERY AUTOMATION SUMMARY")
        print("="*50)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Scraped examples: {report['total_scraped']}")
        print(f"Processed examples: {report['total_processed']}")
        print(f"Updated files: {report['total_updated']}")
        print(f"Packages covered: {', '.join(report['packages_scraped'])}")
        print(f"Average confidence: {report['average_confidence']:.2f}")
        print("="*50)
    
    def _sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return re.sub(r'\s+', '_', sanitized).lower()[:30]
    
    def _cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.work_dir)
            self.logger.info("Cleaned up temporary work directory")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup work directory: {e}")


class ScheduledRunner:
    """Handle scheduled execution of the workflow"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def should_run_update(self) -> bool:
        """Determine if update should run (weekly check)"""
        # Check if it's been a week since last run
        last_run_file = Path("last_run.txt")
        
        if not last_run_file.exists():
            return True
        
        try:
            with open(last_run_file, 'r') as f:
                last_run_str = f.read().strip()
            
            last_run = datetime.fromisoformat(last_run_str)
            now = datetime.now()
            
            # Run if it's been more than 7 days
            return (now - last_run) > timedelta(days=7)
        except Exception as e:
            self.logger.error(f"Error checking last run: {e}")
            return True
    
    def mark_run_complete(self):
        """Mark the current run as complete"""
        with open("last_run.txt", 'w') as f:
            f.write(datetime.now().isoformat())


async def main():
    """Main entry point for automation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PyHC Gallery Automation Workflow')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (no pull request)')
    parser.add_argument('--force', action='store_true',
                       help='Force run even if not scheduled')
    
    args = parser.parse_args()
    
    # Check if we should run
    scheduler = ScheduledRunner()
    if not args.force and not scheduler.should_run_update():
        print("Not scheduled to run yet (less than 7 days since last run)")
        return
    
    # Run workflow
    workflow = WorkflowManager(dry_run=args.dry_run)
    success = await workflow.run_weekly_update()
    
    if success:
        scheduler.mark_run_complete()
        print("Workflow completed successfully!")
    else:
        print("Workflow failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())