# 🔧 Siemply Dependencies Installation Guide

## ❌ **Error: ModuleNotFoundError: No module named 'fastapi'**

This error occurs when the required dependencies are not installed in your Python environment.

## 🚀 **Quick Fix**

### **Option 1: Install Dependencies (Recommended)**
```bash
# Navigate to your Siemply directory
cd /path/to/your/siemply

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### **Option 2: Install Specific Missing Packages**
```bash
# Activate your virtual environment first
source venv/bin/activate

# Install missing packages
pip install fastapi uvicorn websockets
pip install click pyyaml asyncssh cryptography
```

### **Option 3: Use Our Working Environment**
```bash
# Copy our working environment
cp -r /Users/amitkumar/Cursur/siemply/venv /path/to/your/siemply/
```

## 📋 **Required Dependencies**

### **Core Dependencies**
```
click>=8.0.0
pyyaml>=6.0
asyncssh>=2.13.0
cryptography>=41.0.0
```

### **Web API Dependencies**
```
fastapi>=0.95.0
uvicorn[standard]>=0.20.0
websockets>=11.0.0
```

## 🔍 **Troubleshooting**

### **Check Current Environment**
```bash
# Check Python version
python3 --version

# Check installed packages
pip list | grep -E "(fastapi|uvicorn|click|pyyaml)"

# Check if virtual environment is activated
echo $VIRTUAL_ENV
```

### **Common Issues**

1. **Virtual Environment Not Activated**
   ```bash
   # Solution: Activate virtual environment
   source venv/bin/activate
   ```

2. **Wrong Python Version**
   ```bash
   # Solution: Use Python 3.11+ and create new venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Permission Issues**
   ```bash
   # Solution: Use --user flag
   pip install --user -r requirements.txt
   ```

4. **Network Issues**
   ```bash
   # Solution: Use different index
   pip install -i https://pypi.org/simple/ -r requirements.txt
   ```

## ✅ **Verification**

### **Test Installation**
```bash
# Activate virtual environment
source venv/bin/activate

# Test imports
python3 -c "
import fastapi
import uvicorn
import click
import yaml
import asyncssh
print('✅ All dependencies installed successfully!')
"

# Test API startup
python3 -c "
from siemply.api.main import app
print('✅ API imports successful!')
"
```

### **Start Web Interface**
```bash
# Activate virtual environment
source venv/bin/activate

# Start web interface
./start_web_simple.sh
```

## 🎯 **Complete Installation Script**

Create this script and run it:

```bash
#!/bin/bash
# Complete Siemply Installation Script

echo "🚀 Installing Siemply Dependencies"
echo "=================================="

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $python_version"

if [ "$(echo "$python_version < 3.11" | bc -l)" -eq 1 ]; then
    echo "❌ Python 3.11+ required. Current: $python_version"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

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
import fastapi
import uvicorn
import click
import yaml
import asyncssh
print('✅ All dependencies installed successfully!')
"

echo "🎉 Installation complete!"
echo ""
echo "To start the web interface:"
echo "  source venv/bin/activate"
echo "  ./start_web_simple.sh"
```

## 📞 **Need Help?**

If you're still having issues:

1. **Check your Python version**: `python3 --version`
2. **Check your virtual environment**: `echo $VIRTUAL_ENV`
3. **Check installed packages**: `pip list`
4. **Try the complete installation script above**

---

**The fastapi module error will be resolved once dependencies are properly installed!** 🎉
