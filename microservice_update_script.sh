#!/bin/bash

# Configuration
BRANCH_NAME="update-abc-property"
COMMIT_MESSAGE="Update ABC;D property to use environment variable"
PR_TITLE="Update ABC;D property configuration"
PR_BODY="This PR updates the ABC;D property from hardcoded value to use environment variable \${sss}"

# Configuration for Git repositories
GITHUB_USERNAME="your-username"           # Your GitHub username
GITHUB_PAT="your-personal-access-token"   # Your GitHub Personal Access Token
GITHUB_ORG="your-organization"            # Your GitHub organization name

# Construct the base URL with PAT embedded
GIT_BASE_URL="https://${GITHUB_USERNAME}:${GITHUB_PAT}@github.com/${GITHUB_ORG}"

# Alternative examples for other Git providers:
# GitLab: GIT_BASE_URL="https://${GITHUB_USERNAME}:${GITHUB_PAT}@gitlab.com/${GITHUB_ORG}"
# Bitbucket: GIT_BASE_URL="https://${GITHUB_USERNAME}:${GITHUB_PAT}@bitbucket.org/${GITHUB_ORG}"
# Azure DevOps: GIT_BASE_URL="https://${GITHUB_USERNAME}:${GITHUB_PAT}@dev.azure.com/${GITHUB_ORG}"

WORK_DIR="./microservices_workspace"  # Directory where repos will be cloned

# List of microservices - update this array with your microservice repository names
MICROSERVICES=(
    "microservice1"
    "microservice2" 
    "microservice3"
    # Add more microservice names here
)

# Function to update properties file
update_properties_file() {
    local file_path="$1"
    
    if [ -f "$file_path" ]; then
        echo "  Updating $file_path..."
        # Use sed to replace ABC;D=fdfdfd_ pattern with ABC;D=${sss}
        # This handles the pattern where value starts with fdfdfd_ 
        sed -i 's/ABC;D=fdfdfd_[^[:space:]]*/ABC;D=${sss}/g' "$file_path"
        
        # Alternative: if you want to replace ANY value after ABC;D= with ${sss}
        # sed -i 's/ABC;D=.*/ABC;D=${sss}/g' "$file_path"
        
        echo "  File updated successfully"
        return 0
    else
        echo "  Warning: File $file_path not found"
        return 1
    fi
}

# Function to clone repository
clone_repository() {
    local service_name="$1"
    local repo_url="${GIT_BASE_URL}/${service_name}.git"
    
    echo "Cloning $service_name from $repo_url..."
    
    if git clone "$repo_url" "$service_name"; then
        echo "  Successfully cloned $service_name"
        return 0
    else
        echo "  Error: Failed to clone $service_name"
        return 1
    fi
}

# Function to process each microservice
process_microservice() {
    local service_name="$1"
    local service_path="./$service_name"
    
    echo "Processing microservice: $service_name"
    echo "=================================="
    
    # Clone the repository if it doesn't exist
    if [ ! -d "$service_path" ]; then
        echo "Repository not found locally. Cloning..."
        if ! clone_repository "$service_name"; then
            echo "Failed to clone repository. Skipping $service_name"
            echo ""
            return 1
        fi
    else
        echo "Repository already exists locally"
    fi
    
    cd "$service_path" || return 1
    
    # 1. Create and checkout new branch from master
    echo "1. Creating branch '$BRANCH_NAME' from master..."
    git checkout master
    git pull origin master
    git checkout -b "$BRANCH_NAME"
    
    # 2. Update the properties file
    echo "2. Updating sample/app.properties..."
    if update_properties_file "sample/app.properties"; then
        # Check if there are actually changes to commit
        if git diff --quiet; then
            echo "  No changes detected in the file"
            git checkout master
            git branch -d "$BRANCH_NAME"
            cd ..
            echo ""
            return 0
        fi
        
        # 3. Commit the changes
        echo "3. Committing changes..."
        git add sample/app.properties
        git commit -m "$COMMIT_MESSAGE"
        
        # 4. Push the branch
        echo "4. Pushing branch to remote..."
        git push origin "$BRANCH_NAME"
        
        # 5. Create Pull Request (using GitHub CLI)
        echo "5. Creating Pull Request..."
        if command -v gh &> /dev/null; then
            gh pr create --title "$PR_TITLE" --body "$PR_BODY" --base master --head "$BRANCH_NAME"
            echo "  Pull Request created successfully"
        else
            echo "  GitHub CLI (gh) not found. Please create PR manually:"
            echo "  Branch: $BRANCH_NAME"
            echo "  Title: $PR_TITLE"
        fi
    else
        echo "  Failed to update properties file"
        git checkout master
        git branch -d "$BRANCH_NAME"
    fi
    
    cd ..
    echo ""
}

# Main execution
echo "Starting microservice update process..."
echo "======================================"

# Create workspace directory
echo "Setting up workspace..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR" || {
    echo "Error: Failed to create/access workspace directory"
    exit 1
}

echo "Working in directory: $(pwd)"
echo ""

for service in "${MICROSERVICES[@]}"; do
    process_microservice "$service"
done

echo ""
echo "Setup Instructions:"
echo "==================="
echo "1. Update the following variables in this script:"
echo "   - GITHUB_USERNAME: Your GitHub username"
echo "   - GITHUB_PAT: Your Personal Access Token"
echo "   - GITHUB_ORG: Your organization name"
echo "   - MICROSERVICES: Array of your microservice names"
echo ""
echo "2. To create a GitHub PAT:"
echo "   - Go to GitHub Settings → Developer settings → Personal access tokens"
echo "   - Generate new token with 'repo' permissions"
echo ""
echo "3. Keep your PAT secure and never commit it to version control!"
echo ""
echo "SECURITY WARNING: This script contains embedded credentials."
echo "Make sure to:"
echo "- Never commit this script with real credentials"
echo "- Use environment variables for production"
echo "- Delete or secure this script after use"