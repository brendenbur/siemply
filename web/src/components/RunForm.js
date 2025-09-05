import React, { useState } from 'react';
import { X } from 'lucide-react';

export function RunForm({ onClose, onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    playbook: '',
    target_hosts: [],
    target_groups: [],
    dry_run: true,
    limit: '',
    forks: 10,
    timeout: 3600,
    batch_size: 10,
    batch_delay: 300,
    tags: [],
    skip_tags: [],
    extra_vars: {},
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setFormData(prev => ({
        ...prev,
        [name]: checked
      }));
    } else if (type === 'number') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 0
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleArrayChange = (name, value) => {
    const array = value.split(',').map(item => item.trim()).filter(item => item);
    setFormData(prev => ({
      ...prev,
      [name]: array
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.playbook.trim()) {
      newErrors.playbook = 'Playbook is required';
    }
    
    if (formData.target_hosts.length === 0 && formData.target_groups.length === 0) {
      newErrors.target_hosts = 'At least one target host or group is required';
    }
    
    if (formData.forks < 1 || formData.forks > 100) {
      newErrors.forks = 'Forks must be between 1 and 100';
    }
    
    if (formData.timeout < 60 || formData.timeout > 86400) {
      newErrors.timeout = 'Timeout must be between 60 and 86400 seconds';
    }
    
    if (formData.batch_size < 1 || formData.batch_size > 100) {
      newErrors.batch_size = 'Batch size must be between 1 and 100';
    }
    
    if (formData.batch_delay < 0 || formData.batch_delay > 3600) {
      newErrors.batch_delay = 'Batch delay must be between 0 and 3600 seconds';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    // Convert array fields
    const submitData = {
      ...formData,
      target_hosts: formData.target_hosts.length > 0 ? formData.target_hosts : [],
      target_groups: formData.target_groups.length > 0 ? formData.target_groups : [],
      tags: formData.tags.length > 0 ? formData.tags : null,
      skip_tags: formData.skip_tags.length > 0 ? formData.skip_tags : null,
      limit: formData.limit ? parseInt(formData.limit) : null,
    };
    
    onSubmit(submitData);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Start Run</h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Playbook */}
                <div>
                  <label className="form-label">Playbook *</label>
                  <input
                    type="text"
                    name="playbook"
                    value={formData.playbook}
                    onChange={handleChange}
                    className={`form-input ${errors.playbook ? 'border-red-300' : ''}`}
                    placeholder="plays/upgrade-uf.yml"
                  />
                  {errors.playbook && <p className="form-error">{errors.playbook}</p>}
                </div>
                
                {/* Targets */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Target Hosts</label>
                    <input
                      type="text"
                      value={formData.target_hosts.join(', ')}
                      onChange={(e) => handleArrayChange('target_hosts', e.target.value)}
                      className={`form-input ${errors.target_hosts ? 'border-red-300' : ''}`}
                      placeholder="web-01, web-02"
                    />
                    <p className="form-help">Comma-separated host names</p>
                    {errors.target_hosts && <p className="form-error">{errors.target_hosts}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">Target Groups</label>
                    <input
                      type="text"
                      value={formData.target_groups.join(', ')}
                      onChange={(e) => handleArrayChange('target_groups', e.target.value)}
                      className="form-input"
                      placeholder="prod-web, prod-idx"
                    />
                    <p className="form-help">Comma-separated group names</p>
                  </div>
                </div>
                
                {/* Options */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Forks</label>
                    <input
                      type="number"
                      name="forks"
                      value={formData.forks}
                      onChange={handleChange}
                      className={`form-input ${errors.forks ? 'border-red-300' : ''}`}
                      min="1"
                      max="100"
                    />
                    {errors.forks && <p className="form-error">{errors.forks}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">Timeout (seconds)</label>
                    <input
                      type="number"
                      name="timeout"
                      value={formData.timeout}
                      onChange={handleChange}
                      className={`form-input ${errors.timeout ? 'border-red-300' : ''}`}
                      min="60"
                      max="86400"
                    />
                    {errors.timeout && <p className="form-error">{errors.timeout}</p>}
                  </div>
                </div>
                
                {/* Batch Settings */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Batch Size</label>
                    <input
                      type="number"
                      name="batch_size"
                      value={formData.batch_size}
                      onChange={handleChange}
                      className={`form-input ${errors.batch_size ? 'border-red-300' : ''}`}
                      min="1"
                      max="100"
                    />
                    {errors.batch_size && <p className="form-error">{errors.batch_size}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">Batch Delay (seconds)</label>
                    <input
                      type="number"
                      name="batch_delay"
                      value={formData.batch_delay}
                      onChange={handleChange}
                      className={`form-input ${errors.batch_delay ? 'border-red-300' : ''}`}
                      min="0"
                      max="3600"
                    />
                    {errors.batch_delay && <p className="form-error">{errors.batch_delay}</p>}
                  </div>
                </div>
                
                {/* Tags */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Tags</label>
                    <input
                      type="text"
                      value={formData.tags.join(', ')}
                      onChange={(e) => handleArrayChange('tags', e.target.value)}
                      className="form-input"
                      placeholder="precheck, upgrade"
                    />
                    <p className="form-help">Comma-separated tags</p>
                  </div>
                  
                  <div>
                    <label className="form-label">Skip Tags</label>
                    <input
                      type="text"
                      value={formData.skip_tags.join(', ')}
                      onChange={(e) => handleArrayChange('skip_tags', e.target.value)}
                      className="form-input"
                      placeholder="test, debug"
                    />
                    <p className="form-help">Comma-separated tags to skip</p>
                  </div>
                </div>
                
                {/* Dry Run */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="dry_run"
                    checked={formData.dry_run}
                    onChange={handleChange}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Dry Run (simulate only)
                  </label>
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
                Start Run
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
