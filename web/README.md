# Siemply Web Interface

A modern React-based web interface for the Siemply Splunk Infrastructure Orchestration Framework.

## Features

- **Real-time Dashboard**: Live monitoring of hosts, runs, and system health
- **Host Management**: Add, edit, and manage Splunk infrastructure hosts
- **Run Management**: Start, monitor, and manage playbook executions
- **Audit Logging**: View and analyze system audit logs
- **WebSocket Support**: Real-time updates and notifications
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Frontend**: React 18, React Router, React Query
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.11+ (for the backend API)
- Siemply backend running on port 8000

### Installation

1. Install dependencies:
```bash
cd web
npm install
```

2. Build the application:
```bash
npm run build
```

3. Start the development server:
```bash
npm start
```

The web interface will be available at `http://localhost:3000` (development) or served by the FastAPI backend at `http://localhost:8000` (production).

### Development

For development with hot reloading:

```bash
npm start
```

This will start the React development server with proxy configuration to the FastAPI backend.

### Building for Production

```bash
npm run build
```

This creates a `build` directory with optimized production files.

## Project Structure

```
web/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   ├── pages/             # Page components
│   ├── services/          # API services
│   ├── hooks/             # Custom React hooks
│   ├── styles/            # CSS styles
│   └── App.js             # Main application component
├── package.json           # Dependencies and scripts
└── tailwind.config.js     # Tailwind CSS configuration
```

## API Integration

The web interface communicates with the Siemply FastAPI backend through:

- **REST API**: For CRUD operations on hosts, runs, and audit data
- **WebSocket**: For real-time updates and notifications
- **File Upload/Download**: For reports and exports

## Configuration

The web interface can be configured through the Settings page or environment variables:

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)
- `REACT_APP_WS_URL`: WebSocket URL (default: ws://localhost:8000/api/ws/)

## Features Overview

### Dashboard
- System health overview
- Host status summary
- Recent runs and activities
- Real-time charts and metrics

### Hosts
- List and search hosts
- Add new hosts with SSH configuration
- Test host connectivity
- Filter by group, type, and OS

### Runs
- Start new playbook executions
- Monitor running jobs
- View run details and logs
- Download reports

### Audit
- View audit events and logs
- Filter by date, user, host, and event type
- Export audit data
- View statistics and analytics

### Settings
- Configure API endpoints
- Set refresh intervals
- Customize UI preferences
- Test connections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
