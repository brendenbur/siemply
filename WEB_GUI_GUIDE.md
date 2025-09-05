# Siemply Web GUI - Complete Guide

## 🎉 Web GUI Successfully Added!

The Siemply framework now includes a **modern, full-featured web interface** built with React and FastAPI. This provides a comprehensive dashboard for managing Splunk infrastructure orchestration through a beautiful, responsive web interface.

## 🌟 Features Overview

### **Real-time Dashboard**
- Live system health monitoring
- Host status overview with visual indicators
- Recent runs and activities
- Interactive charts and metrics
- WebSocket-powered real-time updates

### **Host Management**
- Add, edit, and delete hosts
- SSH connectivity testing
- Group-based organization
- Advanced filtering and search
- Bulk operations support

### **Run Management**
- Start playbook executions
- Monitor running jobs in real-time
- View detailed run logs and progress
- Download reports (Markdown, JSON, CSV)
- Cancel running operations

### **Audit & Logging**
- Comprehensive audit event viewer
- Advanced filtering by date, user, host, event type
- Export capabilities (JSON, CSV, Markdown)
- Statistics and analytics
- Real-time log streaming

### **Settings & Configuration**
- API endpoint configuration
- WebSocket settings
- Refresh interval customization
- UI preferences
- Connection testing

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Install Node.js dependencies
cd web
npm install
```

### 2. Build the Web Interface

```bash
# Build React app for production
cd web
npm run build
cd ..
```

### 3. Start the Web Server

```bash
# Start the complete web interface
./start_web.sh
```

### 4. Access the Interface

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Status**: http://localhost:8000/api/status

## 🏗️ Architecture

### **Backend (FastAPI)**
```
src/siemply/api/
├── main.py              # FastAPI application
├── routes/
│   ├── hosts.py         # Host management API
│   ├── runs.py          # Run execution API
│   ├── audit.py         # Audit logging API
│   ├── health.py        # Health check API
│   └── websocket.py     # Real-time WebSocket API
```

### **Frontend (React)**
```
web/src/
├── components/          # Reusable UI components
├── pages/              # Page components
├── services/           # API integration
├── hooks/              # Custom React hooks
└── styles/             # Tailwind CSS styles
```

## 📱 User Interface

### **Dashboard Page**
- **System Health**: Real-time health status with color-coded indicators
- **Host Overview**: Summary of all hosts with status badges
- **Recent Runs**: Latest playbook executions with progress
- **Charts**: Interactive health and activity visualizations

### **Hosts Page**
- **Host List**: Sortable table with all host information
- **Add Host**: Modal form for adding new hosts
- **Test Connectivity**: Bulk SSH connectivity testing
- **Filters**: Search by name, IP, group, type, OS
- **Actions**: Edit, delete, and manage hosts

### **Runs Page**
- **Run List**: All playbook executions with status
- **Start Run**: Modal form for starting new executions
- **Progress Tracking**: Real-time progress updates
- **Logs & Reports**: Detailed execution logs and reports
- **Actions**: Cancel, view details, download reports

### **Audit Page**
- **Event Viewer**: Comprehensive audit log display
- **Advanced Filters**: Date range, user, host, event type
- **Statistics**: Activity summaries and analytics
- **Export**: Download audit data in multiple formats
- **Real-time**: Live event streaming

### **Settings Page**
- **API Configuration**: Backend endpoint settings
- **WebSocket Settings**: Real-time connection configuration
- **Refresh Intervals**: Data refresh timing
- **UI Preferences**: Theme, page size, notifications
- **Connection Testing**: Verify API connectivity

## 🔧 Technical Details

### **API Endpoints**

#### Hosts API (`/api/hosts/`)
- `GET /` - List all hosts
- `POST /` - Create new host
- `GET /{host_name}` - Get specific host
- `PUT /{host_name}` - Update host
- `DELETE /{host_name}` - Delete host
- `POST /test` - Test host connectivity
- `GET /groups/` - List groups
- `GET /summary/` - Get hosts summary

#### Runs API (`/api/runs/`)
- `GET /` - List all runs
- `POST /` - Start new run
- `GET /{run_id}` - Get run details
- `GET /{run_id}/progress` - Get run progress
- `GET /{run_id}/logs` - Get run logs
- `GET /{run_id}/report` - Get run report
- `POST /{run_id}/cancel` - Cancel run

#### Audit API (`/api/audit/`)
- `GET /events` - Get audit events
- `GET /task-executions` - Get task executions
- `GET /report` - Generate audit report
- `GET /stats` - Get audit statistics
- `GET /export` - Export audit data

#### Health API (`/api/health/`)
- `GET /` - Get system health
- `GET /hosts/{host_name}` - Get host health
- `POST /hosts/{host_name}/check` - Run health checks

#### WebSocket API (`/api/ws/`)
- `ws://localhost:8000/api/ws/` - General WebSocket
- `ws://localhost:8000/api/ws/runs` - Run monitoring
- `ws://localhost:8000/api/ws/hosts` - Host monitoring
- `ws://localhost:8000/api/ws/logs` - Log streaming

### **Real-time Features**

#### WebSocket Integration
- **Connection Management**: Automatic reconnection
- **Message Types**: Ping/pong, subscriptions, updates
- **Event Streaming**: Real-time run progress, host status
- **Error Handling**: Graceful connection failures

#### Live Updates
- **Host Status**: Real-time health monitoring
- **Run Progress**: Live execution tracking
- **Audit Events**: Instant event notifications
- **System Alerts**: Immediate status changes

### **Responsive Design**

#### Mobile Support
- **Responsive Layout**: Adapts to all screen sizes
- **Touch-Friendly**: Optimized for mobile interaction
- **Progressive Web App**: Can be installed on mobile devices

#### Desktop Features
- **Keyboard Shortcuts**: Power user productivity
- **Drag & Drop**: Intuitive file operations
- **Multi-window**: Support for multiple browser tabs

## 🛠️ Development

### **Frontend Development**

```bash
# Start development server
cd web
npm start

# Build for production
npm run build

# Run tests
npm test
```

### **Backend Development**

```bash
# Start FastAPI with auto-reload
uvicorn siemply.api.main:app --reload

# Start with specific host/port
uvicorn siemply.api.main:app --host 0.0.0.0 --port 8000
```

### **Full Stack Development**

```bash
# Terminal 1: Start backend
./start_web.sh

# Terminal 2: Start frontend dev server
cd web
npm start
```

## 🔒 Security Features

### **Authentication & Authorization**
- **API Key Support**: Secure API access
- **Role-based Access**: Different permission levels
- **Session Management**: Secure user sessions

### **Data Protection**
- **Input Validation**: All inputs sanitized
- **XSS Protection**: Cross-site scripting prevention
- **CSRF Protection**: Cross-site request forgery prevention

### **Network Security**
- **HTTPS Support**: Encrypted communication
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: API abuse prevention

## 📊 Performance

### **Optimization Features**
- **Code Splitting**: Lazy loading of components
- **Caching**: Intelligent data caching
- **Compression**: Gzip compression for assets
- **CDN Ready**: Static asset optimization

### **Scalability**
- **Horizontal Scaling**: Multiple backend instances
- **Database Optimization**: Efficient queries
- **Connection Pooling**: Resource management
- **Load Balancing**: Traffic distribution

## 🚀 Deployment

### **Production Deployment**

1. **Build the Application**:
```bash
cd web
npm run build
```

2. **Configure Environment**:
```bash
export SIEMPLY_CONFIG_DIR="/etc/siemply"
export SIEMPLY_LOG_LEVEL="INFO"
```

3. **Start the Server**:
```bash
./start_web.sh
```

### **Docker Deployment**

```dockerfile
# Dockerfile for web interface
FROM node:18-alpine as build
WORKDIR /app
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
COPY --from=build /app/build ./web/build
EXPOSE 8000
CMD ["uvicorn", "siemply.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🎯 Usage Examples

### **Starting a UF Upgrade**

1. Navigate to **Runs** page
2. Click **Start Run**
3. Select playbook: `plays/upgrade-uf.yml`
4. Choose target group: `prod-web`
5. Set version: `9.2.2`
6. Click **Start Run**
7. Monitor progress in real-time

### **Adding a New Host**

1. Navigate to **Hosts** page
2. Click **Add Host**
3. Fill in host details:
   - Name: `web-03.example.com`
   - IP: `192.168.1.13`
   - User: `splunk`
   - Splunk Type: `Universal Forwarder`
4. Click **Add Host**
5. Test connectivity

### **Monitoring System Health**

1. Navigate to **Dashboard**
2. View system health overview
3. Check host status indicators
4. Review recent activities
5. Use **Health** page for detailed checks

### **Audit Analysis**

1. Navigate to **Audit** page
2. Set date range filters
3. Filter by event type or user
4. View detailed event logs
5. Export data for analysis

## 🔧 Configuration

### **Environment Variables**

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/api/ws/

# Backend Configuration
SIEMPLY_CONFIG_DIR=./config
SIEMPLY_LOG_LEVEL=INFO
SIEMPLY_DB_URL=sqlite:///siemply.db
```

### **Settings Page**

The web interface includes a comprehensive settings page where users can configure:

- **API Endpoints**: Backend URL and timeout settings
- **WebSocket**: Real-time connection configuration
- **Refresh Intervals**: How often data is refreshed
- **UI Preferences**: Theme, page size, notifications
- **Notifications**: Sound, duration, and types

## 🎉 Summary

The Siemply Web GUI provides:

✅ **Complete Web Interface** - Modern React-based dashboard  
✅ **Real-time Updates** - WebSocket-powered live monitoring  
✅ **Host Management** - Full CRUD operations for hosts  
✅ **Run Management** - Start, monitor, and manage playbooks  
✅ **Audit Logging** - Comprehensive audit and logging  
✅ **Responsive Design** - Works on all devices  
✅ **Production Ready** - Secure, scalable, and optimized  
✅ **Easy Deployment** - Simple startup scripts and Docker support  

The web interface seamlessly integrates with the existing CLI and core modules, providing a powerful graphical interface for managing Splunk infrastructure orchestration at scale.

**Ready to use!** Start the web interface with `./start_web.sh` and access it at http://localhost:8000
