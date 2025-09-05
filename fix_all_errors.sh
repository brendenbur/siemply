#!/bin/bash
# Complete Fix for All Siemply Web Interface Errors

echo "🔧 Complete Fix for All Siemply Web Interface Errors"
echo "==================================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the Siemply root directory"
    exit 1
fi

# Step 1: Fix FastAPI import error
echo "📦 Step 1: Installing missing dependencies..."
if [ -d "venv" ]; then
    echo "🔧 Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "🔧 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install all required dependencies
echo "📦 Installing FastAPI and all dependencies..."
pip install fastapi uvicorn websockets
pip install click pyyaml asyncssh cryptography

# Step 2: Fix missing static directory error
echo "📁 Step 2: Setting up web directories..."
mkdir -p web/static/css
mkdir -p web/static/js
mkdir -p web/build/static/css
mkdir -p web/build/static/js

# Create basic CSS file
cat > web/static/css/main.css << 'EOF'
/* Basic Siemply Web Interface Styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.content {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.api-link {
    display: inline-block;
    margin: 10px;
    padding: 12px 24px;
    background: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    transition: background-color 0.3s;
}

.api-link:hover {
    background: #0056b3;
    color: white;
    text-decoration: none;
}

.status {
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}

.status.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.status.info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}
EOF

# Create basic JavaScript file
cat > web/static/js/main.js << 'EOF'
// Basic Siemply Web Interface JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Siemply Web Interface loaded');
    
    // Add some basic interactivity
    const apiLinks = document.querySelectorAll('.api-link');
    apiLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            console.log('API link clicked:', this.href);
        });
    });
    
    // Check API status
    checkApiStatus();
});

async function checkApiStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        const statusElement = document.getElementById('api-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="status success">
                    ✅ API Status: ${data.status} (Version: ${data.version})
                </div>
            `;
        }
    } catch (error) {
        console.error('API status check failed:', error);
        const statusElement = document.getElementById('api-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="status error">
                    ❌ API Status: Unable to connect
                </div>
            `;
        }
    }
}
EOF

# Copy files to build directory
echo "📦 Setting up build directory..."
cp -r web/static/* web/build/static/ 2>/dev/null || true
cp web/index.html web/build/ 2>/dev/null || true

# Step 3: Test the fixes
echo "✅ Step 3: Testing the fixes..."
python3 -c "
try:
    import fastapi
    import uvicorn
    from siemply.api.main import app
    print('✅ FastAPI import successful!')
    print('✅ Static directory issue resolved!')
    print('✅ Web interface ready!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Other error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ALL ERRORS FIXED SUCCESSFULLY!"
    echo ""
    echo "✅ FastAPI import error: FIXED"
    echo "✅ Missing static directory: FIXED"
    echo "✅ Web interface: READY"
    echo ""
    echo "You can now start the web interface:"
    echo "  ./start_web_simple.sh"
    echo ""
    echo "Or test manually:"
    echo "  source venv/bin/activate"
    echo "  python3 -m uvicorn siemply.api.main:app --host 0.0.0.0 --port 8000"
else
    echo ""
    echo "❌ Some errors remain. Please check the output above."
    echo "Try running the full installation:"
    echo "  ./install_dependencies.sh"
fi
