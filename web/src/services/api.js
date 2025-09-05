import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Health
  health: '/api/health/',
  systemHealth: '/api/health/',
  hostHealth: (hostName) => `/api/health/hosts/${hostName}`,
  
  // Hosts
  hosts: '/api/hosts/',
  host: (hostName) => `/api/hosts/${hostName}`,
  hostGroups: '/api/hosts/groups/',
  hostGroup: (groupName) => `/api/hosts/groups/${groupName}/hosts`,
  hostsSummary: '/api/hosts/summary/',
  testHosts: '/api/hosts/test',
  
  // Runs
  runs: '/api/runs/',
  run: (runId) => `/api/runs/${runId}`,
  runProgress: (runId) => `/api/runs/${runId}/progress`,
  runLogs: (runId) => `/api/runs/${runId}/logs`,
  runReport: (runId) => `/api/runs/${runId}/report`,
  cancelRun: (runId) => `/api/runs/${runId}/cancel`,
  
  // Audit
  auditEvents: '/api/audit/events',
  taskExecutions: '/api/audit/task-executions',
  auditReport: '/api/audit/report',
  runSummary: (runId) => `/api/audit/runs/${runId}/summary`,
  auditStats: '/api/audit/stats',
  cleanupAudit: '/api/audit/cleanup',
  exportAudit: '/api/audit/export',
  
  // WebSocket
  websocket: '/api/ws/',
  websocketRuns: '/api/ws/runs',
  websocketHosts: '/api/ws/hosts',
  websocketLogs: '/api/ws/logs',
};

// Helper functions
export const apiHelpers = {
  // Format error messages
  formatError: (error) => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  },
  
  // Handle API errors
  handleError: (error, defaultMessage = 'An error occurred') => {
    console.error('API Error:', error);
    return apiHelpers.formatError(error) || defaultMessage;
  },
  
  // Retry failed requests
  retry: async (fn, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  },
};

export default api;
