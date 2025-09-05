#!/bin/bash
# Siemply Production Web Interface Startup Script

set -e

echo "🚀 Starting Siemply Production Web Interface"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "src/siemply/api/main.py" ]; then
    echo "❌ Error: Please run this script from the Siemply root directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python..."
fi

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install -e . > /dev/null 2>&1

# Check if web build exists
if [ -d "web/build" ]; then
    echo "✅ React build found"
else
    echo "⚠️  React build not found. Using HTML fallback interface."
    echo "   To build React interface, install Node.js and run:"
    echo "   cd web && npm install && npm run build"
fi

# Set environment variables
export SIEMPLY_CONFIG_DIR="${SIEMPLY_CONFIG_DIR:-./config}"
export SIEMPLY_LOG_LEVEL="${SIEMPLY_LOG_LEVEL:-INFO}"

# Start the web server
echo "🌐 Starting FastAPI server..."
echo "   API URL: http://localhost:8000"
echo "   Web Interface: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""

# Start with uvicorn
uvicorn siemply.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
