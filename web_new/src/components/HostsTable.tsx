import { useState } from 'react'
import { 
  MoreVertical, 
  Edit, 
  Trash2, 
  TestTube, 
  Play,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import { cn } from '../lib/utils'

interface Host {
  id: string
  hostname: string
  ip: string
  port: number
  username: string
  auth_type: string
  labels: string[]
  last_seen: string | null
  status: string
  created_at: string
  updated_at: string
}

interface HostsTableProps {
  hosts: Host[]
  isLoading: boolean
  selectedHosts: string[]
  onSelectionChange: (hostIds: string[]) => void
  onEdit: (host: Host) => void
  onDelete: (id: string) => void
  onTestSSH: (hostIds: string[]) => void
  onRunPlaybook: (hostIds: string[]) => void
}

export function HostsTable({
  hosts,
  isLoading,
  selectedHosts,
  onSelectionChange,
  onEdit,
  onDelete,
  onTestSSH,
  onRunPlaybook,
}: HostsTableProps) {
  const [showActions, setShowActions] = useState<string | null>(null)

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(hosts.map(host => host.id))
    } else {
      onSelectionChange([])
    }
  }

  const handleSelectHost = (hostId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedHosts, hostId])
    } else {
      onSelectionChange(selectedHosts.filter(id => id !== hostId))
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'reachable':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'unreachable':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'reachable':
        return 'bg-green-100 text-green-800'
      case 'unreachable':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  if (hosts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto h-12 w-12 text-gray-400">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No hosts yet</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by adding your first host.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden">
      {/* Bulk Actions */}
      {selectedHosts.length > 0 && (
        <div className="bg-blue-50 px-4 py-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">
              {selectedHosts.length} host{selectedHosts.length !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => onTestSSH(selectedHosts)}
                className="inline-flex items-center px-3 py-1 border border-blue-300 text-sm font-medium rounded text-blue-700 bg-white hover:bg-blue-50"
              >
                <TestTube className="h-4 w-4 mr-1" />
                Test SSH
              </button>
              <button
                onClick={() => onRunPlaybook(selectedHosts)}
                className="inline-flex items-center px-3 py-1 border border-blue-300 text-sm font-medium rounded text-blue-700 bg-white hover:bg-blue-50"
              >
                <Play className="h-4 w-4 mr-1" />
                Run Playbook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedHosts.length === hosts.length && hosts.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Host
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                IP Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Port
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Labels
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Seen
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {hosts.map((host) => (
              <tr key={host.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={selectedHosts.includes(host.id)}
                    onChange={(e) => handleSelectHost(host.id, e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-8 w-8">
                      <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {host.hostname.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {host.hostname}
                      </div>
                      <div className="text-sm text-gray-500">
                        {host.auth_type === 'key' ? 'SSH Key' : 'Password'}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {host.ip}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {host.port}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {host.username}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-wrap gap-1">
                    {host.labels.map((label, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {host.last_seen ? new Date(host.last_seen).toLocaleString() : 'Never'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(host.status)}
                    <span className={cn(
                      'ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getStatusColor(host.status)
                    )}>
                      {host.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="relative">
                    <button
                      onClick={() => setShowActions(showActions === host.id ? null : host.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                    
                    {showActions === host.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                        <div className="py-1">
                          <button
                            onClick={() => {
                              onEdit(host)
                              setShowActions(null)
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <Edit className="h-4 w-4 mr-3" />
                            Edit
                          </button>
                          <button
                            onClick={() => {
                              onTestSSH([host.id])
                              setShowActions(null)
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <TestTube className="h-4 w-4 mr-3" />
                            Test SSH
                          </button>
                          <button
                            onClick={() => {
                              onRunPlaybook([host.id])
                              setShowActions(null)
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <Play className="h-4 w-4 mr-3" />
                            Run Playbook
                          </button>
                          <button
                            onClick={() => {
                              onDelete(host.id)
                              setShowActions(null)
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4 mr-3" />
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
