import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Play, Plus, RefreshCw, X } from 'lucide-react';
import { RunsTable } from '../components/RunsTable';
import { RunForm } from '../components/RunForm';
import { api, apiHelpers } from '../services/api';
import toast from 'react-hot-toast';

export function Runs() {
  const [showRunForm, setShowRunForm] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const queryClient = useQueryClient();

  const { data: runs, isLoading, error } = useQuery(
    'runs',
    () => api.get('/api/runs/').then(res => res.data),
    {
      refetchInterval: 10000, // Refresh every 10 seconds
    }
  );

  const createRunMutation = useMutation(
    (runData) => api.post('/api/runs/', runData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('runs');
        setShowRunForm(false);
        toast.success('Run started successfully');
      },
      onError: (error) => {
        toast.error(apiHelpers.handleError(error, 'Failed to start run'));
      },
    }
  );

  const cancelRunMutation = useMutation(
    (runId) => api.post(`/api/runs/${runId}/cancel`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('runs');
        toast.success('Run cancelled successfully');
      },
      onError: (error) => {
        toast.error(apiHelpers.handleError(error, 'Failed to cancel run'));
      },
    }
  );

  const handleCreateRun = (runData) => {
    createRunMutation.mutate(runData);
  };

  const handleCancelRun = (runId) => {
    if (window.confirm('Are you sure you want to cancel this run?')) {
      cancelRunMutation.mutate(runId);
    }
  };

  const handleViewRun = (run) => {
    setSelectedRun(run);
  };

  const handleDownloadReport = async (runId) => {
    try {
      const response = await api.get(`/api/runs/${runId}/report?format=markdown`);
      const blob = new Blob([response.data.report], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `run-${runId}-report.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Report downloaded successfully');
    } catch (error) {
      toast.error(apiHelpers.handleError(error, 'Failed to download report'));
    }
  };

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">Failed to load runs</div>
        <button
          onClick={() => queryClient.invalidateQueries('runs')}
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
          <h1 className="text-2xl font-bold text-gray-900">Runs</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and monitor playbook executions
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowRunForm(true)}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Start Run
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                  <Play className="h-5 w-5 text-blue-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Runs</p>
                <p className="text-2xl font-semibold text-gray-900">{runs?.length || 0}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                  <Play className="h-5 w-5 text-green-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {runs?.filter(r => r.status === 'completed').length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                  <Play className="h-5 w-5 text-yellow-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Running</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {runs?.filter(r => r.status === 'running').length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
                  <Play className="h-5 w-5 text-red-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Failed</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {runs?.filter(r => r.status === 'failed').length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Runs Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">
            Runs ({runs?.length || 0})
          </h3>
        </div>
        <div className="card-body">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <RunsTable 
              runs={runs || []} 
              onView={handleViewRun}
              onCancel={handleCancelRun}
              onDownload={handleDownloadReport}
            />
          )}
        </div>
      </div>

      {/* Start Run Modal */}
      {showRunForm && (
        <RunForm
          onClose={() => setShowRunForm(false)}
          onSubmit={handleCreateRun}
          isLoading={createRunMutation.isLoading}
        />
      )}

      {/* Run Details Modal */}
      {selectedRun && (
        <RunDetails
          run={selectedRun}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </div>
  );
}

// Run Details Component
function RunDetails({ run, onClose }) {
  const { data: runDetails, isLoading } = useQuery(
    ['run', run.run_id],
    () => api.get(`/api/runs/${run.run_id}`).then(res => res.data),
    {
      enabled: !!run.run_id,
    }
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Run Details</h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="loading-spinner"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Run Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Run ID</label>
                    <p className="text-sm text-gray-900 font-mono">{runDetails?.run_id}</p>
                  </div>
                  <div>
                    <label className="form-label">Status</label>
                    <p className="text-sm text-gray-900">{runDetails?.status}</p>
                  </div>
                </div>
                
                {/* Results */}
                <div>
                  <label className="form-label">Results</label>
                  <pre className="text-xs bg-gray-100 p-4 rounded-md overflow-auto max-h-64">
                    {JSON.stringify(runDetails?.results, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
