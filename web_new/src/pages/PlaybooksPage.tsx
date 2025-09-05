import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, FileText, Edit, Trash2, Copy } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { api } from '../lib/api'

export function PlaybooksPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingPlaybook, setEditingPlaybook] = useState<any>(null)
  
  const queryClient = useQueryClient()

  const { data: playbooks = [], isLoading, error } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => api.get('/playbooks').then(res => res.data),
  })

  const deletePlaybookMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/playbooks/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      toast.success('Playbook deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete playbook')
    },
  })

  const filteredPlaybooks = playbooks.filter((playbook: any) => {
    const matchesSearch = playbook.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (playbook.description && playbook.description.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this playbook?')) {
      deletePlaybookMutation.mutate(id)
    }
  }

  const handleEdit = (playbook: any) => {
    setEditingPlaybook(playbook)
    setShowAddModal(true)
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">Failed to load playbooks</div>
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
            <h1 className="text-2xl font-bold text-gray-900">Playbooks</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage your automation playbooks
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Playbook
          </button>
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
              placeholder="Search playbooks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>
      </div>

      {/* Playbooks Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white shadow rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : filteredPlaybooks.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <FileText className="h-12 w-12" />
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No playbooks yet</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first playbook.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredPlaybooks.map((playbook: any) => (
            <div key={playbook.id} className="bg-white shadow rounded-lg">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        {playbook.name}
                      </h3>
                    </div>
                  </div>
                  
                  <div className="relative">
                    <button className="text-gray-400 hover:text-gray-600">
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                      </svg>
                    </button>
                  </div>
                </div>
                
                {playbook.description && (
                  <p className="mt-2 text-sm text-gray-500">
                    {playbook.description}
                  </p>
                )}
                
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Updated {new Date(playbook.updated_at).toLocaleDateString()}
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEdit(playbook)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(playbook.id)}
                      className="text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => {
              setShowAddModal(false)
              setEditingPlaybook(null)
            }} />
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {editingPlaybook ? 'Edit Playbook' : 'Create Playbook'}
                  </h3>
                  <button
                    onClick={() => {
                      setShowAddModal(false)
                      setEditingPlaybook(null)
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="text-center py-8">
                  <FileText className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Playbook Editor</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Playbook editor coming soon. For now, you can manage playbooks via the API.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
