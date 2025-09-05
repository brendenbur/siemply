import React from 'react';
import { Play, CheckCircle, XCircle, Clock, Pause, Eye, Download, X } from 'lucide-react';

export function RunsTable({ runs, onView, onCancel, onDownload }) {
  if (!runs || runs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No runs found
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <Pause className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'running':
        return <span className="status-info">Running</span>;
      case 'completed':
        return <span className="status-success">Completed</span>;
      case 'failed':
        return <span className="status-danger">Failed</span>;
      case 'cancelled':
        return <span className="status-gray">Cancelled</span>;
      default:
        return <span className="status-gray">Unknown</span>;
    }
  };

  const formatDuration = (duration) => {
    if (!duration) return '-';
    if (duration < 60) return `${duration.toFixed(1)}s`;
    if (duration < 3600) return `${(duration / 60).toFixed(1)}m`;
    return `${(duration / 3600).toFixed(1)}h`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="overflow-hidden">
      <table className="table">
        <thead className="table-header">
          <tr>
            <th className="table-header-cell">Run ID</th>
            <th className="table-header-cell">Status</th>
            <th className="table-header-cell">Playbook</th>
            <th className="table-header-cell">Hosts</th>
            <th className="table-header-cell">Duration</th>
            <th className="table-header-cell">Started</th>
            <th className="table-header-cell">Actions</th>
          </tr>
        </thead>
        <tbody className="table-body">
          {runs.map((run) => (
            <tr key={run.run_id} className="table-row">
              <td className="table-cell">
                <div className="flex items-center">
                  {getStatusIcon(run.status)}
                  <span className="ml-2 font-mono text-sm text-gray-900">{run.run_id}</span>
                </div>
              </td>
              <td className="table-cell">
                {getStatusBadge(run.status)}
              </td>
              <td className="table-cell text-gray-500">
                {run.playbook || 'Unknown'}
              </td>
              <td className="table-cell">
                <div className="text-sm">
                  <div className="text-gray-900">{run.total_hosts || 0} total</div>
                  <div className="text-gray-500">
                    {run.successful_hosts || 0} success, {run.failed_hosts || 0} failed
                  </div>
                </div>
              </td>
              <td className="table-cell text-gray-500">
                {formatDuration(run.duration)}
              </td>
              <td className="table-cell text-gray-500">
                {formatDate(run.start_time)}
              </td>
              <td className="table-cell">
                <div className="flex space-x-2">
                  {onView && (
                    <button
                      onClick={() => onView(run)}
                      className="text-blue-600 hover:text-blue-800"
                      title="View Details"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  )}
                  {onDownload && (
                    <button
                      onClick={() => onDownload(run.run_id)}
                      className="text-green-600 hover:text-green-800"
                      title="Download Report"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  )}
                  {run.status === 'running' && onCancel && (
                    <button
                      onClick={() => onCancel(run.run_id)}
                      className="text-red-600 hover:text-red-800"
                      title="Cancel Run"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
