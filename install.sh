#!/bin/bash
# Siemply Installation Script

set -e

echo "🚀 Installing Siemply - Splunk Infrastructure Orchestration Framework"
echo "=================================================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected. Consider using a virtual environment:"
    echo "   python3 -m venv siemply-env"
    echo "   source siemply-env/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install the package
echo "📦 Installing Siemply..."
pip install -e .

# Verify installation
echo "🔍 Verifying installation..."
if command -v siemply &> /dev/null; then
    echo "✅ Siemply CLI installed successfully"
    siemply --version
else
    echo "❌ Installation failed - siemply command not found"
    exit 1
fi

# Create example project
echo "📁 Creating example project..."
if [ ! -d "example-project" ]; then
    siemply init example-project
    echo "✅ Example project created in 'example-project' directory"
else
    echo "ℹ️  Example project already exists"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. cd example-project"
echo "2. Edit config/inventory.yml with your hosts"
echo "3. Edit config/ssh_profiles.yml with your SSH settings"
echo "4. Run: siemply hosts test --all"
echo "5. Run: siemply run -p plays/upgrade-uf.yml -g prod-web --dry-run"
echo ""
echo "For more information, see:"
echo "- README.md"
echo "- docs/getting-started.md"
echo "- CLI_EXAMPLES.md"
