import { useState, useEffect } from 'react'
import { X, Play, FileText } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { api } from '../lib/api'

interface RunPlaybookModalProps {
  hostIds: string[]
  onClose: () => void
}

export function RunPlaybookModal({ hostIds, onClose }: RunPlaybookModalProps) {
  const [selectedPlaybook, setSelectedPlaybook] = useState<string>('')
  const [showPreview, setShowPreview] = useState(false)
  
  const queryClient = useQueryClient()

  const { data: playbooks = [] } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => api.get('/playbooks').then(res => res.data),
  })

  const { data: selectedPlaybookData } = useQuery({
    queryKey: ['playbook', selectedPlaybook],
    queryFn: () => api.get(`/playbooks/${selectedPlaybook}`).then(res => res.data),
    enabled: !!selectedPlaybook,
  })

  const runPlaybookMutation = useMutation({
    mutationFn: (data: any) => api.post('/runs', data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      toast.success('Playbook run started successfully')
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start playbook run')
    },
  })

  const handleRun = () => {
    if (!selectedPlaybook) {
      toast.error('Please select a playbook')
      return
    }

    runPlaybookMutation.mutate({
      playbook_id: selectedPlaybook,
      host_ids: hostIds,
    })
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Run Playbook</h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Host Selection Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  Selected Hosts ({hostIds.length})
                </h4>
                <p className="text-sm text-blue-700">
                  This playbook will be executed on {hostIds.length} host{hostIds.length !== 1 ? 's' : ''}.
                </p>
              </div>
              
              {/* Playbook Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Playbook
                </label>
                <select
                  value={selectedPlaybook}
                  onChange={(e) => setSelectedPlaybook(e.target.value)}
                  className="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">Choose a playbook...</option>
                  {playbooks.map((playbook: any) => (
                    <option key={playbook.id} value={playbook.id}>
                      {playbook.name}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Playbook Preview */}
              {selectedPlaybookData && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-700">
                      Playbook Preview
                    </h4>
                    <button
                      onClick={() => setShowPreview(!showPreview)}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <FileText className="h-4 w-4 mr-1" />
                      {showPreview ? 'Hide' : 'Show'} Preview
                    </button>
                  </div>
                  
                  {showPreview && (
                    <div className="border border-gray-200 rounded-lg">
                      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                        <h5 className="text-sm font-medium text-gray-900">
                          {selectedPlaybookData.name}
                        </h5>
                        {selectedPlaybookData.description && (
                          <p className="text-sm text-gray-500 mt-1">
                            {selectedPlaybookData.description}
                          </p>
                        )}
                      </div>
                      <div className="p-4">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                          {selectedPlaybookData.yaml_content}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              onClick={handleRun}
              disabled={!selectedPlaybook || runPlaybookMutation.isPending}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              <Play className="h-4 w-4 mr-2" />
              {runPlaybookMutation.isPending ? 'Starting...' : 'Run Playbook'}
            </button>
            <button
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
