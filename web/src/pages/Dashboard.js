import React from 'react';
import { useQuery } from 'react-query';
import { 
  Server, 
  Play, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Activity,
  Clock,
  Users
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { HostsTable } from '../components/HostsTable';
import { RunsTable } from '../components/RunsTable';
import { HealthChart } from '../components/HealthChart';
import { api } from '../services/api';

export function Dashboard() {
  const { data: systemHealth, isLoading: healthLoading } = useQuery(
    'systemHealth',
    () => api.get('/api/health/'),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: hosts, isLoading: hostsLoading } = useQuery(
    'hosts',
    () => api.get('/api/hosts/'),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const { data: runs, isLoading: runsLoading } = useQuery(
    'runs',
    () => api.get('/api/runs/'),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  const stats = [
    {
      name: 'Total Hosts',
      value: hosts?.length || 0,
      icon: Server,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Healthy Hosts',
      value: systemHealth?.summary?.healthy_hosts || 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Active Runs',
      value: runs?.filter(run => run.status === 'running').length || 0,
      icon: Play,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Failed Hosts',
      value: systemHealth?.summary?.unhealthy_hosts || 0,
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
  ];

  const recentRuns = runs?.slice(0, 5) || [];
  const recentHosts = hosts?.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your Splunk infrastructure orchestration
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.name} {...stat} />
        ))}
      </div>

      {/* Charts and Tables */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Health Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">System Health</h3>
          </div>
          <div className="card-body">
            {healthLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="loading-spinner"></div>
              </div>
            ) : (
              <HealthChart data={systemHealth} />
            )}
          </div>
        </div>

        {/* Recent Runs */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Recent Runs</h3>
          </div>
          <div className="card-body">
            {runsLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="loading-spinner"></div>
              </div>
            ) : (
              <RunsTable runs={recentRuns} />
            )}
          </div>
        </div>
      </div>

      {/* Hosts Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Hosts Overview</h3>
        </div>
        <div className="card-body">
          {hostsLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <HostsTable hosts={recentHosts} />
          )}
        </div>
      </div>
    </div>
  );
}
