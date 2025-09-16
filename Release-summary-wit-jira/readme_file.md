# 🚀 Release Summary Report Generator

A comprehensive Python tool that generates executive-level release summary reports by analyzing Git branches, Jira tickets, code coverage, and security vulnerabilities.

## ✨ Features

### 📊 **Comprehensive Analysis**
- **Git Integration**: Analyzes merge commits between branches
- **Jira Integration**: Fetches ticket details, descriptions, and fix versions
- **AI-Powered Summaries**: Uses OpenAI to create executive summaries
- **Code Coverage**: SonarQube integration for coverage metrics
- **Security Analysis**: Veracode integration for vulnerability assessment

### 📋 **Story Analysis**
- Extracts story IDs from branch names (e.g., `feature/PROJ-123`, `bugfix/BUG-456`)
- Supports multiple branch naming conventions
- Validates fix versions against target release versions
- Parses impacted resources and risk levels from Jira descriptions

### 📈 **Rich HTML Reports**
- Executive-friendly dashboard with visual metrics
- Responsive design that works on all devices
- Print-ready formatting
- Interactive charts and progress bars
- Professional styling with modern UI components

### 🤖 **AI Integration**
- Consolidates story descriptions into executive summaries
- Identifies overall risk levels and impacted resources
- Provides actionable insights and recommendations

## 🚀 Quick Start

### 1. **Setup**
```bash
# Clone or download the files
git clone <your-repo> release-report-generator
cd release-report-generator

# Run setup script
chmod +x setup.sh
./setup.sh
```

### 2. **Configure**
Edit `config.py` with your API keys and settings:

```python
config = {
    'git_repo_path': '/path/to/your/repository',
    'jira_url': 'https://your-company.atlassian.net',
    'jira_pat_token': 'your_jira_personal_access_token',
    'openai_api_key': 'sk-your_openai_api_key',
    'sonarqube_url': 'https://your-sonarqube-instance.com',
    'sonarqube_token': 'your_sonarqube_token',
    'project_key': 'your_project_key',
    'veracode_api_id': 'your_veracode_api_id',
    'veracode_api_key': 'your_veracode_api_key'
}
```

### 3. **Generate Reports**
```bash
# Basic usage
./release-report main release/v2.1.0 v2.1.0

# With custom output file
./release-report main develop --output my_report.html

# Dry run to see what would be analyzed
./release-report main feature/new-feature --dry-run

# Skip certain analyses for faster reports
./release-report main release/v1.0.0 v1.0.0 --skip-ai --skip-sonar
```

## 📚 Detailed Usage

### **Command Line Options**
```bash
./release-report [base_branch] [target_branch] [target_version] [options]

Options:
  -o, --output FILE     Output HTML file path
  --dry-run            Show analysis without generating report
  --list-branches      List all available branches
  --config-check       Validate configuration
  --verbose, -v        Enable verbose output
  --skip-ai            Skip OpenAI consolidation
  --skip-sonar         Skip SonarQube analysis
  --skip-veracode      Skip Veracode analysis
```

### **Branch Naming Conventions**
The tool automatically detects story IDs from various branch naming patterns:

```
feature/PROJ-123-new-feature    → Story: PROJ-123, Type: feature
bugfix/BUG-456-fix-login       → Story: BUG-456, Type: bugfix
hotfix/URGENT-789-security     → Story: URGENT-789, Type: hotfix
TASK-321-update-docs           → Story: TASK-321, Type: other
```

### **Jira Description Parsing**
The tool extracts key information from Jira descriptions:

```
Impacted Resource - http://api.company.com/users PUT (Update User)
Risk level - High
Implementation description: Updates user profile endpoint
```

### **Example Reports**
Generated reports include:

- 📊 **Executive Dashboard**: High-level metrics and KPIs
- 🤖 **AI Summary**: Consolidated business impact analysis
- 📋 **Story Breakdown**: Detailed analysis of each story
- 📈 **Code Coverage**: Current coverage metrics and trends
- 🔒 **Security Analysis**: Vulnerability assessment
- ⚠️ **Recommendations**: Actionable insights for stakeholders

## 🔧 Configuration

### **Required API Keys**

1. **Jira Personal Access Token**
   ```
   Go to: Jira → Profile → Personal Access Tokens → Create token
   Scope: Read access to projects and issues
   ```

2. **OpenAI API Key**
   ```
   Go to: https://platform.openai.com/api-keys
   Create new secret key
   ```

3. **SonarQube Token**
   ```
   Go to: SonarQube → My Account → Security → Generate Token
   Permissions: Browse, Execute Analysis
   ```

4. **Veracode API Credentials**
   ```
   Go to: Veracode → Admin → API Credentials
   Generate API ID and Secret Key
   ```

### **Environment Variables**
You can use environment variables instead of editing config.py:

```bash
export GIT_REPO_PATH="/path/to/your/repository"
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_PAT_TOKEN="your_jira_token"
export OPENAI_API_KEY="sk-your_openai_key"
export SONARQUBE_URL="https://your-sonarqube.com"
export SONARQUBE_TOKEN="your_sonar_token"
export SONARQUBE_PROJECT_KEY="your_project_key"
export VERACODE_API_ID="your_veracode_id"
export VERACODE_API_KEY="your_veracode_key"
```

## 📋 Requirements

- **Python 3.8+**
- **Git** (for repository analysis)
- **Internet connection** (for API calls)

### **Python Packages**
- `requests` - API communication
- `openai` - AI-powered summaries
- `jinja2` - HTML template rendering
- `python-dateutil` - Date handling

## 🔍 Troubleshooting

### **Common Issues**

1. **"No stories found"**
   ```bash
   # Check if branches exist and have merge commits
   ./release-report --list-branches
   git log --merges main..feature/branch
   ```

2. **"Jira authentication failed"**
   ```bash
   # Verify your PAT token and URL
   ./release-report --config-check
   curl -H "Authorization: Bearer YOUR_TOKEN" "YOUR_JIRA_URL/rest/api/3/myself"
   ```

3. **"OpenAI API error"**
   ```bash
   # Check API key and quota
   curl -H "Authorization: Bearer YOUR_API_KEY" "https://api.openai.com/v1/models"
   ```

4. **"SonarQube connection failed"**
   ```bash
   # Verify SonarQube URL and token
   curl -u "YOUR_TOKEN:" "YOUR_SONARQUBE_URL/api/system/status"
   ```

### **Debug Mode**
```bash
# Enable verbose logging
./release-report main release/v1.0.0 v1.0.0 --verbose

# Skip problematic integrations
./release-report main release/v1.0.0 v1.0.0 --skip-ai --skip-sonar --skip-veracode
```

## 🎯 Best Practices

### **Branch Strategy**
- Use consistent branch naming: `type/STORY-ID-description`
- Include story IDs in merge commit messages
- Keep fix versions updated in Jira tickets

### **Jira Setup**
- Include detailed descriptions with impacted resources
- Set appropriate risk levels (High/Medium/Low)
- Maintain fix version consistency

### **Report Generation**
- Run reports regularly during release cycles
- Compare coverage trends over time
- Address high-risk items before releases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🔄 Advanced Usage

### **Custom Story Patterns**
You can customize branch naming patterns in `config.py`:

```python
'story_patterns': {
    'feature': [
        r'^feature/([a-zA-Z]+-\d+)',
        r'^feat/([a-zA-Z]+-\d+)',
        r'^new/([a-zA-Z]+-\d+)',  # Custom pattern
    ],
    'bugfix': [
        r'^bugfix/([a-zA-Z]+-\d+)',
        r'^fix/([a-zA-Z]+-\d+)',
        r'^bug/([a-zA-Z]+-\d+)',
    ],
    'hotfix': [
        r'^hotfix/([a-zA-Z]+-\d+)',
        r'^urgent/([a-zA-Z]+-\d+)',  # Custom pattern
    ]
}
```

### **Batch Processing**
Generate multiple reports for different release branches:

```bash
#!/bin/bash
# generate_all_reports.sh

releases=("v1.0.0" "v1.1.0" "v2.0.0")
base_branch="main"

for version in "${releases[@]}"; do
    echo "Generating report for $version..."
    ./release-report "$base_branch" "release/$version" "$version" \
        --output "reports/release_report_$version.html"
done
```

### **Integration with CI/CD**
Add to your GitHub Actions or Jenkins pipeline:

```yaml
# .github/workflows/release-report.yml
name: Generate Release Report

on:
  push:
    branches: [ 'release/*' ]

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Need full history for git analysis
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Generate Report
      env:
        JIRA_PAT_TOKEN: ${{ secrets.JIRA_PAT_TOKEN }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        SONARQUBE_TOKEN: ${{ secrets.SONARQUBE_TOKEN }}
        VERACODE_API_ID: ${{ secrets.VERACODE_API_ID }}
        VERACODE_API_KEY: ${{ secrets.VERACODE_API_KEY }}
      run: |
        python3 run_release_report.py main ${{ github.ref_name }} ${GITHUB_REF#refs/heads/release/}
    
    - name: Upload Report
      uses: actions/upload-artifact@v3
      with:
        name: release-report
        path: '*.html'
```

### **Custom Report Styling**
Override the default CSS by creating a custom template:

```python
# In release_report_generator.py, modify the html_template variable
# Or create a custom CSS file and reference it in the template

custom_css = """
<style>
    :root {
        --primary-color: #your-brand-color;
        --secondary-color: #your-secondary-color;
    }
    
    .header h1 {
        color: var(--primary-color);
        font-family: 'Your Brand Font', sans-serif;
    }
    
    .summary-card {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    }
</style>
"""
```

## 📊 Sample Output

### **Executive Dashboard**
```
🚀 Release Summary Report
Release: main → release/v2.1.0 (v2.1.0)
Generated: 2024-01-15 14:30:25

┌─────────────────────────────────────────┐
│  📊 Total Stories: 15                   │
│  ⚠️  Version Mismatches: 2              │
│  🔥 High Risk Items: 3                  │
│  📈 Code Coverage: 87.5%                │
└─────────────────────────────────────────┘
```

### **AI-Generated Summary**
```
🤖 Executive Summary:
This release introduces 15 stories across multiple domains, with a focus on 
user authentication improvements and API endpoint enhancements. 

Key impacted resources include:
- /api/v1/users endpoint (authentication updates)
- /api/v1/payments endpoint (payment processing improvements)
- Customer dashboard UI components

Overall risk assessment: MEDIUM
- 3 high-risk items require additional testing
- Payment processing changes need thorough validation
- Authentication updates affect all user sessions

Recommendations:
- Conduct extended regression testing for payment flows
- Plan gradual rollout for authentication changes
- Monitor user session metrics post-deployment
```

## 🔐 Security Considerations

### **API Token Security**
- Store tokens in environment variables, not in code
- Use token rotation policies for long-term deployments
- Implement least-privilege access for service accounts

### **Sensitive Data Handling**
- The tool processes commit messages and Jira descriptions
- Ensure no sensitive data is included in branch names or descriptions
- Consider data retention policies for generated reports

### **Network Security**
- All API calls use HTTPS
- Validate SSL certificates in production environments
- Consider using VPN or private networks for internal tools

## 🚀 Roadmap

### **Planned Features**
- [ ] **Multi-repository support**: Analyze multiple repos in one report
- [ ] **Historical trending**: Track metrics over time
- [ ] **Slack/Teams integration**: Send reports to channels
- [ ] **PDF export**: Generate PDF versions of reports
- [ ] **Custom webhooks**: Trigger reports on specific events
- [ ] **Dashboard mode**: Web interface for interactive reports

### **API Integrations**
- [ ] **GitHub/GitLab**: Direct integration without local git
- [ ] **Azure DevOps**: Full TFS/Azure DevOps support
- [ ] **Confluence**: Auto-publish reports to wiki pages
- [ ] **ServiceNow**: Change management integration

## 📞 Support

### **Getting Help**
1. **Check the troubleshooting section** above
2. **Run configuration check**: `./release-report --config-check`
3. **Enable verbose mode**: `./release-report --verbose`
4. **Create an issue** with full error messages and configuration (sanitized)

### **Common Support Questions**

**Q: Can I use this with GitHub Enterprise?**
A: Yes, but you'll need to modify the git commands to work with your authentication method.

**Q: Does this work with Jira Cloud and Server?**
A: Yes, both are supported. Use the appropriate API endpoints in your configuration.

**Q: Can I customize the AI prompts?**
A: Yes, modify the `get_openai_consolidation()` method in `release_report_generator.py`.

**Q: How do I handle large repositories?**
A: Use `--dry-run` to test first, and consider using `--skip-*` options for faster processing.

**Q: Can I run this in a Docker container?**
A: Yes, create a Dockerfile based on the Python 3.9+ image and install the requirements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Jira REST API** for ticket integration
- **OpenAI API** for intelligent summaries  
- **SonarQube** for code quality metrics
- **Veracode** for security analysis
- **Jinja2** for beautiful HTML templating