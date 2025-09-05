#!/bin/bash
# Fix Pydantic v2 compatibility issues

echo "🔧 Fixing Pydantic v2 compatibility issues..."

# Update requirements to use compatible versions
cat > requirements_fixed.txt << 'EOF'
# Core dependencies
click>=8.0.0
pyyaml>=6.0
asyncssh>=2.13.0
cryptography>=41.0.0

# Web API dependencies
fastapi>=0.95.0
uvicorn[standard]>=0.20.0
websockets>=11.0.0

# Database dependencies
sqlalchemy>=2.0.0
alembic>=1.10.0

# SSH and execution
paramiko>=3.0.0
jinja2>=3.1.0

# Pydantic v2 compatibility
pydantic>=2.0.0,<3.0.0

# Additional utilities
python-multipart>=0.0.6
EOF

echo "✅ Updated requirements with Pydantic v2 compatibility"

# Install the fixed requirements
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "📦 Installing fixed requirements..."
    pip install --upgrade pip
    pip install -r requirements_fixed.txt
    echo "✅ Dependencies updated successfully"
else
    echo "❌ Virtual environment not found. Please run ./start_host_management.sh first"
    exit 1
fi

echo "🎉 Pydantic compatibility fixes applied!"
echo "You can now run: ./start_host_management.sh"
