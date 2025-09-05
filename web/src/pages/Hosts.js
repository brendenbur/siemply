import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Plus, Search, Filter, RefreshCw, TestTube } from 'lucide-react';
import { HostsTable } from '../components/HostsTable';
import { HostForm } from '../components/HostForm';
import { api, apiHelpers } from '../services/api';
import toast from 'react-hot-toast';

export function Hosts() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterGroup, setFilterGroup] = useState('');
  const [filterType, setFilterType] = useState('');
  const queryClient = useQueryClient();

  const { data: hosts, isLoading, error } = useQuery(
    'hosts',
    () => api.get('/api/hosts/').then(res => res.data),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const { data: groups } = useQuery(
    'hostGroups',
    () => api.get('/api/hosts/groups/').then(res => res.data),
  );

  const addHostMutation = useMutation(
    (hostData) => api.post('/api/hosts/', hostData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('hosts');
        setShowAddForm(false);
        toast.success('Host added successfully');
      },
      onError: (error) => {
        toast.error(apiHelpers.handleError(error, 'Failed to add host'));
      },
    }
  );

  const testHostsMutation = useMutation(
    (hostNames) => api.post('/api/hosts/test', hostNames),
    {
      onSuccess: (response) => {
        const results = response.data;
        const successCount = results.filter(r => r.status === 'success').length;
        const failCount = results.filter(r => r.status === 'failed').length;
        toast.success(`Test completed: ${successCount} successful, ${failCount} failed`);
      },
      onError: (error) => {
        toast.error(apiHelpers.handleError(error, 'Failed to test hosts'));
      },
    }
  );

  const filteredHosts = hosts?.filter(host => {
    const matchesSearch = host.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         host.ip.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesGroup = !filterGroup || host.group === filterGroup;
    const matchesType = !filterType || host.splunk_type === filterType;
    return matchesSearch && matchesGroup && matchesType;
  }) || [];

  const handleAddHost = (hostData) => {
    addHostMutation.mutate(hostData);
  };

  const handleTestHosts = () => {
    const hostNames = filteredHosts.map(host => host.name);
    if (hostNames.length === 0) {
      toast.error('No hosts to test');
      return;
    }
    testHostsMutation.mutate(hostNames);
  };

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">Failed to load hosts</div>
        <button
          onClick={() => queryClient.invalidateQueries('hosts')}
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
          <h1 className="text-2xl font-bold text-gray-900">Hosts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your Splunk infrastructure hosts
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleTestHosts}
            disabled={testHostsMutation.isLoading}
            className="btn btn-outline"
          >
            <TestTube className="h-4 w-4 mr-2" />
            Test Connectivity
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Host
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div>
              <label className="form-label">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search hosts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="form-input pl-10"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Group</label>
              <select
                value={filterGroup}
                onChange={(e) => setFilterGroup(e.target.value)}
                className="form-input"
              >
                <option value="">All Groups</option>
                {groups?.map(group => (
                  <option key={group} value={group}>{group}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Splunk Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="form-input"
              >
                <option value="">All Types</option>
                <option value="uf">Universal Forwarder</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterGroup('');
                  setFilterType('');
                }}
                className="btn btn-outline w-full"
              >
                <Filter className="h-4 w-4 mr-2" />
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hosts Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">
            Hosts ({filteredHosts.length})
          </h3>
        </div>
        <div className="card-body">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <HostsTable hosts={filteredHosts} />
          )}
        </div>
      </div>

      {/* Add Host Modal */}
      {showAddForm && (
        <HostForm
          onClose={() => setShowAddForm(false)}
          onSubmit={handleAddHost}
          isLoading={addHostMutation.isLoading}
        />
      )}
    </div>
  );
}
