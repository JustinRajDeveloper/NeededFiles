#!/bin/bash

# Release Summary Generator
# Usage: ./generate-release-summary.sh <previous-branch> <current-branch>

set -e

PREV_BRANCH=${1:-"main"}
CURR_BRANCH=${2:-"HEAD"}
OUTPUT_DIR="release-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$OUTPUT_DIR/release-summary-$TIMESTAMP.md"

# Create output directory
mkdir -p $OUTPUT_DIR

echo "# Release Summary Report" > $REPORT_FILE
echo "**Generated on:** $(date)" >> $REPORT_FILE
echo "**Comparing:** $PREV_BRANCH → $CURR_BRANCH" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 1. High-level Statistics
echo "## 📊 Release Statistics" >> $REPORT_FILE
echo "" >> $REPORT_FILE

COMMIT_COUNT=$(git rev-list --count $PREV_BRANCH..$CURR_BRANCH)
MERGE_COUNT=$(git rev-list --merges --count $PREV_BRANCH..$CURR_BRANCH)
FILES_CHANGED=$(git diff --name-only $PREV_BRANCH..$CURR_BRANCH | wc -l)

echo "- **Total Commits:** $COMMIT_COUNT" >> $REPORT_FILE
echo "- **Merge Commits:** $MERGE_COUNT" >> $REPORT_FILE
echo "- **Files Changed:** $FILES_CHANGED" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 2. File Changes by Category
echo "## 📁 Changes by File Type" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "### Java Files" >> $REPORT_FILE
git diff --name-only $PREV_BRANCH..$CURR_BRANCH | grep -E '\.java$' | head -20 >> $REPORT_FILE || echo "No Java files changed" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "### Configuration Files" >> $REPORT_FILE
git diff --name-only $PREV_BRANCH..$CURR_BRANCH | grep -E '\.(properties|yml|yaml|xml)$' | head -10 >> $REPORT_FILE || echo "No config files changed" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "### Test Files" >> $REPORT_FILE
git diff --name-only $PREV_BRANCH..$CURR_BRANCH | grep -E 'Test\.java$|test.*\.java$' | head -10 >> $REPORT_FILE || echo "No test files changed" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 3. Detailed Merge Commits
echo "## 🔄 Merge Commits Details" >> $REPORT_FILE
echo "" >> $REPORT_FILE

git log --merges --oneline --format="- **%s** by %an (%ad)" --date=short $PREV_BRANCH..$CURR_BRANCH >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 4. Generate diff summaries for key files (chunked approach)
echo "## 🔍 Key Changes Analysis" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Get Java files with significant changes (>10 lines)
SIGNIFICANT_JAVA_FILES=$(git diff --numstat $PREV_BRANCH..$CURR_BRANCH | awk '$1+$2 > 10 && $3 ~ /\.java$/ {print $3}' | head -5)

if [ ! -z "$SIGNIFICANT_JAVA_FILES" ]; then
    echo "### Significant Java File Changes" >> $REPORT_FILE
    for file in $SIGNIFICANT_JAVA_FILES; do
        echo "" >> $REPORT_FILE
        echo "#### $file" >> $REPORT_FILE
        echo "\`\`\`diff" >> $REPORT_FILE
        # Limit diff output to prevent overwhelming
        git diff $PREV_BRANCH..$CURR_BRANCH -- "$file" | head -50 >> $REPORT_FILE
        echo "\`\`\`" >> $REPORT_FILE
    done
fi

# 5. Dependencies Changes (Maven/Gradle)
echo "" >> $REPORT_FILE
echo "## 📦 Dependency Changes" >> $REPORT_FILE
echo "" >> $REPORT_FILE

if [ -f "pom.xml" ]; then
    echo "### Maven Dependencies (pom.xml)" >> $REPORT_FILE
    echo "\`\`\`xml" >> $REPORT_FILE
    git diff $PREV_BRANCH..$CURR_BRANCH -- pom.xml | grep -E '^\+.*<dependency>|^\+.*<version>|^\-.*<dependency>|^\-.*<version>' | head -20 >> $REPORT_FILE || echo "No dependency changes detected" >> $REPORT_FILE
    echo "\`\`\`" >> $REPORT_FILE
elif [ -f "build.gradle" ]; then
    echo "### Gradle Dependencies (build.gradle)" >> $REPORT_FILE
    echo "\`\`\`gradle" >> $REPORT_FILE
    git diff $PREV_BRANCH..$CURR_BRANCH -- build.gradle | grep -E '^\+.*implementation|^\+.*testImplementation|^\-.*implementation|^\-.*testImplementation' | head -20 >> $REPORT_FILE || echo "No dependency changes detected" >> $REPORT_FILE
    echo "\`\`\`" >> $REPORT_FILE
fi

# 6. Generate individual file analysis for AI processing
mkdir -p "$OUTPUT_DIR/file-chunks"
JAVA_FILES=$(git diff --name-only $PREV_BRANCH..$CURR_BRANCH | grep -E '\.java$' | head -10)

for file in $JAVA_FILES; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .java)
        echo "Analyzing changes in: $file" > "$OUTPUT_DIR/file-chunks/${filename}_analysis.txt"
        echo "File: $file" >> "$OUTPUT_DIR/file-chunks/${filename}_analysis.txt"
        echo "Changes:" >> "$OUTPUT_DIR/file-chunks/${filename}_analysis.txt"
        git diff $PREV_BRANCH..$CURR_BRANCH -- "$file" >> "$OUTPUT_DIR/file-chunks/${filename}_analysis.txt"
    fi
done

echo "" >> $REPORT_FILE
echo "## 🤖 AI Analysis Instructions" >> $REPORT_FILE
echo "" >> $REPORT_FILE
echo "Individual file analysis chunks have been generated in: \`$OUTPUT_DIR/file-chunks/\`" >> $REPORT_FILE
echo "" >> $REPORT_FILE
echo "To get detailed AI analysis:" >> $REPORT_FILE
echo "1. Process each file chunk separately with GitHub Copilot" >> $REPORT_FILE
echo "2. Use the prompt: 'Analyze this code diff and explain the business impact and technical changes'" >> $REPORT_FILE
echo "3. Consolidate the individual analyses into this report" >> $REPORT_FILE

echo "" >> $REPORT_FILE
echo "---" >> $REPORT_FILE
echo "*Report generated by release-summary-generator on $(date)*" >> $REPORT_FILE

echo "✅ Release summary generated: $REPORT_FILE"
echo "📁 File chunks created in: $OUTPUT_DIR/file-chunks/"