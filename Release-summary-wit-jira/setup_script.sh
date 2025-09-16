#!/bin/bash

# Release Report Generator Setup Script
# This script helps you set up the Release Report Generator

set -e

echo "🚀 Release Report Generator Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and run this script again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip3 and run this script again."
    exit 1
fi

echo "✅ pip3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f "config.py" ]; then
    echo "⚙️  Creating config.py from template..."
    cp config_template.py config.py
    echo "✅ Config file created: config.py"
    echo "📝 Please edit config.py with your API keys and settings"
else
    echo "✅ Config file already exists: config.py"
fi

# Make CLI script executable
chmod +x run_release_report.py

# Create a convenient launcher script
cat > release-report << 'EOF'
#!/bin/bash
# Release Report Launcher Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the CLI with all arguments passed through
python3 run_release_report.py "$@"
EOF

chmod +x release-report

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your API keys and settings"
echo "2. Run: ./release-report --config-check"
echo "3. Generate your first report: ./release-report main release/v1.0.0 v1.0.0"
echo ""
echo "Available commands:"
echo "  ./release-report --help                    # Show help"
echo "  ./release-report --config-check            # Validate configuration"
echo "  ./release-report --list-branches           # List available branches"
echo "  ./release-report main develop              # Generate report"
echo ""
echo "For more information, see the README or run ./release-report --help"
