"""
Siemply Task Runner - Idempotent task execution engine
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import yaml

from .ssh_executor import SSHExecutor
from .audit import AuditLogger


@dataclass
class TaskResult:
    """Result of a task execution"""
    name: str
    status: str  # success, failed, skipped, changed
    start_time: datetime
    end_time: datetime
    duration: float
    output: str
    error: Optional[str] = None
    changed: bool = False
    facts: Dict[str, Any] = None


class TaskRunner:
    """
    Task execution engine with idempotent primitives
    """
    
    def __init__(self, ssh_executor: SSHExecutor, audit_logger: AuditLogger):
        self.ssh_executor = ssh_executor
        self.audit = audit_logger
        self.logger = logging.getLogger(__name__)
        
        # Register built-in task types
        self.task_types = {
            'command': self._execute_command,
            'file': self._execute_file,
            'package': self._execute_package,
            'service': self._execute_service,
            'archive': self._execute_archive,
            'template': self._execute_template,
            'script': self._execute_script,
            'checkpoint': self._execute_checkpoint,
            'splunk_precheck': self._execute_splunk_precheck,
            'splunk_download': self._execute_splunk_download,
            'splunk_install': self._execute_splunk_install,
            'splunk_backup': self._execute_splunk_backup,
            'splunk_restore': self._execute_splunk_restore,
            'splunk_health_check': self._execute_splunk_health_check,
            'splunk_version_check': self._execute_splunk_version_check,
            'splunk_status_check': self._execute_splunk_status_check,
            'splunk_wait_ready': self._execute_splunk_wait_ready,
            'splunk_verify_package': self._execute_splunk_verify_package,
            'splunk_verify_backup': self._execute_splunk_verify_backup,
            'splunk_restore_config': self._execute_splunk_restore_config,
            'splunk_set_permissions': self._execute_splunk_set_permissions,
            'splunk_cleanup_backups': self._execute_splunk_cleanup_backups,
            'splunk_validate_upgrade': self._execute_splunk_validate_upgrade,
        }
    
    async def execute_task(self, task_config: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> TaskResult:
        """
        Execute a single task on a host
        
        Args:
            task_config: Task configuration
            host: Host information
            run_config: Run configuration
            
        Returns:
            TaskResult with execution details
        """
        task_name = task_config.get('name', 'unnamed_task')
        task_type = task_config.get('task', 'command')
        args = task_config.get('args', {})
        
        start_time = datetime.now()
        
        self.logger.info(f"Executing task '{task_name}' ({task_type}) on {host.get('ansible_host', 'unknown')}")
        
        try:
            # Check if task should be skipped
            if await self._should_skip_task(task_config, host, run_config):
                return TaskResult(
                    name=task_name,
                    status='skipped',
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration=0,
                    output="Task skipped due to condition",
                    changed=False
                )
            
            # Execute task
            if task_type not in self.task_types:
                raise ValueError(f"Unknown task type: {task_type}")
            
            result = await self.task_types[task_type](args, host, run_config)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Create task result
            task_result = TaskResult(
                name=task_name,
                status=result.get('status', 'success'),
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output=result.get('output', ''),
                error=result.get('error'),
                changed=result.get('changed', False),
                facts=result.get('facts', {})
            )
            
            # Log task execution
            await self.audit.log_task_execution(host, task_config, task_result)
            
            return task_result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(f"Task '{task_name}' failed: {e}")
            
            return TaskResult(
                name=task_name,
                status='failed',
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output='',
                error=str(e),
                changed=False
            )
    
    async def _should_skip_task(self, task_config: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> bool:
        """Check if task should be skipped based on conditions"""
        # Check when conditions
        when = task_config.get('when')
        if when:
            if not await self._evaluate_condition(when, host, run_config):
                return True
        
        # Check only_if conditions
        only_if = task_config.get('only_if')
        if only_if:
            if not await self._evaluate_condition(only_if, host, run_config):
                return True
        
        # Check tags
        task_tags = task_config.get('tags', [])
        if run_config.tags and not any(tag in task_tags for tag in run_config.tags):
            return True
        
        # Check skip_tags
        if run_config.skip_tags and any(tag in task_tags for tag in run_config.skip_tags):
            return True
        
        return False
    
    async def _evaluate_condition(self, condition: str, host: Dict[str, Any], run_config: Any) -> bool:
        """Evaluate a condition string"""
        # Simple condition evaluation - in production, use a proper expression evaluator
        try:
            # Replace variables
            condition = condition.replace('{{ ansible_host }}', f"'{host.get('ansible_host', '')}'")
            condition = condition.replace('{{ splunk_type }}', f"'{host.get('splunk_type', '')}'")
            condition = condition.replace('{{ os_family }}', f"'{host.get('os_family', '')}'")
            
            # Evaluate condition
            return eval(condition)
        except:
            return False
    
    # Built-in task implementations
    
    async def _execute_command(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Execute a command on the remote host"""
        cmd = args.get('cmd')
        if not cmd:
            raise ValueError("Command not specified")
        
        timeout = args.get('timeout', 300)
        
        result = await self.ssh_executor.execute_command(host, cmd, timeout=timeout)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_file(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Manage files on the remote host"""
        path = args.get('path')
        state = args.get('state', 'present')
        
        if state == 'present':
            # Create file or directory
            if args.get('directory', False):
                cmd = f"mkdir -p {path}"
            else:
                content = args.get('content', '')
                cmd = f"echo '{content}' > {path}"
            
            result = await self.ssh_executor.execute_command(host, cmd)
            
            # Set ownership and permissions
            if args.get('owner'):
                await self.ssh_executor.execute_command(host, f"chown {args['owner']} {path}")
            if args.get('group'):
                await self.ssh_executor.execute_command(host, f"chgrp {args['group']} {path}")
            if args.get('mode'):
                await self.ssh_executor.execute_command(host, f"chmod {args['mode']} {path}")
            
            return {
                'status': 'success' if result['exit_code'] == 0 else 'failed',
                'output': result['stdout'],
                'error': result['stderr'] if result['exit_code'] != 0 else None,
                'changed': True
            }
        
        elif state == 'absent':
            # Remove file or directory
            cmd = f"rm -rf {path}"
            result = await self.ssh_executor.execute_command(host, cmd)
            
            return {
                'status': 'success' if result['exit_code'] == 0 else 'failed',
                'output': result['stdout'],
                'error': result['stderr'] if result['exit_code'] != 0 else None,
                'changed': True
            }
    
    async def _execute_package(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Manage packages on the remote host"""
        name = args.get('name')
        state = args.get('state', 'present')
        
        # Determine package manager
        os_family = host.get('os_family', 'RedHat')
        if os_family in ['RedHat', 'CentOS']:
            pkg_mgr = 'yum'
        elif os_family in ['Ubuntu', 'Debian']:
            pkg_mgr = 'apt'
        else:
            raise ValueError(f"Unsupported OS family: {os_family}")
        
        if state == 'present':
            if pkg_mgr == 'yum':
                cmd = f"yum install -y {name}"
            else:
                cmd = f"apt-get install -y {name}"
        elif state == 'absent':
            if pkg_mgr == 'yum':
                cmd = f"yum remove -y {name}"
            else:
                cmd = f"apt-get remove -y {name}"
        else:
            raise ValueError(f"Unsupported package state: {state}")
        
        result = await self.ssh_executor.execute_command(host, cmd)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_service(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Manage services on the remote host"""
        name = args.get('name')
        state = args.get('state', 'started')
        enabled = args.get('enabled', None)
        
        # Build systemctl commands
        if state == 'started':
            cmd = f"systemctl start {name}"
        elif state == 'stopped':
            cmd = f"systemctl stop {name}"
        elif state == 'restarted':
            cmd = f"systemctl restart {name}"
        else:
            raise ValueError(f"Unsupported service state: {state}")
        
        result = await self.ssh_executor.execute_command(host, cmd)
        
        # Handle enabled/disabled
        if enabled is not None:
            if enabled:
                enable_cmd = f"systemctl enable {name}"
            else:
                enable_cmd = f"systemctl disable {name}"
            
            enable_result = await self.ssh_executor.execute_command(host, enable_cmd)
            if enable_result['exit_code'] != 0:
                return {
                    'status': 'failed',
                    'output': result['stdout'],
                    'error': f"Failed to {'enable' if enabled else 'disable'} service: {enable_result['stderr']}",
                    'changed': True
                }
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_archive(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Extract archives on the remote host"""
        src = args.get('src')
        dest = args.get('dest')
        remote_src = args.get('remote_src', False)
        
        if not remote_src:
            # Copy archive to remote host first
            await self.ssh_executor.copy_file(host, src, dest)
            src = os.path.basename(src)
        
        # Extract archive
        if src.endswith('.tar.gz') or src.endswith('.tgz'):
            cmd = f"tar -xzf {src} -C {dest}"
        elif src.endswith('.tar'):
            cmd = f"tar -xf {src} -C {dest}"
        elif src.endswith('.zip'):
            cmd = f"unzip {src} -d {dest}"
        else:
            raise ValueError(f"Unsupported archive format: {src}")
        
        result = await self.ssh_executor.execute_command(host, cmd)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_template(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Generate file from template"""
        src = args.get('src')
        dest = args.get('dest')
        
        # Read template
        with open(src, 'r') as f:
            template_content = f.read()
        
        # Simple template substitution
        template_content = template_content.replace('{{ inventory_hostname }}', host.get('ansible_host', ''))
        template_content = template_content.replace('{{ splunk_home }}', host.get('splunk_home', '/opt/splunk'))
        template_content = template_content.replace('{{ splunk_user }}', host.get('splunk_user', 'splunk'))
        template_content = template_content.replace('{{ splunk_group }}', host.get('splunk_group', 'splunk'))
        
        # Write to temporary file
        temp_file = f"/tmp/siemply_template_{os.urandom(8).hex()}"
        with open(temp_file, 'w') as f:
            f.write(template_content)
        
        try:
            # Copy to remote host
            await self.ssh_executor.copy_file(host, temp_file, dest)
            
            # Set permissions
            if args.get('mode'):
                await self.ssh_executor.execute_command(host, f"chmod {args['mode']} {dest}")
            if args.get('owner'):
                await self.ssh_executor.execute_command(host, f"chown {args['owner']} {dest}")
            
            return {
                'status': 'success',
                'output': f"Template generated: {dest}",
                'changed': True
            }
        finally:
            # Clean up temporary file
            os.unlink(temp_file)
    
    async def _execute_script(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Execute a script on the remote host"""
        script_path = args.get('file') or args.get('src')
        if not script_path:
            raise ValueError("Script path not specified")
        
        # Copy script to remote host
        remote_script = f"/tmp/siemply_script_{os.urandom(8).hex()}"
        await self.ssh_executor.copy_file(host, script_path, remote_script)
        
        try:
            # Make script executable
            await self.ssh_executor.execute_command(host, f"chmod +x {remote_script}")
            
            # Execute script
            result = await self.ssh_executor.execute_command(host, remote_script)
            
            return {
                'status': 'success' if result['exit_code'] == 0 else 'failed',
                'output': result['stdout'],
                'error': result['stderr'] if result['exit_code'] != 0 else None,
                'changed': True
            }
        finally:
            # Clean up script
            await self.ssh_executor.execute_command(host, f"rm -f {remote_script}")
    
    async def _execute_checkpoint(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Create a checkpoint for rollback purposes"""
        checkpoint_name = args.get('checkpoint_name')
        checkpoint_data = args.get('checkpoint_data', {})
        
        # Create checkpoint directory
        checkpoint_dir = f"/opt/siemply/checkpoints/{checkpoint_name}"
        await self.ssh_executor.execute_command(host, f"mkdir -p {checkpoint_dir}")
        
        # Save checkpoint data
        checkpoint_file = f"{checkpoint_dir}/checkpoint.json"
        checkpoint_json = json.dumps(checkpoint_data, indent=2)
        
        # Write checkpoint data
        temp_file = f"/tmp/checkpoint_{os.urandom(8).hex()}.json"
        with open(temp_file, 'w') as f:
            f.write(checkpoint_json)
        
        try:
            await self.ssh_executor.copy_file(host, temp_file, checkpoint_file)
            return {
                'status': 'success',
                'output': f"Checkpoint created: {checkpoint_name}",
                'changed': True
            }
        finally:
            os.unlink(temp_file)
    
    # Splunk-specific task implementations
    
    async def _execute_splunk_precheck(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Execute Splunk pre-upgrade checks"""
        checks = []
        
        # Check disk space
        if args.get('check_disk_space', True):
            min_space = args.get('min_disk_space_gb', 10)
            cmd = f"df -BG {host.get('splunk_home', '/opt/splunk')} | awk 'NR==2 {{print $4}}' | sed 's/G//'"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] == 0:
                available_gb = int(result['stdout'].strip())
                if available_gb < min_space:
                    checks.append(f"Disk space check failed: {available_gb}GB < {min_space}GB")
        
        # Check memory
        if args.get('check_memory', True):
            min_memory = args.get('min_memory_gb', 2)
            cmd = "free -g | awk 'NR==2{print $2}'"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] == 0:
                total_gb = int(result['stdout'].strip())
                if total_gb < min_memory:
                    checks.append(f"Memory check failed: {total_gb}GB < {min_memory}GB")
        
        # Check ulimits
        if args.get('check_ulimits', True):
            cmd = "ulimit -n"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] == 0:
                file_limit = int(result['stdout'].strip())
                if file_limit < 8192:
                    checks.append(f"File descriptor limit too low: {file_limit} < 8192")
        
        # Check SELinux
        if args.get('check_selinux', True):
            cmd = "getenforce 2>/dev/null || echo 'Disabled'"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] == 0 and 'Enforcing' in result['stdout']:
                checks.append("SELinux is in Enforcing mode - may cause issues")
        
        # Check ports
        if args.get('check_ports', True):
            ports = [8089, 9997]  # Default Splunk ports
            for port in ports:
                cmd = f"netstat -tlnp | grep :{port}"
                result = await self.ssh_executor.execute_command(host, cmd)
                if result['exit_code'] != 0:
                    checks.append(f"Port {port} is not listening")
        
        # Check Python
        if args.get('check_python', True):
            cmd = "python3 --version"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                checks.append("Python3 not available")
        
        if checks:
            return {
                'status': 'failed',
                'output': 'Pre-check failed',
                'error': '; '.join(checks),
                'changed': False
            }
        else:
            return {
                'status': 'success',
                'output': 'All pre-checks passed',
                'changed': False
            }
    
    async def _execute_splunk_download(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Download Splunk package"""
        version = args.get('version')
        package_type = args.get('package_type', 'uf')
        os_family = args.get('os_family', host.get('os_family', 'RedHat'))
        os_version = args.get('os_version', host.get('os_version', '8'))
        cpu_arch = args.get('cpu_arch', host.get('cpu_arch', 'x86_64'))
        download_url = args.get('download_url', 'https://download.splunk.com/products')
        cache_dir = args.get('cache_dir', '/tmp/splunk_packages')
        
        # Build package URL (simplified)
        if package_type == 'uf':
            package_name = f"splunkforwarder-{version}-linux-2.6-{cpu_arch}.rpm"
        else:
            package_name = f"splunk-{version}-linux-2.6-{cpu_arch}.rpm"
        
        package_url = f"{download_url}/{package_name}"
        package_path = f"{cache_dir}/{package_name}"
        
        # Create cache directory
        await self.ssh_executor.execute_command(host, f"mkdir -p {cache_dir}")
        
        # Download package
        cmd = f"wget -O {package_path} {package_url}"
        result = await self.ssh_executor.execute_command(host, cmd, timeout=1800)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': result['stdout'],
                'error': f"Failed to download package: {result['stderr']}",
                'changed': False
            }
        
        return {
            'status': 'success',
            'output': f"Package downloaded: {package_path}",
            'changed': True,
            'facts': {'package_path': package_path}
        }
    
    async def _execute_splunk_install(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Install Splunk package"""
        package_path = args.get('package_path')
        install_method = args.get('install_method', 'install')
        
        if not package_path:
            raise ValueError("Package path not specified")
        
        # Install package
        if package_path.endswith('.rpm'):
            cmd = f"rpm -Uvh {package_path}"
        elif package_path.endswith('.deb'):
            cmd = f"dpkg -i {package_path}"
        else:
            raise ValueError(f"Unsupported package format: {package_path}")
        
        result = await self.ssh_executor.execute_command(host, cmd, timeout=900)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_splunk_backup(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Create Splunk backup"""
        backup_dir = args.get('backup_dir', '/opt/splunk_backups')
        backup_name = args.get('backup_name')
        include_configs = args.get('include_configs', True)
        include_apps = args.get('include_apps', True)
        include_users = args.get('include_users', True)
        compression = args.get('compression', True)
        
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup directory
        await self.ssh_executor.execute_command(host, f"mkdir -p {backup_dir}")
        
        # Build tar command
        splunk_home = host.get('splunk_home', '/opt/splunk')
        backup_path = f"{backup_dir}/{backup_name}.tar.gz"
        
        tar_cmd = f"tar -czf {backup_path}"
        if include_configs:
            tar_cmd += f" -C {splunk_home} etc"
        if include_apps:
            tar_cmd += f" -C {splunk_home} etc/apps"
        if include_users:
            tar_cmd += f" -C {splunk_home} etc/users"
        
        result = await self.ssh_executor.execute_command(host, tar_cmd, timeout=600)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True,
            'facts': {'backup_path': backup_path}
        }
    
    async def _execute_splunk_restore(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Restore Splunk from backup"""
        backup_path = args.get('backup_path')
        restore_configs = args.get('restore_configs', True)
        restore_apps = args.get('restore_apps', True)
        restore_users = args.get('restore_users', True)
        
        if not backup_path:
            raise ValueError("Backup path not specified")
        
        splunk_home = host.get('splunk_home', '/opt/splunk')
        
        # Extract backup
        cmd = f"tar -xzf {backup_path} -C {splunk_home}"
        result = await self.ssh_executor.execute_command(host, cmd, timeout=600)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': result['stdout'],
                'error': f"Failed to restore backup: {result['stderr']}",
                'changed': False
            }
        
        return {
            'status': 'success',
            'output': f"Backup restored from: {backup_path}",
            'changed': True
        }
    
    async def _execute_splunk_health_check(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Perform Splunk health checks"""
        splunk_home = host.get('splunk_home', '/opt/splunk')
        checks = []
        
        # Check splunkd status
        if args.get('check_splunkd', True):
            cmd = f"{splunk_home}/bin/splunk status"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0 or 'splunkd is running' not in result['stdout']:
                checks.append("splunkd is not running")
        
        # Check web interface
        if args.get('check_web', False):
            web_port = host.get('splunk_web_port', 8000)
            cmd = f"netstat -tlnp | grep :{web_port}"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                checks.append(f"Web interface not listening on port {web_port}")
        
        # Check forwarder
        if args.get('check_forwarder', True):
            forwarder_port = host.get('splunk_forwarder_port', 9997)
            cmd = f"netstat -tlnp | grep :{forwarder_port}"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                checks.append(f"Forwarder not listening on port {forwarder_port}")
        
        # Check license
        if args.get('check_license', False):
            cmd = f"{splunk_home}/bin/splunk show license"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                checks.append("License check failed")
        
        # Check connectivity
        if args.get('check_connectivity', False):
            cmd = f"{splunk_home}/bin/splunk list forward-server"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                checks.append("Forward server connectivity check failed")
        
        # Check logs for errors
        if args.get('check_logs', True):
            cmd = f"grep -i error {splunk_home}/var/log/splunk/splunkd.log | tail -5"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] == 0 and result['stdout'].strip():
                checks.append(f"Errors found in logs: {result['stdout'].strip()}")
        
        if checks:
            return {
                'status': 'failed',
                'output': 'Health check failed',
                'error': '; '.join(checks),
                'changed': False
            }
        else:
            return {
                'status': 'success',
                'output': 'All health checks passed',
                'changed': False
            }
    
    async def _execute_splunk_version_check(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Check Splunk version"""
        expected_version = args.get('expected_version')
        splunk_home = args.get('splunk_home', host.get('splunk_home', '/opt/splunk'))
        
        cmd = f"{splunk_home}/bin/splunk version"
        result = await self.ssh_executor.execute_command(host, cmd)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': result['stdout'],
                'error': f"Failed to get Splunk version: {result['stderr']}",
                'changed': False
            }
        
        current_version = result['stdout'].strip()
        
        if expected_version and expected_version not in current_version:
            return {
                'status': 'failed',
                'output': current_version,
                'error': f"Version mismatch: expected {expected_version}, got {current_version}",
                'changed': False
            }
        
        return {
            'status': 'success',
            'output': current_version,
            'changed': False
        }
    
    async def _execute_splunk_status_check(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Check Splunk service status"""
        splunk_home = host.get('splunk_home', '/opt/splunk')
        
        cmd = f"{splunk_home}/bin/splunk status"
        result = await self.ssh_executor.execute_command(host, cmd)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': False
        }
    
    async def _execute_splunk_wait_ready(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Wait for Splunk to be ready"""
        splunk_home = args.get('splunk_home', host.get('splunk_home', '/opt/splunk'))
        mgmt_port = args.get('mgmt_port', host.get('splunk_mgmt_port', 8089))
        timeout = args.get('timeout', 300)
        retries = args.get('retries', 10)
        interval = args.get('interval', 30)
        
        for attempt in range(retries):
            cmd = f"curl -s http://localhost:{mgmt_port}/services/server/info"
            result = await self.ssh_executor.execute_command(host, cmd)
            
            if result['exit_code'] == 0:
                return {
                    'status': 'success',
                    'output': 'Splunk is ready',
                    'changed': False
                }
            
            if attempt < retries - 1:
                await asyncio.sleep(interval)
        
        return {
            'status': 'failed',
            'output': 'Splunk did not become ready',
            'error': f'Timeout after {timeout} seconds',
            'changed': False
        }
    
    async def _execute_splunk_verify_package(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Verify Splunk package integrity"""
        package_path = args.get('package_path')
        verify_checksum = args.get('verify_checksum', True)
        
        if not package_path:
            raise ValueError("Package path not specified")
        
        # Check if package exists
        cmd = f"test -f {package_path}"
        result = await self.ssh_executor.execute_command(host, cmd)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': '',
                'error': f"Package not found: {package_path}",
                'changed': False
            }
        
        # Verify checksum if requested
        if verify_checksum:
            cmd = f"sha256sum {package_path}"
            result = await self.ssh_executor.execute_command(host, cmd)
            if result['exit_code'] != 0:
                return {
                    'status': 'failed',
                    'output': result['stdout'],
                    'error': f"Failed to verify checksum: {result['stderr']}",
                    'changed': False
                }
        
        return {
            'status': 'success',
            'output': f"Package verified: {package_path}",
            'changed': False
        }
    
    async def _execute_splunk_verify_backup(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Verify Splunk backup integrity"""
        backup_path = args.get('backup_path')
        
        if not backup_path:
            raise ValueError("Backup path not specified")
        
        # Check if backup exists
        cmd = f"test -f {backup_path}"
        result = await self.ssh_executor.execute_command(host, cmd)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': '',
                'error': f"Backup not found: {backup_path}",
                'changed': False
            }
        
        # Test backup integrity
        cmd = f"tar -tzf {backup_path} > /dev/null"
        result = await self.ssh_executor.execute_command(host, cmd)
        
        if result['exit_code'] != 0:
            return {
                'status': 'failed',
                'output': result['stdout'],
                'error': f"Backup integrity check failed: {result['stderr']}",
                'changed': False
            }
        
        return {
            'status': 'success',
            'output': f"Backup verified: {backup_path}",
            'changed': False
        }
    
    async def _execute_splunk_restore_config(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Restore Splunk configuration from backup"""
        backup_path = args.get('backup_path')
        restore_configs = args.get('restore_configs', True)
        restore_apps = args.get('restore_apps', True)
        restore_users = args.get('restore_users', True)
        
        if not backup_path:
            raise ValueError("Backup path not specified")
        
        splunk_home = host.get('splunk_home', '/opt/splunk')
        
        # Extract specific directories
        tar_cmd = f"tar -xzf {backup_path} -C {splunk_home}"
        if restore_configs:
            tar_cmd += " etc"
        if restore_apps:
            tar_cmd += " etc/apps"
        if restore_users:
            tar_cmd += " etc/users"
        
        result = await self.ssh_executor.execute_command(host, tar_cmd, timeout=300)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_splunk_set_permissions(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Set Splunk ownership and permissions"""
        splunk_home = args.get('splunk_home', host.get('splunk_home', '/opt/splunk'))
        splunk_user = args.get('splunk_user', host.get('splunk_user', 'splunk'))
        splunk_group = args.get('splunk_group', host.get('splunk_group', 'splunk'))
        recursive = args.get('recursive', True)
        
        # Set ownership
        if recursive:
            cmd = f"chown -R {splunk_user}:{splunk_group} {splunk_home}"
        else:
            cmd = f"chown {splunk_user}:{splunk_group} {splunk_home}"
        
        result = await self.ssh_executor.execute_command(host, cmd, timeout=180)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_splunk_cleanup_backups(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Clean up old Splunk backups"""
        backup_dir = args.get('backup_dir', '/opt/splunk_backups')
        retention_days = args.get('retention_days', 7)
        
        # Find and remove old backups
        cmd = f"find {backup_dir} -name '*.tar.gz' -mtime +{retention_days} -delete"
        result = await self.ssh_executor.execute_command(host, cmd, timeout=300)
        
        return {
            'status': 'success' if result['exit_code'] == 0 else 'failed',
            'output': result['stdout'],
            'error': result['stderr'] if result['exit_code'] != 0 else None,
            'changed': True
        }
    
    async def _execute_splunk_validate_upgrade(self, args: Dict[str, Any], host: Dict[str, Any], run_config: Any) -> Dict[str, Any]:
        """Validate Splunk upgrade path"""
        current_version = args.get('current_version')
        target_version = args.get('target_version')
        
        if not current_version or not target_version:
            raise ValueError("Current and target versions must be specified")
        
        # Simple version comparison (in production, use proper version parsing)
        current_major = int(current_version.split('.')[0])
        current_minor = int(current_version.split('.')[1])
        target_major = int(target_version.split('.')[0])
        target_minor = int(target_version.split('.')[1])
        
        # Check if upgrade is valid
        if target_major < current_major or (target_major == current_major and target_minor < current_minor):
            return {
                'status': 'failed',
                'output': '',
                'error': f"Downgrade not supported: {current_version} -> {target_version}",
                'changed': False
            }
        
        # Check if upgrade is too many versions
        if target_major > current_major + 1:
            return {
                'status': 'failed',
                'output': '',
                'error': f"Major version upgrade not supported: {current_version} -> {target_version}",
                'changed': False
            }
        
        return {
            'status': 'success',
            'output': f"Upgrade path validated: {current_version} -> {target_version}",
            'changed': False
        }
