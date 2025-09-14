# Release Analysis Tools - Setup Instructions

## 📥 Quick Setup

### Step 1: Save the Scripts

1. Copy each script from the artifacts above
2. Save them in your project root directory:
   - `generate-release-summary.sh`
   - `analyze-test-coverage.sh`
   - `ai_analysis_enhancer.py`

### Step 2: Make Scripts Executable

```bash
chmod +x generate-release-summary.sh
chmod +x analyze-test-coverage.sh
chmod +x ai_analysis_enhancer.py
```

### Step 3: Verify Requirements

Ensure you have:
- ✅ **Git repository** with target branches
- ✅ **Maven** (`pom.xml`) or **Gradle** (`build.gradle`)
- ✅ **Python 3** (for AI enhancement script)
- ✅ **Bash shell** (Linux, macOS, or WSL)

## 🚀 Usage Examples

### Basic Release Summary
```bash
# Compare main branch to current HEAD
./generate-release-summary.sh main HEAD

# Compare specific branches
./generate-release-summary.sh release-1.0 release-2.0
```

### Test Coverage Analysis
```bash
# Generate coverage comparison
./analyze-test-