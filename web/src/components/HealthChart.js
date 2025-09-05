import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const COLORS = {
  healthy: '#22c55e',
  warning: '#f59e0b',
  unhealthy: '#ef4444',
  unknown: '#6b7280'
};

export function HealthChart({ data }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No health data available
      </div>
    );
  }

  const { summary, hosts = [] } = data;

  // Prepare data for pie chart
  const pieData = [
    { name: 'Healthy', value: summary.healthy_hosts || 0, color: COLORS.healthy },
    { name: 'Warning', value: summary.warning_hosts || 0, color: COLORS.warning },
    { name: 'Unhealthy', value: summary.unhealthy_hosts || 0, color: COLORS.unhealthy },
  ];

  // Prepare data for bar chart (host status over time)
  const barData = hosts.map(host => ({
    name: host.host,
    healthy: host.overall_status === 'healthy' ? 1 : 0,
    warning: host.overall_status === 'warning' ? 1 : 0,
    unhealthy: host.overall_status === 'unhealthy' ? 1 : 0,
  }));

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{summary.healthy_hosts || 0}</div>
          <div className="text-sm text-gray-500">Healthy</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{summary.warning_hosts || 0}</div>
          <div className="text-sm text-gray-500">Warning</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{summary.unhealthy_hosts || 0}</div>
          <div className="text-sm text-gray-500">Unhealthy</div>
        </div>
      </div>

      {/* Pie Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      {barData.length > 0 && (
        <div className="h-64">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Host Status</h4>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="healthy" stackId="a" fill={COLORS.healthy} name="Healthy" />
              <Bar dataKey="warning" stackId="a" fill={COLORS.warning} name="Warning" />
              <Bar dataKey="unhealthy" stackId="a" fill={COLORS.unhealthy} name="Unhealthy" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
