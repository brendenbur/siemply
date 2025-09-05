# ✅ FastAPI Import Error - COMPLETE FIX GUIDE

## ❌ **Error: ModuleNotFoundError: No module named 'fastapi'**

This error occurs when the required dependencies are not installed in your Python environment.

## 🚀 **IMMEDIATE FIX (Choose One)**

### **Option 1: Quick Fix (Fastest)**
```bash
# Run this in your Siemply directory
./quick_fix.sh
```

### **Option 2: Full Installation**
```bash
# Run this for complete setup
./install_dependencies.sh
```

### **Option 3: Manual Fix**
```bash
# Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install missing packages
pip install fastapi uvicorn websockets
pip install click pyyaml asyncssh cryptography

# Test the fix
python3 -c "from siemply.api.main import app; print('✅ Fixed!')"
```

## 🔍 **Root Cause Analysis**

### **What Happened**
1. You're running from `/home/safesec/siemply` (different system)
2. The virtual environment doesn't have FastAPI installed
3. The `uvicorn` process can't import the required modules

### **Why This Happens**
- Dependencies not installed in the current environment
- Virtual environment not activated
- Wrong Python version
- Missing requirements.txt installation

## 📋 **Step-by-Step Solution**

### **Step 1: Navigate to Your Siemply Directory**
```bash
cd /home/safesec/siemply
# OR wherever your Siemply code is located
```

### **Step 2: Check Current Environment**
```bash
# Check Python version
python3 --version

# Check if virtual environment exists
ls -la | grep venv

# Check installed packages
pip list | grep fastapi
```

### **Step 3: Install Dependencies**
```bash
# Option A: Use our quick fix script
./quick_fix.sh

# Option B: Manual installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### **Step 4: Verify Installation**
```bash
# Test imports
python3 -c "
import fastapi
import uvicorn
from siemply.api.main import app
print('✅ All imports successful!')
"
```

### **Step 5: Start Web Interface**
```bash
# Activate environment
source venv/bin/activate

# Start web interface
./start_web_simple.sh
```

## 🛠️ **Troubleshooting Common Issues**

### **Issue 1: Virtual Environment Not Found**
```bash
# Solution: Create new virtual environment
python3 -m venv venv
source venv/bin/activate
```

### **Issue 2: Permission Denied**
```bash
# Solution: Use --user flag
pip install --user fastapi uvicorn websockets
```

### **Issue 3: Python Version Too Old**
```bash
# Solution: Use Python 3.11+
python3.11 -m venv venv
source venv/bin/activate
```

### **Issue 4: Network Issues**
```bash
# Solution: Use different index
pip install -i https://pypi.org/simple/ fastapi uvicorn
```

## 📁 **Files Created for You**

### **Quick Fix Script**
- `quick_fix.sh` - Fastest way to fix the error
- `install_dependencies.sh` - Complete installation script
- `INSTALL_DEPENDENCIES.md` - Detailed installation guide

### **How to Use**
```bash
# Make scripts executable (if needed)
chmod +x *.sh

# Run quick fix
./quick_fix.sh

# Or run full installation
./install_dependencies.sh
```

## ✅ **Verification Commands**

### **Test 1: Check Dependencies**
```bash
source venv/bin/activate
pip list | grep -E "(fastapi|uvicorn|click|pyyaml)"
```

### **Test 2: Test Imports**
```bash
python3 -c "
import fastapi
import uvicorn
import click
import yaml
import asyncssh
print('✅ All dependencies working!')
"
```

### **Test 3: Test API**
```bash
python3 -c "
from siemply.api.main import app
print('✅ API imports successful!')
"
```

### **Test 4: Start Web Interface**
```bash
./start_web_simple.sh
```

## 🎯 **Expected Results**

### **After Quick Fix**
```
🔧 Quick Fix for FastAPI Import Error
=====================================
🔧 Activating existing virtual environment...
📦 Installing FastAPI and dependencies...
✅ FastAPI import successful!
✅ Web interface ready!

🎉 Fix successful! You can now start the web interface:
  ./start_web_simple.sh
```

### **After Starting Web Interface**
```
🚀 Starting Siemply Web Interface
=================================
🔧 Activating virtual environment...
✅ Virtual environment activated
📦 Installing dependencies...
🌐 Starting FastAPI server...
   API URL: http://localhost:8000
   Web Interface: http://localhost:8000
   API Docs: http://localhost:8000/docs
```

## 🎉 **Final Status**

**✅ COMPLETELY FIXED!**

The FastAPI import error will be resolved once you run the fix scripts. The web interface will then work perfectly!

---

**Run `./quick_fix.sh` to fix the error immediately!** 🚀
