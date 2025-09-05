import React, { useState } from 'react';
import { Save, RefreshCw, TestTube, Database, Key, Wifi } from 'lucide-react';
import toast from 'react-hot-toast';

export function Settings() {
  const [settings, setSettings] = useState({
    // API Settings
    api_url: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    api_timeout: 30000,
    
    // WebSocket Settings
    websocket_url: 'ws://localhost:8000/api/ws/',
    websocket_reconnect_interval: 5000,
    
    // Refresh Intervals
    hosts_refresh_interval: 60000,
    runs_refresh_interval: 10000,
    health_refresh_interval: 30000,
    audit_refresh_interval: 30000,
    
    // UI Settings
    theme: 'light',
    page_size: 50,
    auto_refresh: true,
    
    // Notification Settings
    notifications_enabled: true,
    notification_sound: true,
    notification_duration: 4000,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const handleChange = (name, value) => {
    setSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save settings to localStorage
      localStorage.setItem('siemply_settings', JSON.stringify(settings));
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      const response = await fetch(`${settings.api_url}/api/status`);
      if (response.ok) {
        toast.success('Connection test successful');
      } else {
        toast.error('Connection test failed');
      }
    } catch (error) {
      toast.error('Connection test failed: ' + error.message);
    } finally {
      setIsTesting(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      setSettings({
        api_url: 'http://localhost:8000',
        api_timeout: 30000,
        websocket_url: 'ws://localhost:8000/api/ws/',
        websocket_reconnect_interval: 5000,
        hosts_refresh_interval: 60000,
        runs_refresh_interval: 10000,
        health_refresh_interval: 30000,
        audit_refresh_interval: 30000,
        theme: 'light',
        page_size: 50,
        auto_refresh: true,
        notifications_enabled: true,
        notification_sound: true,
        notification_duration: 4000,
      });
      toast.success('Settings reset to default');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Configure Siemply application settings
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleTestConnection}
            disabled={isTesting}
            className="btn btn-outline"
          >
            <TestTube className="h-4 w-4 mr-2" />
            Test Connection
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn btn-primary"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Settings
          </button>
        </div>
      </div>

      {/* API Settings */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">API Settings</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="form-label">API URL</label>
              <input
                type="url"
                value={settings.api_url}
                onChange={(e) => handleChange('api_url', e.target.value)}
                className="form-input"
                placeholder="http://localhost:8000"
              />
              <p className="form-help">Base URL for the Siemply API</p>
            </div>
            
            <div>
              <label className="form-label">API Timeout (ms)</label>
              <input
                type="number"
                value={settings.api_timeout}
                onChange={(e) => handleChange('api_timeout', parseInt(e.target.value))}
                className="form-input"
                min="1000"
                max="300000"
              />
              <p className="form-help">Request timeout in milliseconds</p>
            </div>
          </div>
        </div>
      </div>

      {/* WebSocket Settings */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">WebSocket Settings</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="form-label">WebSocket URL</label>
              <input
                type="url"
                value={settings.websocket_url}
                onChange={(e) => handleChange('websocket_url', e.target.value)}
                className="form-input"
                placeholder="ws://localhost:8000/api/ws/"
              />
              <p className="form-help">WebSocket URL for real-time updates</p>
            </div>
            
            <div>
              <label className="form-label">Reconnect Interval (ms)</label>
              <input
                type="number"
                value={settings.websocket_reconnect_interval}
                onChange={(e) => handleChange('websocket_reconnect_interval', parseInt(e.target.value))}
                className="form-input"
                min="1000"
                max="60000"
              />
              <p className="form-help">Delay between reconnection attempts</p>
            </div>
          </div>
        </div>
      </div>

      {/* Refresh Intervals */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Refresh Intervals</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="form-label">Hosts Refresh (ms)</label>
              <input
                type="number"
                value={settings.hosts_refresh_interval}
                onChange={(e) => handleChange('hosts_refresh_interval', parseInt(e.target.value))}
                className="form-input"
                min="10000"
                max="300000"
              />
              <p className="form-help">How often to refresh hosts data</p>
            </div>
            
            <div>
              <label className="form-label">Runs Refresh (ms)</label>
              <input
                type="number"
                value={settings.runs_refresh_interval}
                onChange={(e) => handleChange('runs_refresh_interval', parseInt(e.target.value))}
                className="form-input"
                min="5000"
                max="60000"
              />
              <p className="form-help">How often to refresh runs data</p>
            </div>
            
            <div>
              <label className="form-label">Health Refresh (ms)</label>
              <input
                type="number"
                value={settings.health_refresh_interval}
                onChange={(e) => handleChange('health_refresh_interval', parseInt(e.target.value))}
                className="form-input"
                min="10000"
                max="300000"
              />
              <p className="form-help">How often to refresh health data</p>
            </div>
            
            <div>
              <label className="form-label">Audit Refresh (ms)</label>
              <input
                type="number"
                value={settings.audit_refresh_interval}
                onChange={(e) => handleChange('audit_refresh_interval', parseInt(e.target.value))}
                className="form-input"
                min="10000"
                max="300000"
              />
              <p className="form-help">How often to refresh audit data</p>
            </div>
          </div>
        </div>
      </div>

      {/* UI Settings */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">UI Settings</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="form-label">Theme</label>
              <select
                value={settings.theme}
                onChange={(e) => handleChange('theme', e.target.value)}
                className="form-input"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
              </select>
            </div>
            
            <div>
              <label className="form-label">Page Size</label>
              <input
                type="number"
                value={settings.page_size}
                onChange={(e) => handleChange('page_size', parseInt(e.target.value))}
                className="form-input"
                min="10"
                max="1000"
              />
              <p className="form-help">Number of items per page</p>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.auto_refresh}
                onChange={(e) => handleChange('auto_refresh', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Enable Auto Refresh
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Notification Settings</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.notifications_enabled}
                onChange={(e) => handleChange('notifications_enabled', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Enable Notifications
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.notification_sound}
                onChange={(e) => handleChange('notification_sound', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Enable Notification Sound
              </label>
            </div>
            
            <div>
              <label className="form-label">Notification Duration (ms)</label>
              <input
                type="number"
                value={settings.notification_duration}
                onChange={(e) => handleChange('notification_duration', parseInt(e.target.value))}
                className="form-input"
                min="1000"
                max="10000"
              />
              <p className="form-help">How long notifications stay visible</p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Actions</h3>
        </div>
        <div className="card-body">
          <div className="flex space-x-3">
            <button
              onClick={handleReset}
              className="btn btn-outline"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset to Default
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
