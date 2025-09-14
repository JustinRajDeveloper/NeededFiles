#!/usr/bin/env python3
"""
AI Analysis Enhancement Script for GitHub Copilot
Prepares structured prompts for better code analysis

Usage: python3 ai_analysis_enhancer.py <repo_path> <prev_branch> <curr_branch>
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_git_command(command, repo_path):
    """Run git command and return output"""
    try:
        result = subprocess.run(
            command.split(), 
            cwd=repo_path, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return ""

def analyze_file_changes(repo_path, prev_branch, curr_branch):
    """Analyze changes in each file"""
    
    # Get list of changed files
    changed_files_cmd = f"git diff --name-only {prev_branch}..{curr_branch}"
    changed_files = run_git_command(changed_files_cmd, repo_path).split('\n')
    
    java_files = [f for f in changed_files if f.endswith('.java') and f]
    
    analysis_data = {
        "metadata": {
            "prev_branch": prev_branch,
            "curr_branch": curr_branch,
            "analysis_date": datetime.now().isoformat(),
            "total_files_changed": len([f for f in changed_files if f])
        },
        "files": []
    }
    
    for java_file in java_files[:15]:  # Limit to prevent overwhelming
        file_path = os.path.join(repo_path, java_file)
        
        if not os.path.exists(file_path):
            continue
            
        # Get file diff
        diff_cmd = f"git diff {prev_branch}..{curr_branch} -- {java_file}"
        diff_output = run_git_command(diff_cmd, repo_path)
        
        # Get file stats
        stat_cmd = f"git diff --numstat {prev_branch}..{curr_branch} -- {java_file}"
        stat_output = run_git_command(stat_cmd, repo_path)
        
        # Parse stats
        additions, deletions = 0, 0
        if stat_output:
            parts = stat_output.split('\t')
            if len(parts) >= 2:
                try:
                    additions = int(parts[0]) if parts[0] != '-' else 0
                    deletions = int(parts[1]) if parts[1] != '-' else 0
                except ValueError:
                    pass
        
        # Determine file type and purpose
        file_type = "unknown"
        if "Test" in java_file or "test" in java_file.lower():
            file_type = "test"
        elif "Controller" in java_file:
            file_type = "controller"
        elif "Service" in java_file:
            file_type = "service"
        elif "Repository" in java_file:
            file_type = "repository"
        elif "Entity" in java_file or "Model" in java_file:
            file_type = "model"
        elif "Config" in java_file:
            file_type = "configuration"
        else:
            file_type = "business_logic"
        
        # Read current file content (first 100 lines for context)
        current_content = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:100]
                current_content = ''.join(lines)
        except Exception:
            pass
        
        file_analysis = {
            "filename": java_file,
            "file_type": file_type,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "net_change": additions - deletions
            },
            "diff": diff_output[:2000],  # Limit diff size
            "current_content_preview": current_content[:1000],  # First 1000 chars
            "analysis_priority": "high" if additions + deletions > 20 else "medium" if additions + deletions > 5 else "low"
        }
        
        analysis_data["files"].append(file_analysis)
    
    return analysis_data

def generate_ai_prompts(analysis_data, output_dir):
    """Generate structured prompts for AI analysis"""
    
    prompts_dir = os.path.join(output_dir, "ai-prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Generate overview prompt
    overview_prompt = f"""
# Release Analysis Overview

## Context
Analyzing changes from {analysis_data['metadata']['prev_branch']} to {analysis_data['metadata']['curr_branch']}
Total files changed: {analysis_data['metadata']['total_files_changed']}

## Files by Priority
High Priority Changes: {len([f for f in analysis_data['files'] if f['analysis_priority'] == 'high'])}
Medium Priority Changes: {len([f for f in analysis_data['files'] if f['analysis_priority'] == 'medium'])}
Low Priority Changes: {len([f for f in analysis_data['files'] if f['analysis_priority'] == 'low'])}

## Analysis Request
Please analyze this Spring Boot application release and provide:

1. **Business Impact Summary**: What features/functionality changed?
2. **Technical Risk Assessment**: Any potential breaking changes or risks?
3. **Architecture Changes**: New patterns, dependencies, or structural changes?
4. **Testing Recommendations**: Areas that need additional testing focus?

## File Distribution by Type
"""
    
    file_types = {}
    for file_info in analysis_data['files']:
        file_type = file_info['file_type']
        file_types[file_type] = file_types.get(file_type, 0) + 1
    
    for file_type, count in file_types.items():
        overview_prompt += f"- {file_type.replace('_', ' ').title()}: {count} files\n"
    
    with open(os.path.join(prompts_dir, "00_overview_prompt.md"), 'w') as f:
        f.write(overview_prompt)
    
    # Generate individual file prompts
    for i, file_info in enumerate(analysis_data['files'], 1):
        file_prompt = f"""# File Analysis Request

## File: {file_info['filename']}
**Type:** {file_info['file_type'].replace('_', ' ').title()}
**Priority:** {file_info['analysis_priority'].title()}

## Change Statistics
- **Lines Added:** {file_info['stats']['additions']}
- **Lines Deleted:** {file_info['stats']['deletions']}
- **Net Change:** {file_info['stats']['net_change']}

## Current File Context (Preview)
```java
{file_info['current_content_preview']}
```

## Code Diff
```diff
{file_info['diff']}
```

## Analysis Questions
1. **What is the purpose of this change?**
2. **Are there any potential side effects or breaking changes?**
3. **Does this change follow Spring Boot best practices?**
4. **What should be tested to verify this change?**
5. **Are there any security or performance implications?**

Please provide a concise analysis focusing on the business impact and technical implications.
"""
        
        filename = f"{i:02d}_{Path(file_info['filename']).stem}_analysis.md"
        with open(os.path.join(prompts_dir, filename), 'w') as f:
            f.write(file_prompt)
    
    # Generate consolidation prompt
    consolidation_prompt = f"""# Release Summary Consolidation

## Instructions
After analyzing all individual files, please consolidate your findings into a comprehensive release summary.

## Required Sections

### 1. Executive Summary
- Brief overview of the release scope
- Key business features added/modified
- Overall risk level (Low/Medium/High)

### 2. Feature Changes
- New features introduced
- Modified existing features
- Deprecated or removed features

### 3. Technical Changes
- Architecture modifications
- New dependencies or framework updates
- Configuration changes
- Database schema changes (if any)

### 4. Risk Assessment
- Breaking changes
- Backward compatibility issues
- Performance implications
- Security considerations

### 5. Testing Strategy
- Critical test scenarios
- Areas requiring manual testing
- Regression test recommendations

### 6. Deployment Considerations
- Migration steps required
- Configuration updates needed
- Rollback procedures

## File Analysis Summary
Total files analyzed: {len(analysis_data['files'])}

Please reference your individual file analyses to create this comprehensive summary.
"""
    
    with open(os.path.join(prompts_dir, "99_consolidation_prompt.md"), 'w') as f:
        f.write(consolidation_prompt)
    
    return prompts_dir

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 ai_analysis_enhancer.py <repo_path> <prev_branch> <curr_branch>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    prev_branch = sys.argv[2]
    curr_branch = sys.argv[3]
    
    if not os.path.exists(repo_path):
        print(f"Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    print(f"🔍 Analyzing changes between {prev_branch} and {curr_branch}...")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"ai-analysis-{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Analyze changes
    analysis_data = analyze_file_changes(repo_path, prev_branch, curr_branch)
    
    # Save raw analysis data
    with open(os.path.join(output_dir, "analysis_data.json"), 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    # Generate AI prompts
    prompts_dir = generate_ai_prompts(analysis_data, output_dir)
    
    print(f"✅ Analysis complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"🤖 AI prompts generated in: {prompts_dir}")
    print(f"📊 Total Java files analyzed: {len(analysis_data['files'])}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Review the prompts in {prompts_dir}")
    print(f"2. Use each prompt file with GitHub Copilot/ChatGPT individually")
    print(f"3. Start with 00_overview_prompt.md")
    print(f"4. Process high-priority files first")
    print(f"5. Finish with 99_consolidation_prompt.md for the final report")

if __name__ == "__main__":
    main()