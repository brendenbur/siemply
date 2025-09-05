import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Download, Filter, RefreshCw, Calendar, User, Server } from 'lucide-react';
import { api, apiHelpers } from '../services/api';
import toast from 'react-hot-toast';

export function Audit() {
  const [filters, setFilters] = useState({
    start_time: '',
    end_time: '',
    event_type: '',
    user: '',
    host: '',
    limit: 100,
  });

  const { data: events, isLoading, error, refetch } = useQuery(
    ['auditEvents', filters],
    () => api.get('/api/audit/events', { params: filters }).then(res => res.data),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: stats } = useQuery(
    'auditStats',
    () => api.get('/api/audit/stats').then(res => res.data),
  );

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleExport = async () => {
    try {
      const response = await api.get('/api/audit/export', {
        params: filters,
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Audit data exported successfully');
    } catch (error) {
      toast.error(apiHelpers.handleError(error, 'Failed to export audit data'));
    }
  };

  const handleClearFilters = () => {
    setFilters({
      start_time: '',
      end_time: '',
      event_type: '',
      user: '',
      host: '',
      limit: 100,
    });
  };

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">Failed to load audit events</div>
        <button
          onClick={() => refetch()}
          className="btn btn-primary"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit</h1>
          <p className="mt-1 text-sm text-gray-500">
            View and analyze system audit logs
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleExport}
            className="btn btn-outline"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                    <Calendar className="h-5 w-5 text-blue-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Events</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.total_events}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                    <User className="h-5 w-5 text-green-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Active Users</p>
                  <p className="text-2xl font-semibold text-gray-900">{Object.keys(stats.user_counts || {}).length}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                    <Server className="h-5 w-5 text-purple-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Active Hosts</p>
                  <p className="text-2xl font-semibold text-gray-900">{Object.keys(stats.host_counts || {}).length}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                    <Calendar className="h-5 w-5 text-yellow-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Period (Days)</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.period_days}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="form-label">Start Time</label>
              <input
                type="datetime-local"
                value={filters.start_time}
                onChange={(e) => handleFilterChange('start_time', e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">End Time</label>
              <input
                type="datetime-local"
                value={filters.end_time}
                onChange={(e) => handleFilterChange('end_time', e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">Event Type</label>
              <select
                value={filters.event_type}
                onChange={(e) => handleFilterChange('event_type', e.target.value)}
                className="form-input"
              >
                <option value="">All Types</option>
                <option value="run_started">Run Started</option>
                <option value="run_completed">Run Completed</option>
                <option value="run_failed">Run Failed</option>
                <option value="host_added">Host Added</option>
                <option value="host_updated">Host Updated</option>
                <option value="host_removed">Host Removed</option>
                <option value="task_executed">Task Executed</option>
              </select>
            </div>
            
            <div>
              <label className="form-label">User</label>
              <input
                type="text"
                value={filters.user}
                onChange={(e) => handleFilterChange('user', e.target.value)}
                className="form-input"
                placeholder="Filter by user"
              />
            </div>
            
            <div>
              <label className="form-label">Host</label>
              <input
                type="text"
                value={filters.host}
                onChange={(e) => handleFilterChange('host', e.target.value)}
                className="form-input"
                placeholder="Filter by host"
              />
            </div>
            
            <div>
              <label className="form-label">Limit</label>
              <input
                type="number"
                value={filters.limit}
                onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
                className="form-input"
                min="1"
                max="1000"
              />
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleClearFilters}
              className="btn btn-outline"
            >
              <Filter className="h-4 w-4 mr-2" />
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Events Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">
            Audit Events ({events?.length || 0})
          </h3>
        </div>
        <div className="card-body">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <AuditEventsTable events={events || []} />
          )}
        </div>
      </div>
    </div>
  );
}

// Audit Events Table Component
function AuditEventsTable({ events }) {
  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No audit events found
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <span className="status-success">Success</span>;
      case 'failed':
        return <span className="status-danger">Failed</span>;
      case 'warning':
        return <span className="status-warning">Warning</span>;
      default:
        return <span className="status-gray">Unknown</span>;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="overflow-hidden">
      <table className="table">
        <thead className="table-header">
          <tr>
            <th className="table-header-cell">Timestamp</th>
            <th className="table-header-cell">Event Type</th>
            <th className="table-header-cell">User</th>
            <th className="table-header-cell">Host</th>
            <th className="table-header-cell">Action</th>
            <th className="table-header-cell">Status</th>
            <th className="table-header-cell">Duration</th>
          </tr>
        </thead>
        <tbody className="table-body">
          {events.map((event) => (
            <tr key={event.event_id} className="table-row">
              <td className="table-cell text-sm text-gray-500">
                {formatDate(event.timestamp)}
              </td>
              <td className="table-cell">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {event.event_type}
                </span>
              </td>
              <td className="table-cell text-gray-900">{event.user}</td>
              <td className="table-cell text-gray-900">{event.host}</td>
              <td className="table-cell text-gray-900">{event.action}</td>
              <td className="table-cell">
                {getStatusBadge(event.status)}
              </td>
              <td className="table-cell text-gray-500">
                {event.duration ? `${event.duration.toFixed(2)}s` : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
