#!/bin/bash

# Spring Boot Test Coverage Analyzer
# Compares test coverage between two branches
# Usage: ./analyze-test-coverage.sh <previous-branch> <current-branch>

set -e

PREV_BRANCH=${1:-"main"}
CURR_BRANCH=${2:-"HEAD"}
OUTPUT_DIR="coverage-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create output directory
mkdir -p $OUTPUT_DIR

echo "🧪 Analyzing test coverage between $PREV_BRANCH and $CURR_BRANCH..."

# Function to run tests and generate coverage for a specific branch
generate_coverage_for_branch() {
    local branch=$1
    local report_dir=$2
    
    echo "📊 Generating coverage for branch: $branch"
    
    # Checkout branch
    git stash push -m "temp-stash-for-coverage-$TIMESTAMP" || true
    git checkout $branch
    
    # Clean and run tests with coverage
    if [ -f "pom.xml" ]; then
        # Maven project
        ./mvnw clean test jacoco:report -DskipTests=false
        
        # Copy coverage reports
        mkdir -p "$report_dir"
        if [ -d "target/site/jacoco" ]; then
            cp -r target/site/jacoco/* "$report_dir/"
        fi
        
        # Extract coverage summary
        if [ -f "target/site/jacoco/index.html" ]; then
            # Parse HTML for coverage percentages
            grep -o "Total.*[0-9]*%" target/site/jacoco/index.html > "$report_dir/coverage-summary.txt" || echo "Coverage parsing failed" > "$report_dir/coverage-summary.txt"
        fi
        
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        # Gradle project
        ./gradlew clean test jacocoTestReport
        
        # Copy coverage reports
        mkdir -p "$report_dir"
        if [ -d "build/reports/jacoco/test/html" ]; then
            cp -r build/reports/jacoco/test/html/* "$report_dir/"
        fi
        
        # Extract coverage summary from Gradle
        if [ -f "build/reports/jacoco/test/jacocoTestReport.xml" ]; then
            python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('build/reports/jacoco/test/jacocoTestReport.xml')
    root = tree.getroot()
    for counter in root.findall('.//counter[@type=\"INSTRUCTION\"]'):
        covered = float(counter.get('covered', 0))
        missed = float(counter.get('missed', 0))
        total = covered + missed
        if total > 0:
            percentage = (covered / total) * 100
            print(f'Instruction Coverage: {percentage:.2f}% ({int(covered)}/{int(total)})')
    for counter in root.findall('.//counter[@type=\"BRANCH\"]'):
        covered = float(counter.get('covered', 0))
        missed = float(counter.get('missed', 0))
        total = covered + missed
        if total > 0:
            percentage = (covered / total) * 100
            print(f'Branch Coverage: {percentage:.2f}% ({int(covered)}/{int(total)})')
except Exception as e:
    print(f'Error parsing coverage: {e}')
" > "$report_dir/coverage-summary.txt"
        fi
    else
        echo "❌ No Maven (pom.xml) or Gradle (build.gradle) project detected"
        exit 1
    fi
    
    # Generate test execution summary
    echo "📋 Test Execution Summary for $branch:" > "$report_dir/test-summary.txt"
    
    if [ -f "pom.xml" ]; then
        # Maven test summary
        if [ -f "target/surefire-reports/TEST-*.xml" ]; then
            echo "Test Results:" >> "$report_dir/test-summary.txt"
            find target/surefire-reports -name "TEST-*.xml" -exec grep -h "testcase.*time" {} \; | wc -l | xargs echo "Total Test Cases:" >> "$report_dir/test-summary.txt"
            find target/surefire-reports -name "TEST-*.xml" -exec grep -l "failure\|error" {} \; | wc -l | xargs echo "Failed Test Suites:" >> "$report_dir/test-summary.txt"
        fi
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        # Gradle test summary
        if [ -d "build/test-results/test" ]; then
            echo "Test Results:" >> "$report_dir/test-summary.txt"
            find build/test-results/test -name "TEST-*.xml" -exec grep -h "testcase.*time" {} \; | wc -l | xargs echo "Total Test Cases:" >> "$report_dir/test-summary.txt"
            find build/test-results/test -name "TEST-*.xml" -exec grep -l "failure\|error" {} \; | wc -l | xargs echo "Failed Test Suites:" >> "$report_dir/test-summary.txt"
        fi
    fi
}

# Generate coverage for previous branch
echo "🔄 Analyzing previous branch: $PREV_BRANCH"
generate_coverage_for_branch $PREV_BRANCH "$OUTPUT_DIR/previous-branch"

# Generate coverage for current branch
echo "🔄 Analyzing current branch: $CURR_BRANCH"
generate_coverage_for_branch $CURR_BRANCH "$OUTPUT_DIR/current-branch"

# Return to current branch
git checkout $CURR_BRANCH
git stash pop || true

# Generate comparison report
COMPARISON_REPORT="$OUTPUT_DIR/coverage-comparison-$TIMESTAMP.md"

echo "# Test Coverage Comparison Report" > $COMPARISON_REPORT
echo "**Generated on:** $(date)" >> $COMPARISON_REPORT
echo "**Comparing:** $PREV_BRANCH → $CURR_BRANCH" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "## 📊 Coverage Summary" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "### Previous Branch ($PREV_BRANCH)" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
cat "$OUTPUT_DIR/previous-branch/coverage-summary.txt" 2>/dev/null || echo "Coverage data not available" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "### Current Branch ($CURR_BRANCH)" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
cat "$OUTPUT_DIR/current-branch/coverage-summary.txt" 2>/dev/null || echo "Coverage data not available" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "## 🧪 Test Execution Summary" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "### Previous Branch ($PREV_BRANCH)" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
cat "$OUTPUT_DIR/previous-branch/test-summary.txt" 2>/dev/null || echo "Test summary not available" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "### Current Branch ($CURR_BRANCH)" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
cat "$OUTPUT_DIR/current-branch/test-summary.txt" 2>/dev/null || echo "Test summary not available" >> $COMPARISON_REPORT
echo "\`\`\`" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "## 📈 New Test Files Analysis" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

NEW_TEST_FILES=$(git diff --name-only $PREV_BRANCH..$CURR_BRANCH | grep -E 'Test\.java$|test.*\.java$|.*Tests\.java$' || echo "")
MODIFIED_TEST_FILES=$(git diff --name-status $PREV_BRANCH..$CURR_BRANCH | grep -E '^M.*Test\.java$|^M.*test.*\.java$|^M.*Tests\.java$' | cut -f2 || echo "")

if [ ! -z "$NEW_TEST_FILES" ]; then
    echo "### ✅ New Test Files Added" >> $COMPARISON_REPORT
    echo "$NEW_TEST_FILES" | while read file; do
        echo "- $file" >> $COMPARISON_REPORT
    done
    echo "" >> $COMPARISON_REPORT
fi

if [ ! -z "$MODIFIED_TEST_FILES" ]; then
    echo "### 🔄 Modified Test Files" >> $COMPARISON_REPORT
    echo "$MODIFIED_TEST_FILES" | while read file; do
        echo "- $file" >> $COMPARISON_REPORT
    done
    echo "" >> $COMPARISON_REPORT
fi

echo "## 📂 Coverage Reports Location" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT
echo "- **Previous Branch HTML Report:** \`$OUTPUT_DIR/previous-branch/index.html\`" >> $COMPARISON_REPORT
echo "- **Current Branch HTML Report:** \`$OUTPUT_DIR/current-branch/index.html\`" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "## 🎯 Recommendations" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT
echo "1. Review the HTML coverage reports for detailed class-by-class analysis" >> $COMPARISON_REPORT
echo "2. Focus on files with decreased coverage" >> $COMPARISON_REPORT
echo "3. Ensure new features have adequate test coverage" >> $COMPARISON_REPORT
echo "4. Consider adding integration tests for complex workflows" >> $COMPARISON_REPORT
echo "" >> $COMPARISON_REPORT

echo "---" >> $COMPARISON_REPORT
echo "*Report generated by test-coverage-analyzer on $(date)*" >> $COMPARISON_REPORT

echo "✅ Coverage comparison report generated: $COMPARISON_REPORT"
echo "📊 Coverage reports available at:"
echo "   - Previous: $OUTPUT_DIR/previous-branch/index.html"
echo "   - Current: $OUTPUT_DIR/current-branch/index.html"