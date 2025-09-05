#!/bin/bash
# Quick Fix for FastAPI Import Error

echo "🔧 Quick Fix for FastAPI Import Error"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the Siemply root directory"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "🔧 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install missing dependencies
echo "📦 Installing FastAPI and dependencies..."
pip install fastapi uvicorn websockets
pip install click pyyaml asyncssh cryptography

# Test the fix
echo "✅ Testing the fix..."
python3 -c "
try:
    from siemply.api.main import app
    print('✅ FastAPI import successful!')
    print('✅ Web interface ready!')
except ImportError as e:
    print(f'❌ Still having issues: {e}')
    print('Try running: pip install -r requirements.txt')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Fix successful! You can now start the web interface:"
    echo "  ./start_web_simple.sh"
else
    echo ""
    echo "❌ Fix failed. Please run the full installation:"
    echo "  ./install_dependencies.sh"
fi
