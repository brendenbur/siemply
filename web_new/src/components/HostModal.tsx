import { useState, useEffect } from 'react'
import { X, Upload, Eye, EyeOff } from 'lucide-react'
import { cn } from '../lib/utils'

interface HostModalProps {
  host?: any
  onClose: () => void
  onSave: (hostData: any) => void
  isLoading: boolean
}

export function HostModal({ host, onClose, onSave, isLoading }: HostModalProps) {
  const [formData, setFormData] = useState({
    hostname: '',
    ip: '',
    port: 22,
    username: 'splunk',
    auth_type: 'key',
    private_key: '',
    private_key_passphrase: '',
    password: '',
    labels: [] as string[],
  })
  const [labelInput, setLabelInput] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showKeyPassphrase, setShowKeyPassphrase] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (host) {
      setFormData({
        hostname: host.hostname || '',
        ip: host.ip || '',
        port: host.port || 22,
        username: host.username || 'splunk',
        auth_type: host.auth_type || 'key',
        private_key: '',
        private_key_passphrase: '',
        password: '',
        labels: host.labels || [],
      })
    }
  }, [host])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.hostname.trim()) {
      newErrors.hostname = 'Hostname is required'
    }

    if (!formData.ip.trim()) {
      newErrors.ip = 'IP address is required'
    } else if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(formData.ip)) {
      newErrors.ip = 'Invalid IP address format'
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required'
    }

    if (formData.port < 1 || formData.port > 65535) {
      newErrors.port = 'Port must be between 1 and 65535'
    }

    if (formData.auth_type === 'key' && !formData.private_key.trim()) {
      newErrors.private_key = 'Private key is required for key authentication'
    }

    if (formData.auth_type === 'password' && !formData.password.trim()) {
      newErrors.password = 'Password is required for password authentication'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    const submitData = {
      ...formData,
      port: parseInt(formData.port.toString()),
    }

    if (host) {
      submitData.id = host.id
    }

    onSave(submitData)
  }

  const handleAddLabel = () => {
    if (labelInput.trim() && !formData.labels.includes(labelInput.trim())) {
      setFormData(prev => ({
        ...prev,
        labels: [...prev.labels, labelInput.trim()]
      }))
      setLabelInput('')
    }
  }

  const handleRemoveLabel = (label: string) => {
    setFormData(prev => ({
      ...prev,
      labels: prev.labels.filter(l => l !== label)
    }))
  }

  const handleKeyFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        setFormData(prev => ({
          ...prev,
          private_key: event.target?.result as string
        }))
      }
      reader.readAsText(file)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {host ? 'Edit Host' : 'Add New Host'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Hostname *
                    </label>
                    <input
                      type="text"
                      value={formData.hostname}
                      onChange={(e) => setFormData(prev => ({ ...prev, hostname: e.target.value }))}
                      className={cn(
                        'mt-1 block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                        errors.hostname ? 'border-red-300' : 'border-gray-300'
                      )}
                      placeholder="web-01.example.com"
                    />
                    {errors.hostname && <p className="mt-1 text-sm text-red-600">{errors.hostname}</p>}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      IP Address *
                    </label>
                    <input
                      type="text"
                      value={formData.ip}
                      onChange={(e) => setFormData(prev => ({ ...prev, ip: e.target.value }))}
                      className={cn(
                        'mt-1 block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                        errors.ip ? 'border-red-300' : 'border-gray-300'
                      )}
                      placeholder="192.168.1.10"
                    />
                    {errors.ip && <p className="mt-1 text-sm text-red-600">{errors.ip}</p>}
                  </div>
                </div>
                
                {/* SSH Configuration */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Username *
                    </label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                      className={cn(
                        'mt-1 block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                        errors.username ? 'border-red-300' : 'border-gray-300'
                      )}
                      placeholder="splunk"
                    />
                    {errors.username && <p className="mt-1 text-sm text-red-600">{errors.username}</p>}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Port *
                    </label>
                    <input
                      type="number"
                      value={formData.port}
                      onChange={(e) => setFormData(prev => ({ ...prev, port: parseInt(e.target.value) }))}
                      className={cn(
                        'mt-1 block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                        errors.port ? 'border-red-300' : 'border-gray-300'
                      )}
                      min="1"
                      max="65535"
                    />
                    {errors.port && <p className="mt-1 text-sm text-red-600">{errors.port}</p>}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Authentication
                    </label>
                    <select
                      value={formData.auth_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, auth_type: e.target.value }))}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="key">Private Key</option>
                      <option value="password">Password</option>
                    </select>
                  </div>
                </div>
                
                {/* Authentication Details */}
                {formData.auth_type === 'key' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Private Key *
                      </label>
                      <div className="mt-1 flex space-x-2">
                        <textarea
                          value={formData.private_key}
                          onChange={(e) => setFormData(prev => ({ ...prev, private_key: e.target.value }))}
                          className={cn(
                            'flex-1 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                            errors.private_key ? 'border-red-300' : 'border-gray-300'
                          )}
                          rows={6}
                          placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"
                        />
                        <div className="flex flex-col space-y-2">
                          <label className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                            <Upload className="h-4 w-4 mr-2" />
                            Upload
                            <input
                              type="file"
                              accept=".pem,.key"
                              onChange={handleKeyFileUpload}
                              className="hidden"
                            />
                          </label>
                        </div>
                      </div>
                      {errors.private_key && <p className="mt-1 text-sm text-red-600">{errors.private_key}</p>}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Key Passphrase (optional)
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type={showKeyPassphrase ? 'text' : 'password'}
                          value={formData.private_key_passphrase}
                          onChange={(e) => setFormData(prev => ({ ...prev, private_key_passphrase: e.target.value }))}
                          className="block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm pr-10"
                          placeholder="Enter passphrase if key is encrypted"
                        />
                        <button
                          type="button"
                          onClick={() => setShowKeyPassphrase(!showKeyPassphrase)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        >
                          {showKeyPassphrase ? (
                            <EyeOff className="h-4 w-4 text-gray-400" />
                          ) : (
                            <Eye className="h-4 w-4 text-gray-400" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Password *
                    </label>
                    <div className="mt-1 relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                        className={cn(
                          'block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm pr-10',
                          errors.password ? 'border-red-300' : 'border-gray-300'
                        )}
                        placeholder="Enter password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-400" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                    {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
                  </div>
                )}
                
                {/* Labels */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Labels
                  </label>
                  <div className="mt-1 flex space-x-2">
                    <input
                      type="text"
                      value={labelInput}
                      onChange={(e) => setLabelInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddLabel())}
                      className="flex-1 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Enter label and press Enter"
                    />
                    <button
                      type="button"
                      onClick={handleAddLabel}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Add
                    </button>
                  </div>
                  {formData.labels.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {formData.labels.map((label, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {label}
                          <button
                            type="button"
                            onClick={() => handleRemoveLabel(label)}
                            className="ml-1.5 h-4 w-4 rounded-full inline-flex items-center justify-center text-blue-400 hover:bg-blue-200 hover:text-blue-500"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : (host ? 'Update Host' : 'Add Host')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
