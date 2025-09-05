import { useQuery } from '@tanstack/react-query'
import { Server, Play, FileText, Activity } from 'lucide-react'
import { api } from '../lib/api'

export function DashboardPage() {
  const { data: hosts = [] } = useQuery({
    queryKey: ['hosts'],
    queryFn: () => api.get('/hosts').then(res => res.data),
  })

  const { data: playbooks = [] } = useQuery({
    queryKey: ['playbooks'],
    queryFn: () => api.get('/playbooks').then(res => res.data),
  })

  const { data: runs = [] } = useQuery({
    queryKey: ['runs'],
    queryFn: () => api.get('/runs?limit=10').then(res => res.data),
  })

  const stats = {
    totalHosts: hosts.length,
    reachableHosts: hosts.filter((h: any) => h.status === 'reachable').length,
    totalPlaybooks: playbooks.length,
    recentRuns: runs.length,
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your Splunk infrastructure management
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                  <Server className="h-5 w-5 text-blue-600" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Hosts</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalHosts}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Reachable Hosts</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.reachableHosts}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                  <FileText className="h-5 w-5 text-purple-600" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Playbooks</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalPlaybooks}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-100 rounded-md flex items-center justify-center">
                  <Play className="h-5 w-5 text-orange-600" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Recent Runs</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.recentRuns}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Hosts */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Hosts
            </h3>
            {hosts.length === 0 ? (
              <p className="text-sm text-gray-500">No hosts added yet</p>
            ) : (
              <div className="space-y-3">
                {hosts.slice(0, 5).map((host: any) => (
                  <div key={host.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8">
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {host.hostname.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {host.hostname}
                        </p>
                        <p className="text-sm text-gray-500">
                          {host.ip}:{host.port}
                        </p>
                      </div>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      host.status === 'reachable' 
                        ? 'bg-green-100 text-green-800'
                        : host.status === 'unreachable'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {host.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Runs */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Runs
            </h3>
            {runs.length === 0 ? (
              <p className="text-sm text-gray-500">No runs yet</p>
            ) : (
              <div className="space-y-3">
                {runs.slice(0, 5).map((run: any) => (
                  <div key={run.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Run {run.id.slice(0, 8)}...
                      </p>
                      <p className="text-sm text-gray-500">
                        {run.host_ids.length} host{run.host_ids.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      run.status === 'completed' 
                        ? 'bg-green-100 text-green-800'
                        : run.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : run.status === 'running'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {run.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
