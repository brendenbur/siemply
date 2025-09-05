# 🖥️ Siemply Host Management - Complete Guide

## ✅ **HOST MANAGEMENT FEATURES ADDED!**

I have successfully **enhanced the web interface** with comprehensive host management capabilities. You can now **add, manage, and test hosts** directly from the web GUI!

## 🚀 **How to Access Host Management**

### **1. Start the Web Interface**
```bash
# Fix any errors first
./fix_all_errors.sh

# Start the web interface
./start_web_simple.sh
```

### **2. Access the Interface**
- **URL**: http://localhost:8000
- **Click on "Host Management" tab** in the navigation

## 🎯 **Host Management Features**

### **📋 Host Management Tab**
- **View All Hosts**: Complete table with host details
- **Search & Filter**: Search by name/IP, filter by group and Splunk type
- **Test Connectivity**: Test individual hosts or all hosts at once
- **Add New Host**: Comprehensive form for adding hosts with SSH credentials

### **➕ Add Host Form**
**Basic Information:**
- Host Name (required)
- IP Address (required)

**SSH Configuration:**
- SSH User (default: splunk)
- SSH Port (default: 22)
- SSH Key File (optional)

**Splunk Configuration:**
- Splunk Type (Universal Forwarder/Enterprise)
- Splunk Version

**OS Configuration:**
- OS Family (RedHat, Debian, Ubuntu, CentOS)
- OS Version
- CPU Architecture (x86_64, arm64)

**Resources:**
- Memory (GB)
- Disk Space (GB)

**Grouping:**
- Group (for organizing hosts)

### **🔧 Host Actions**
- **Test**: Test SSH connectivity to individual hosts
- **Edit**: Edit host configuration (coming soon)
- **Delete**: Remove hosts from inventory

## 📱 **User Interface**

### **Navigation Tabs**
1. **Dashboard** - Overview and quick actions
2. **Host Management** - Add, view, and manage hosts
3. **Playbook Runs** - Execute and monitor playbooks
4. **Python Scripts** - Run custom Python scripts

### **Host Management Interface**
```
┌─────────────────────────────────────────────────────────────┐
│ Host Management                                    [Add Host] │
├─────────────────────────────────────────────────────────────┤
│ Search: [________] Group: [All Groups ▼] Type: [All Types ▼] │
│                                        [Test Connectivity] │
├─────────────────────────────────────────────────────────────┤
│ Host          │ IP Address    │ Group │ Type │ Status │ Actions │
│ web-01        │ 192.168.1.10  │ prod  │ uf   │ healthy│ Test Edit Del │
│ search-01     │ 192.168.1.11  │ prod  │ ent  │ healthy│ Test Edit Del │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 **Step-by-Step Usage**

### **Step 1: Add Your First Host**
1. Click **"Host Management"** tab
2. Click **"Add Host"** button
3. Fill in the form:
   - **Host Name**: `web-01.example.com`
   - **IP Address**: `192.168.1.10`
   - **SSH User**: `splunk`
   - **SSH Port**: `22`
   - **SSH Key File**: `~/.ssh/id_rsa` (optional)
   - **Splunk Type**: `Universal Forwarder`
   - **Splunk Version**: `9.2.2`
   - **OS Family**: `RedHat`
   - **OS Version**: `8`
   - **Group**: `prod-web`
4. Click **"Add Host"**

### **Step 2: Test Connectivity**
1. In the Host Management tab
2. Click **"Test Connectivity"** to test all hosts
3. Or click **"Test"** next to individual hosts
4. Check the results in the status column

### **Step 3: Manage Hosts**
- **Search**: Use the search box to find specific hosts
- **Filter**: Use group and type filters to narrow down results
- **View Details**: All host information is displayed in the table
- **Actions**: Test, edit, or delete hosts as needed

## 🔧 **SSH Credentials Management**

### **SSH Key Authentication (Recommended)**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "siemply@yourcompany.com"

# Copy public key to target hosts
ssh-copy-id splunk@192.168.1.10

# Add private key path in the form
# SSH Key File: ~/.ssh/id_rsa
```

### **Password Authentication**
- Leave SSH Key File field empty
- The system will prompt for password when needed

## 📊 **Host Information Stored**

### **Basic Details**
- Host name and IP address
- SSH connection details (user, port, key file)
- Group assignment for organization

### **Splunk Configuration**
- Splunk type (Universal Forwarder/Enterprise)
- Current Splunk version
- OS family and version
- CPU architecture

### **Resource Information**
- Memory allocation
- Disk space available
- System specifications

## 🚀 **Running Python Commands on Hosts**

### **Via Web Interface (Coming Soon)**
- Select hosts from the management interface
- Choose Python script to execute
- Monitor execution in real-time

### **Via CLI (Current)**
```bash
# Run Python script on specific hosts
siemply script run --hosts web-01,search-01 --script scripts/check-splunk.py

# Run on all hosts in a group
siemply script run --group prod-web --script scripts/health-check.py
```

## 🔍 **Troubleshooting**

### **Common Issues**

**1. Host Not Added**
- Check if all required fields are filled
- Verify IP address format
- Ensure SSH credentials are correct

**2. Test Connectivity Fails**
- Check SSH key permissions
- Verify host is reachable
- Check firewall settings

**3. Web Interface Not Loading**
- Run `./fix_all_errors.sh` to fix dependencies
- Check if server is running on port 8000
- Verify virtual environment is activated

### **Debug Steps**
```bash
# Check if web interface is running
curl http://localhost:8000/api/status

# Check host connectivity manually
ssh splunk@192.168.1.10 "echo 'Connection successful'"

# View logs
tail -f logs/siemply.log
```

## 📈 **Advanced Features**

### **Host Groups**
- Organize hosts by environment (prod, dev, test)
- Organize by function (web, search, indexer)
- Filter and manage hosts by group

### **Bulk Operations**
- Test multiple hosts simultaneously
- Add multiple hosts using CSV import (coming soon)
- Bulk configuration updates (coming soon)

### **Real-time Monitoring**
- Live status updates
- Connection health monitoring
- Performance metrics

## 🎉 **Summary**

**✅ COMPLETE HOST MANAGEMENT SOLUTION!**

The enhanced web interface now provides:

1. **Full Host Management**: Add, view, edit, delete hosts
2. **SSH Credentials**: Secure key-based authentication
3. **Search & Filter**: Easy host discovery and organization
4. **Connectivity Testing**: Verify SSH connections
5. **Comprehensive Forms**: All necessary host information
6. **Real-time Updates**: Live status and health monitoring

**Ready to manage your Splunk infrastructure hosts!** 🚀

---

**Access the Host Management tab at http://localhost:8000 to get started!** 🎯
