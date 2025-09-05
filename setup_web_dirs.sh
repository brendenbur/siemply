#!/bin/bash
# Setup Web Directories for Siemply

echo "🔧 Setting up web directories for Siemply"
echo "========================================="

# Create web directory structure
echo "📁 Creating web directory structure..."
mkdir -p web/static/css
mkdir -p web/static/js
mkdir -p web/build/static/css
mkdir -p web/build/static/js

# Copy the fallback HTML file
echo "📄 Setting up fallback HTML..."
if [ -f "web/index.html" ]; then
    echo "✅ web/index.html already exists"
else
    echo "❌ web/index.html not found. Please ensure you have the complete Siemply codebase."
    exit 1
fi

# Create a simple CSS file for basic styling
echo "🎨 Creating basic CSS..."
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

# Create a simple JavaScript file
echo "⚡ Creating basic JavaScript..."
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

# Copy files to build directory (for production)
echo "📦 Setting up build directory..."
cp -r web/static/* web/build/static/ 2>/dev/null || true
cp web/index.html web/build/ 2>/dev/null || true

echo "✅ Web directories setup complete!"
echo ""
echo "Directory structure created:"
echo "  web/static/css/main.css"
echo "  web/static/js/main.js"
echo "  web/build/static/ (copied from static)"
echo ""
echo "You can now start the web interface:"
echo "  source venv/bin/activate"
echo "  ./start_web_simple.sh"
