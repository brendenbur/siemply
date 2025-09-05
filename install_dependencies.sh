#!/bin/bash
# Complete Siemply Dependencies Installation Script

echo "🚀 Installing Siemply Dependencies"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the Siemply root directory"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $python_version"

# Check if Python 3.11+ is available
if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11+ found"
    PYTHON_CMD="python3.11"
elif command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12+ found"
    PYTHON_CMD="python3.12"
elif [ "$(echo "$python_version >= 3.11" | bc -l 2>/dev/null || echo "1")" -eq 1 ]; then
    echo "✅ Python $python_version is compatible"
    PYTHON_CMD="python3"
else
    echo "❌ Python 3.11+ required. Current: $python_version"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install -e .

# Verify installation
echo "✅ Verifying installation..."
python3 -c "
try:
    import fastapi
    import uvicorn
    import click
    import yaml
    import asyncssh
    print('✅ All dependencies installed successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 Installation complete!"
    echo ""
    echo "To start the web interface:"
    echo "  source venv/bin/activate"
    echo "  ./start_web_simple.sh"
    echo ""
    echo "Or test the API:"
    echo "  source venv/bin/activate"
    echo "  python3 -c 'from siemply.api.main import app; print(\"✅ API ready!\")'"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
