import React, { useState } from 'react';
import { X } from 'lucide-react';

export function HostForm({ onClose, onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    name: '',
    ip: '',
    user: 'splunk',
    port: 22,
    key_file: '',
    group: '',
    splunk_type: 'uf',
    splunk_version: '',
    os_family: 'RedHat',
    os_version: '',
    cpu_arch: 'x86_64',
    memory_gb: '',
    disk_gb: '',
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Host name is required';
    }
    
    if (!formData.ip.trim()) {
      newErrors.ip = 'IP address is required';
    } else if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(formData.ip)) {
      newErrors.ip = 'Invalid IP address format';
    }
    
    if (!formData.user.trim()) {
      newErrors.user = 'User is required';
    }
    
    if (formData.port < 1 || formData.port > 65535) {
      newErrors.port = 'Port must be between 1 and 65535';
    }
    
    if (formData.memory_gb && (isNaN(formData.memory_gb) || formData.memory_gb < 0)) {
      newErrors.memory_gb = 'Memory must be a positive number';
    }
    
    if (formData.disk_gb && (isNaN(formData.disk_gb) || formData.disk_gb < 0)) {
      newErrors.disk_gb = 'Disk space must be a positive number';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    // Convert numeric fields
    const submitData = {
      ...formData,
      port: parseInt(formData.port),
      memory_gb: formData.memory_gb ? parseInt(formData.memory_gb) : null,
      disk_gb: formData.disk_gb ? parseInt(formData.disk_gb) : null,
    };
    
    onSubmit(submitData);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Add Host</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Basic Information */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Host Name *</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className={`form-input ${errors.name ? 'border-red-300' : ''}`}
                      placeholder="web-01.example.com"
                    />
                    {errors.name && <p className="form-error">{errors.name}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">IP Address *</label>
                    <input
                      type="text"
                      name="ip"
                      value={formData.ip}
                      onChange={handleChange}
                      className={`form-input ${errors.ip ? 'border-red-300' : ''}`}
                      placeholder="192.168.1.10"
                    />
                    {errors.ip && <p className="form-error">{errors.ip}</p>}
                  </div>
                </div>
                
                {/* SSH Configuration */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="form-label">SSH User *</label>
                    <input
                      type="text"
                      name="user"
                      value={formData.user}
                      onChange={handleChange}
                      className={`form-input ${errors.user ? 'border-red-300' : ''}`}
                      placeholder="splunk"
                    />
                    {errors.user && <p className="form-error">{errors.user}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">SSH Port *</label>
                    <input
                      type="number"
                      name="port"
                      value={formData.port}
                      onChange={handleChange}
                      className={`form-input ${errors.port ? 'border-red-300' : ''}`}
                      min="1"
                      max="65535"
                    />
                    {errors.port && <p className="form-error">{errors.port}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">SSH Key File</label>
                    <input
                      type="text"
                      name="key_file"
                      value={formData.key_file}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="~/.ssh/id_rsa"
                    />
                  </div>
                </div>
                
                {/* Splunk Configuration */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Splunk Type</label>
                    <select
                      name="splunk_type"
                      value={formData.splunk_type}
                      onChange={handleChange}
                      className="form-input"
                    >
                      <option value="uf">Universal Forwarder</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="form-label">Splunk Version</label>
                    <input
                      type="text"
                      name="splunk_version"
                      value={formData.splunk_version}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="9.2.2"
                    />
                  </div>
                </div>
                
                {/* OS Configuration */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="form-label">OS Family</label>
                    <select
                      name="os_family"
                      value={formData.os_family}
                      onChange={handleChange}
                      className="form-input"
                    >
                      <option value="RedHat">RedHat</option>
                      <option value="Debian">Debian</option>
                      <option value="Ubuntu">Ubuntu</option>
                      <option value="CentOS">CentOS</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="form-label">OS Version</label>
                    <input
                      type="text"
                      name="os_version"
                      value={formData.os_version}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="8"
                    />
                  </div>
                  
                  <div>
                    <label className="form-label">CPU Architecture</label>
                    <select
                      name="cpu_arch"
                      value={formData.cpu_arch}
                      onChange={handleChange}
                      className="form-input"
                    >
                      <option value="x86_64">x86_64</option>
                      <option value="arm64">arm64</option>
                    </select>
                  </div>
                </div>
                
                {/* Resources */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Memory (GB)</label>
                    <input
                      type="number"
                      name="memory_gb"
                      value={formData.memory_gb}
                      onChange={handleChange}
                      className={`form-input ${errors.memory_gb ? 'border-red-300' : ''}`}
                      placeholder="8"
                      min="0"
                    />
                    {errors.memory_gb && <p className="form-error">{errors.memory_gb}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">Disk Space (GB)</label>
                    <input
                      type="number"
                      name="disk_gb"
                      value={formData.disk_gb}
                      onChange={handleChange}
                      className={`form-input ${errors.disk_gb ? 'border-red-300' : ''}`}
                      placeholder="100"
                      min="0"
                    />
                    {errors.disk_gb && <p className="form-error">{errors.disk_gb}</p>}
                  </div>
                </div>
                
                {/* Group */}
                <div>
                  <label className="form-label">Group</label>
                  <input
                    type="text"
                    name="group"
                    value={formData.group}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="prod-web"
                  />
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary sm:ml-3 sm:w-auto w-full"
              >
                {isLoading ? (
                  <div className="loading-spinner mr-2"></div>
                ) : null}
                Add Host
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn btn-outline sm:mt-0 mt-3 sm:w-auto w-full"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
