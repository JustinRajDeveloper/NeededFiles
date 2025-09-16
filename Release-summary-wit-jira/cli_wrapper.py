#!/usr/bin/env python3
"""
CLI wrapper for Release Report Generator
Provides an easy command-line interface for generating reports
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Import the main generator and config
try:
    from release_report_generator import ReleaseReportGenerator
    from config_template import get_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure release_report_generator.py and config.py are in the same directory")
    sys.exit(1)

def validate_branches(repo_path: str, base_branch: str, target_branch: str) -> bool:
    """Validate that branches exist in the repository"""
    import subprocess
    
    try:
        # Change to repo directory
        original_dir = os.getcwd()
        os.chdir(repo_path)
        
        # Check if branches exist
        result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True)
        branches = result.stdout
        
        base_exists = any(base_branch in line for line in branches.split('\n'))
        target_exists = any(target_branch in line for line in branches.split('\n'))
        
        os.chdir(original_dir)
        
        if not base_exists:
            print(f"❌ Base branch '{base_branch}' not found in repository")
            return False
        
        if not target_exists:
            print(f"❌ Target branch '{target_branch}' not found in repository")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating branches: {e}")
        return False

def generate_output_filename(base_branch: str, target_branch: str, target_version: str) -> str:
    """Generate a descriptive output filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = target_branch.replace('/', '_').replace(' ', '_')
    
    if target_version:
        return f"release_report_{target_version}_{timestamp}.html"
    else:
        return f"release_report_{safe_target}_{timestamp}.html"

def print_summary(generator: ReleaseReportGenerator):
    """Print a summary of found stories"""
    if not generator.stories:
        print("⚠️  No stories found between the specified branches")
        return
    
    story_types = {'feature': 0, 'bugfix': 0, 'hotfix': 0, 'other': 0}
    risk_levels = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
    
    for story in generator.stories:
        story_types[story.story_type] += 1
        risk_levels[story.risk_level] += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total Stories: {len(generator.stories)}")
    print(f"   Features: {story_types['feature']}")
    print(f"   Bug Fixes: {story_types['bugfix']}")
    print(f"   Hotfixes: {story_types['hotfix']}")
    print(f"   Others: {story_types['other']}")
    print(f"   High Risk: {risk_levels['High']}")
    print(f"   Medium Risk: {risk_levels['Medium']}")
    print(f"   Low Risk: {risk_levels['Low']}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive release summary reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s main release/v2.1.0 v2.1.0
  %(prog)s develop staging --output my_report.html
  %(prog)s main feature/new-ui --dry-run
  %(prog)s --list-branches
        """
    )
    
    parser.add_argument(
        'base_branch',
        nargs='?',
        help='Base branch to compare from (e.g., main, develop)'
    )
    
    parser.add_argument(
        'target_branch', 
        nargs='?',
        help='Target branch to compare to (e.g., release/v2.1.0, feature/xyz)'
    )
    
    parser.add_argument(
        'target_version',
        nargs='?',
        help='Expected version for fix version validation (e.g., v2.1.0)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output HTML file path (default: auto-generated)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be analyzed without generating the report'
    )
    
    parser.add_argument(
        '--list-branches',
        action='store_true',
        help='List all available branches in the repository'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--skip-ai',
        action='store_true',
        help='Skip OpenAI consolidation (faster, but less detailed summary)'
    )
    
    parser.add_argument(
        '--skip-sonar',
        action='store_true',
        help='Skip SonarQube coverage analysis'
    )
    
    parser.add_argument(
        '--skip-veracode',
        action='store_true',
        help='Skip Veracode security analysis'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = get_config()
        if args.verbose:
            print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your config.py file or environment variables")
        sys.exit(1)
    
    # Configuration check
    if args.config_check:
        print("🔍 Configuration Check:")
        print(f"   Git Repo: {config['git_repo_path']}")
        print(f"   Jira URL: {config['jira_url']}")
        print(f"   OpenAI: {'✅' if config.get('openai_api_key', '').startswith('sk-') else '❌'}")
        print(f"   SonarQube: {'✅' if config.get('sonarqube_url') else '❌'}")
        print(f"   Veracode: {'✅' if config.get('veracode_api_id') else '❌'}")
        return
    
    # List branches
    if args.list_branches:
        try:
            import subprocess
            os.chdir(config['git_repo_path'])
            result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True)
            print("Available branches:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Error listing branches: {e}")
        return
    
    # Validate required arguments
    if not args.base_branch or not args.target_branch:
        print("❌ Both base_branch and target_branch are required")
        parser.print_help()
        sys.exit(1)
    
    # Validate branches exist
    if not validate_branches(config['git_repo_path'], args.base_branch, args.target_branch):
        sys.exit(1)
    
    # Generate output filename if not provided
    output_file = args.output or generate_output_filename(
        args.base_branch, 
        args.target_branch, 
        args.target_version or ''
    )
    
    print(f"🚀 Release Report Generator")
    print(f"   Base Branch: {args.base_branch}")
    print(f"   Target Branch: {args.target_branch}")
    print(f"   Target Version: {args.target_version or 'Not specified'}")
    print(f"   Output File: {output_file}")
    
    if args.dry_run:
        print(f"   🔍 DRY RUN MODE - No report will be generated")
    
    print()
    
    # Initialize generator with config modifications based on flags
    if args.skip_ai:
        config['openai_api_key'] = None
        print("⏭️  Skipping OpenAI analysis")
    
    if args.skip_sonar:
        config['sonarqube_token'] = None
        print("⏭️  Skipping SonarQube analysis")
    
    if args.skip_veracode:
        config['veracode_api_id'] = None
        print("⏭️  Skipping Veracode analysis")
    
    try:
        generator = ReleaseReportGenerator(config)
        
        # Analyze stories
        print("🔍 Analyzing merge commits...")
        generator.analyze_stories(
            args.base_branch, 
            args.target_branch, 
            args.target_version or ''
        )
        
        # Print summary
        print_summary(generator)
        
        if args.dry_run:
            print("\n✅ Dry run completed successfully")
            return
        
        # Generate report
        print(f"\n📝 Generating HTML report...")
        output_path = generator.generate_report(
            args.base_branch,
            args.target_branch, 
            args.target_version or '',
            output_file
        )
        
        # Success message
        output_path = Path(output_file).resolve()
        print(f"\n✅ Report generated successfully!")
        print(f"📄 File: {output_path}")
        print(f"🌐 Open in browser: file://{output_path}")
        
        # Optional: Open in browser automatically
        if sys.platform.startswith('darwin'):  # macOS
            os.system(f'open "{output_path}"')
        elif sys.platform.startswith('linux'):  # Linux
            os.system(f'xdg-open "{output_path}"')
        elif sys.platform.startswith('win'):  # Windows
            os.system(f'start "{output_path}"')
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
