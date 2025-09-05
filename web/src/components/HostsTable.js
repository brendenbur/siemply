import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';

export function HostsTable({ hosts }) {
  if (!hosts || hosts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No hosts found
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'healthy':
        return <span className="status-success">Healthy</span>;
      case 'warning':
        return <span className="status-warning">Warning</span>;
      case 'unhealthy':
        return <span className="status-danger">Unhealthy</span>;
      default:
        return <span className="status-gray">Unknown</span>;
    }
  };

  return (
    <div className="overflow-hidden">
      <table className="table">
        <thead className="table-header">
          <tr>
            <th className="table-header-cell">Host</th>
            <th className="table-header-cell">IP Address</th>
            <th className="table-header-cell">Splunk Type</th>
            <th className="table-header-cell">OS</th>
            <th className="table-header-cell">Status</th>
            <th className="table-header-cell">Last Check</th>
          </tr>
        </thead>
        <tbody className="table-body">
          {hosts.map((host) => (
            <tr key={host.name} className="table-row">
              <td className="table-cell">
                <div className="flex items-center">
                  {getStatusIcon(host.status)}
                  <span className="ml-2 font-medium text-gray-900">{host.name}</span>
                </div>
              </td>
              <td className="table-cell text-gray-500">{host.ip}</td>
              <td className="table-cell">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {host.splunk_type || 'Unknown'}
                </span>
              </td>
              <td className="table-cell text-gray-500">
                {host.os_family} {host.os_version}
              </td>
              <td className="table-cell">
                {getStatusBadge(host.status)}
              </td>
              <td className="table-cell text-gray-500">
                {host.last_seen || 'Never'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
