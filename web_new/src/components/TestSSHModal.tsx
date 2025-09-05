import { useState } from 'react'
import { X, TestTube, CheckCircle, XCircle } from 'lucide-react'
import { cn } from '../lib/utils'

interface TestSSHModalProps {
  hosts: any[]
  onClose: () => void
  onTest: (hostIds: string[]) => void
  isLoading: boolean
}

export function TestSSHModal({ hosts, onClose, onTest, isLoading }: TestSSHModalProps) {
  const [selectedHosts, setSelectedHosts] = useState<string[]>([])
  const [testResults, setTestResults] = useState<Record<string, any>>({})

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedHosts(hosts.map(host => host.id))
    } else {
      setSelectedHosts([])
    }
  }

  const handleSelectHost = (hostId: string, checked: boolean) => {
    if (checked) {
      setSelectedHosts([...selectedHosts, hostId])
    } else {
      setSelectedHosts(selectedHosts.filter(id => id !== hostId))
    }
  }

  const handleTest = async () => {
    if (selectedHosts.length === 0) {
      return
    }

    try {
      const response = await fetch('/api/hosts/test-ssh-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host_ids: selectedHosts })
      })
      
      const results = await response.json()
      
      const resultsMap: Record<string, any> = {}
      results.forEach((result: any) => {
        resultsMap[result.host_id] = result
      })
      
      setTestResults(resultsMap)
      onTest(selectedHosts)
    } catch (error) {
      console.error('Test failed:', error)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Test SSH Connectivity</h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <p className="text-sm text-gray-500">
                Select hosts to test SSH connectivity. This will attempt to connect to each host and verify authentication.
              </p>
              
              {/* Host Selection */}
              <div className="border border-gray-200 rounded-lg">
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedHosts.length === hosts.length && hosts.length > 0}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">
                      Select All ({hosts.length} hosts)
                    </span>
                  </div>
                </div>
                
                <div className="max-h-64 overflow-y-auto">
                  {hosts.map((host) => (
                    <div key={host.id} className="px-4 py-3 border-b border-gray-200 last:border-b-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={selectedHosts.includes(host.id)}
                            onChange={(e) => handleSelectHost(host.id, e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              {host.hostname}
                            </div>
                            <div className="text-sm text-gray-500">
                              {host.ip}:{host.port} ({host.username})
                            </div>
                          </div>
                        </div>
                        
                        {testResults[host.id] && (
                          <div className="flex items-center">
                            {testResults[host.id].success ? (
                              <CheckCircle className="h-5 w-5 text-green-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                            <span className={cn(
                              'ml-2 text-sm',
                              testResults[host.id].success ? 'text-green-600' : 'text-red-600'
                            )}>
                              {testResults[host.id].success ? 'Success' : 'Failed'}
                            </span>
                          </div>
                        )}
                      </div>
                      
                      {testResults[host.id] && !testResults[host.id].success && (
                        <div className="mt-2 text-sm text-red-600">
                          {testResults[host.id].message}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              onClick={handleTest}
              disabled={isLoading || selectedHosts.length === 0}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              <TestTube className="h-4 w-4 mr-2" />
              {isLoading ? 'Testing...' : `Test ${selectedHosts.length} Host${selectedHosts.length !== 1 ? 's' : ''}`}
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
