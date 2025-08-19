#!/bin/bash

# Microservice Properties Comparator - Run Script
echo "🚀 Starting Microservice Properties Comparator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your GitHub token if needed"
fi

# Start the Flask application
echo "🌐 Starting Flask application..."
echo "📋 Application will be available at: http://localhost:5000"
echo "🔒 Security analysis included automatically"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py