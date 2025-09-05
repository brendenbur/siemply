#!/bin/bash
# Simple Siemply Web Interface Startup Script

echo "🚀 Starting Siemply Web Interface"
echo "================================="

# Check if we're in the right directory
if [ ! -f "src/siemply/api/main.py" ]; then
    echo "❌ Error: Please run this script from the Siemply root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Using system Python..."
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e . > /dev/null 2>&1

# Set environment variables
export SIEMPLY_CONFIG_DIR="${SIEMPLY_CONFIG_DIR:-./config}"
export SIEMPLY_LOG_LEVEL="${SIEMPLY_LOG_LEVEL:-INFO}"

# Start the web server
echo "🌐 Starting FastAPI server..."
echo "   API URL: http://localhost:8000"
echo "   Web Interface: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with uvicorn
python3 -m uvicorn siemply.api.main:app --host 0.0.0.0 --port 8000 --reload
