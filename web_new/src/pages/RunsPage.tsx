import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Play, Eye, Trash2, X } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { api } from '../lib/api'

export function RunsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [showLogs, setShowLogs] = useState(false)
  
  const queryClient = useQueryClient()

  const { data: runs = [], isLoading, error } = useQuery({
    queryKey: ['runs'],
    queryFn: () => api.get('/runs').then(res => res.data),
  })

  const deleteRunMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/runs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      toast.success('Run deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete run')
    },
  })

  const cancelRunMutation = useMutation({
    mutationFn: (id: string) => api.post(`/runs/${id}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      toast.success('Run cancelled successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel run')
    },
  })

  const filteredRuns = runs.filter((run: any) => {
    const matchesSearch = run.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         run.status.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this run?')) {
      deleteRunMutation.mutate(id)
    }
  }

  const handleCancel = (id: string) => {
    if (window.confirm('Are you sure you want to cancel this run?')) {
      cancelRunMutation.mutate(id)
    }
  }

  const handleViewLogs = (run: any) => {
    setSelectedRun(run)
    setShowLogs(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'partial':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">Failed to load runs</div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Playbook Runs</h1>
            <p className="mt-1 text-sm text-gray-500">
              Monitor and manage playbook executions
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6 bg-white shadow rounded-lg">
        <div className="p-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search runs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>
      </div>

      {/* Runs Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-12">
            <Play className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No runs yet</h3>
            <p className="mt-1 text-sm text-gray-500">Execute a playbook to see runs here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hosts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRuns.map((run: any) => (
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {run.id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.host_ids.length} host{run.host_ids.length !== 1 ? 's' : ''}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.ended_at 
                        ? `${Math.round((new Date(run.ended_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                        : 'Running...'
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleViewLogs(run)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {run.status === 'running' && (
                          <button
                            onClick={() => handleCancel(run.id)}
                            className="text-orange-600 hover:text-orange-900"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(run.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Logs Modal */}
      {showLogs && selectedRun && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowLogs(false)} />
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Run Logs - {selectedRun.id.slice(0, 8)}...
                  </h3>
                  <button
                    onClick={() => setShowLogs(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
                
                <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm text-green-400 whitespace-pre-wrap">
                    {selectedRun.logs?.map((log: any) => 
                      `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`
                    ).join('\n') || 'No logs available'}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
