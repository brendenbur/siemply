import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Filter, RefreshCw, TestTube, MoreVertical } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { HostsTable } from '../components/HostsTable'
import { HostModal } from '../components/HostModal'
import { TestSSHModal } from '../components/TestSSHModal'
import { RunPlaybookModal } from '../components/RunPlaybookModal'
import { api } from '../lib/api'

export function HostsPage() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [showTestModal, setShowTestModal] = useState(false)
  const [showRunModal, setShowRunModal] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedHosts, setSelectedHosts] = useState<string[]>([])
  const [editingHost, setEditingHost] = useState<any>(null)
  
  const queryClient = useQueryClient()

  const { data: hosts = [], isLoading, error } = useQuery({
    queryKey: ['hosts'],
    queryFn: () => api.get('/hosts').then(res => res.data),
  })

  const addHostMutation = useMutation({
    mutationFn: (hostData: any) => api.post('/hosts', hostData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] })
      setShowAddModal(false)
      toast.success('Host added successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add host')
    },
  })

  const updateHostMutation = useMutation({
    mutationFn: ({ id, ...data }: any) => api.put(`/hosts/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] })
      setEditingHost(null)
      toast.success('Host updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update host')
    },
  })

  const deleteHostMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/hosts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] })
      toast.success('Host deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete host')
    },
  })

  const testSSHMutation = useMutation({
    mutationFn: (hostIds: string[]) => api.post('/hosts/test-ssh-bulk', { host_ids: hostIds }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] })
      const successCount = data.data.filter((r: any) => r.success).length
      const failCount = data.data.filter((r: any) => !r.success).length
      toast.success(`SSH test completed: ${successCount} successful, ${failCount} failed`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to test SSH')
    },
  })

  const filteredHosts = hosts.filter((host: any) => {
    const matchesSearch = host.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         host.ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         host.labels.some((label: string) => 
                           label.toLowerCase().includes(searchTerm.toLowerCase())
                         )
    return matchesSearch
  })

  const handleAddHost = (hostData: any) => {
    addHostMutation.mutate(hostData)
  }

  const handleUpdateHost = (hostData: any) => {
    updateHostMutation.mutate(hostData)
  }

  const handleDeleteHost = (id: string) => {
    if (window.confirm('Are you sure you want to delete this host?')) {
      deleteHostMutation.mutate(id)
    }
  }

  const handleTestSSH = (hostIds: string[]) => {
    testSSHMutation.mutate(hostIds)
  }

  const handleRunPlaybook = (hostIds: string[]) => {
    setSelectedHosts(hostIds)
    setShowRunModal(true)
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">Failed to load hosts</div>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['hosts'] })}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </button>
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
            <h1 className="text-2xl font-bold text-gray-900">Host Management</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage your Splunk infrastructure hosts
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowTestModal(true)}
              disabled={testSSHMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <TestTube className="h-4 w-4 mr-2" />
              Test SSH
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Host
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 bg-white shadow rounded-lg">
        <div className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search hosts by name, IP, or labels..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>
            <button
              onClick={() => setSearchTerm('')}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Filter className="h-4 w-4 mr-2" />
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Hosts Table */}
      <div className="bg-white shadow rounded-lg">
        <HostsTable
          hosts={filteredHosts}
          isLoading={isLoading}
          selectedHosts={selectedHosts}
          onSelectionChange={setSelectedHosts}
          onEdit={(host) => {
            setEditingHost(host)
            setShowAddModal(true)
          }}
          onDelete={handleDeleteHost}
          onTestSSH={handleTestSSH}
          onRunPlaybook={handleRunPlaybook}
        />
      </div>

      {/* Modals */}
      {showAddModal && (
        <HostModal
          host={editingHost}
          onClose={() => {
            setShowAddModal(false)
            setEditingHost(null)
          }}
          onSave={editingHost ? handleUpdateHost : handleAddHost}
          isLoading={addHostMutation.isPending || updateHostMutation.isPending}
        />
      )}

      {showTestModal && (
        <TestSSHModal
          hosts={hosts}
          onClose={() => setShowTestModal(false)}
          onTest={handleTestSSH}
          isLoading={testSSHMutation.isPending}
        />
      )}

      {showRunModal && (
        <RunPlaybookModal
          hostIds={selectedHosts}
          onClose={() => setShowRunModal(false)}
        />
      )}
    </div>
  )
}
