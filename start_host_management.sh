#!/bin/bash
# Start Siemply Host Management with Enhanced Features

echo "🚀 Starting Siemply Host Management"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "src/siemply/api/main_new.py" ]; then
    echo "❌ Error: Please run this script from the Siemply root directory"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $python_version"

if [ "$(echo "$python_version < 3.11" | bc -l 2>/dev/null || echo "1")" -eq 1 ]; then
    echo "❌ Python 3.11+ required. Current: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements_new.txt
pip install -e .

# Set environment variables
export SIEMPLY_SECRET_KEY="${SIEMPLY_SECRET_KEY:-$(openssl rand -hex 32)}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./siemply.db}"
export SIEMPLY_LOG_LEVEL="${SIEMPLY_LOG_LEVEL:-INFO}"

echo "🔐 Using secret key: ${SIEMPLY_SECRET_KEY:0:8}..."
echo "🗄️  Database: $DATABASE_URL"

# Check if web frontend is built
if [ -d "web_new/dist" ]; then
    echo "✅ React frontend build found"
    # Copy build to web directory for serving
    cp -r web_new/dist/* web/build/ 2>/dev/null || true
else
    echo "⚠️  React frontend not built. Building now..."
    cd web_new
    if command -v npm &> /dev/null; then
        npm install
        npm run build
        cd ..
        # Copy build to web directory for serving
        cp -r web_new/dist/* web/build/ 2>/dev/null || true
        echo "✅ React frontend built and copied"
    else
        echo "⚠️  npm not found. Using fallback HTML interface."
        cd ..
    fi
fi

# Start the enhanced web server
echo "🌐 Starting Enhanced Host Management API..."
echo "   API URL: http://localhost:8000"
echo "   Web Interface: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Features:"
echo "  ✅ Host Management with SSH credentials"
echo "  ✅ Playbook execution engine"
echo "  ✅ Real-time run monitoring"
echo "  ✅ Modern React frontend"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with uvicorn using the new main module
python3 -m uvicorn siemply.api.main_new:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
