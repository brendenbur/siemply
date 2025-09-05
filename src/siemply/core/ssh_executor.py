"""
Siemply SSH Executor - Secure remote execution via asyncssh
"""

import asyncio
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import asyncssh
import yaml

from .secrets import SecretsManager


@dataclass
class SSHResult:
    """Result of an SSH command execution"""
    exit_code: int
    stdout: str
    stderr: str
    duration: float


class SSHExecutor:
    """
    SSH executor for remote command execution and file operations
    """
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets = secrets_manager
        self.logger = logging.getLogger(__name__)
        
        # SSH connection cache
        self.connections: Dict[str, asyncssh.SSHClientConnection] = {}
        
        # Load SSH profiles
        self.ssh_profiles = {}
        self._load_ssh_profiles()
    
    def _load_ssh_profiles(self):
        """Load SSH profiles from configuration"""
        try:
            with open('config/ssh_profiles.yml', 'r') as f:
                config = yaml.safe_load(f)
                self.ssh_profiles = config.get('profiles', {})
        except Exception as e:
            self.logger.warning(f"Failed to load SSH profiles: {e}")
            # Use default profile
            self.ssh_profiles = {
                'default': {
                    'user': 'root',
                    'port': 22,
                    'auth_method': 'key',
                    'timeout': 30,
                    'connect_timeout': 10
                }
            }
    
    async def get_connection(self, host: Dict[str, Any], profile_name: Optional[str] = None) -> asyncssh.SSHClientConnection:
        """
        Get or create SSH connection to host
        
        Args:
            host: Host information
            profile_name: SSH profile name to use
            
        Returns:
            SSH connection
        """
        host_id = host.get('ansible_host', host.get('name', 'unknown'))
        
        # Check if connection already exists
        if host_id in self.connections:
            return self.connections[host_id]
        
        # Determine profile to use
        if not profile_name:
            # Try to determine from host environment
            if 'prod' in host_id.lower():
                profile_name = 'prod'
            elif 'stage' in host_id.lower():
                profile_name = 'stage'
            elif 'dev' in host_id.lower():
                profile_name = 'dev'
            else:
                profile_name = 'default'
        
        profile = self.ssh_profiles.get(profile_name, self.ssh_profiles.get('default', {}))
        
        # Get host connection details
        hostname = host.get('ansible_host', host.get('name'))
        port = host.get('ansible_port', profile.get('port', 22))
        user = host.get('ansible_user', profile.get('user', 'root'))
        
        # Get authentication details
        auth_method = profile.get('auth_method', 'key')
        private_key_file = host.get('ansible_ssh_private_key_file', profile.get('private_key_file'))
        
        if not private_key_file:
            raise ValueError(f"No private key file specified for host {host_id}")
        
        # Expand tilde in path
        private_key_file = os.path.expanduser(private_key_file)
        
        # Get key passphrase from secrets
        key_passphrase = None
        if profile.get('key_passphrase'):
            key_passphrase = await self.secrets.get_secret(profile['key_passphrase'])
        
        # Build connection options
        options = asyncssh.SSHClientConnectionOptions(
            username=user,
            port=port,
            client_keys=[private_key_file],
            passphrase=key_passphrase,
            connect_timeout=profile.get('connect_timeout', 10),
            login_timeout=profile.get('timeout', 30),
            keepalive_interval=profile.get('keepalive_interval', 30),
            keepalive_count_max=profile.get('keepalive_count_max', 3),
            compression=profile.get('compression', True),
            compression_level=profile.get('compression_level', 6),
            ciphers=profile.get('ciphers', []),
            kex_algorithms=profile.get('kex_algorithms', []),
            mac_algorithms=profile.get('mac_algorithms', []),
            host_key_checking=profile.get('host_key_checking', True),
            known_hosts=profile.get('known_hosts_file'),
            strict_host_key_checking=profile.get('strict_host_key_checking', True)
        )
        
        # Handle bastion/jump host
        bastion = profile.get('bastion', {})
        if bastion.get('enabled', False):
            # Connect through bastion host
            bastion_conn = await self._get_bastion_connection(bastion)
            # TODO: Implement bastion connection forwarding
            raise NotImplementedError("Bastion host support not yet implemented")
        
        try:
            # Establish connection
            connection = await asyncssh.connect(hostname, options=options)
            self.connections[host_id] = connection
            self.logger.info(f"SSH connection established to {host_id}")
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {host_id}: {e}")
            raise
    
    async def _get_bastion_connection(self, bastion_config: Dict[str, Any]) -> asyncssh.SSHClientConnection:
        """Get connection to bastion host"""
        bastion_host = bastion_config.get('host')
        bastion_port = bastion_config.get('port', 22)
        bastion_user = bastion_config.get('user')
        bastion_key = bastion_config.get('private_key_file')
        
        if not all([bastion_host, bastion_user, bastion_key]):
            raise ValueError("Bastion host configuration incomplete")
        
        # Expand tilde in path
        bastion_key = os.path.expanduser(bastion_key)
        
        # Get key passphrase
        key_passphrase = None
        if bastion_config.get('key_passphrase'):
            key_passphrase = await self.secrets.get_secret(bastion_config['key_passphrase'])
        
        options = asyncssh.SSHClientConnectionOptions(
            username=bastion_user,
            port=bastion_port,
            client_keys=[bastion_key],
            passphrase=key_passphrase,
            connect_timeout=10,
            login_timeout=30
        )
        
        return await asyncssh.connect(bastion_host, options=options)
    
    async def execute_command(self, host: Dict[str, Any], command: str, timeout: int = 300, 
                            profile_name: Optional[str] = None) -> SSHResult:
        """
        Execute a command on the remote host
        
        Args:
            host: Host information
            command: Command to execute
            timeout: Command timeout in seconds
            profile_name: SSH profile name to use
            
        Returns:
            SSHResult with command output
        """
        import time
        start_time = time.time()
        
        try:
            connection = await self.get_connection(host, profile_name)
            
            # Execute command
            result = await connection.run(command, timeout=timeout)
            
            duration = time.time() - start_time
            
            return SSHResult(
                exit_code=result.exit_status,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.logger.error(f"Command timeout on {host.get('ansible_host', 'unknown')}: {command}")
            return SSHResult(
                exit_code=124,  # Timeout exit code
                stdout='',
                stderr=f'Command timed out after {timeout} seconds',
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Command failed on {host.get('ansible_host', 'unknown')}: {e}")
            return SSHResult(
                exit_code=1,
                stdout='',
                stderr=str(e),
                duration=duration
            )
    
    async def copy_file(self, host: Dict[str, Any], local_path: str, remote_path: str,
                       profile_name: Optional[str] = None) -> bool:
        """
        Copy a file to the remote host
        
        Args:
            host: Host information
            local_path: Local file path
            remote_path: Remote file path
            profile_name: SSH profile name to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = await self.get_connection(host, profile_name)
            
            # Copy file using SFTP
            async with connection.start_sftp_client() as sftp:
                await sftp.put(local_path, remote_path)
            
            self.logger.info(f"File copied: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {local_path} to {remote_path}: {e}")
            return False
    
    async def copy_file_from_remote(self, host: Dict[str, Any], remote_path: str, local_path: str,
                                   profile_name: Optional[str] = None) -> bool:
        """
        Copy a file from the remote host
        
        Args:
            host: Host information
            remote_path: Remote file path
            local_path: Local file path
            profile_name: SSH profile name to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = await self.get_connection(host, profile_name)
            
            # Copy file using SFTP
            async with connection.start_sftp_client() as sftp:
                await sftp.get(remote_path, local_path)
            
            self.logger.info(f"File copied: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {remote_path} to {local_path}: {e}")
            return False
    
    async def copy_directory(self, host: Dict[str, Any], local_dir: str, remote_dir: str,
                            profile_name: Optional[str] = None) -> bool:
        """
        Copy a directory to the remote host
        
        Args:
            host: Host information
            local_dir: Local directory path
            remote_dir: Remote directory path
            profile_name: SSH profile name to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = await self.get_connection(host, profile_name)
            
            # Create remote directory
            await self.execute_command(host, f"mkdir -p {remote_dir}", profile_name=profile_name)
            
            # Copy directory using SFTP
            async with connection.start_sftp_client() as sftp:
                await self._copy_directory_recursive(sftp, local_dir, remote_dir)
            
            self.logger.info(f"Directory copied: {local_dir} -> {remote_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy directory {local_dir} to {remote_dir}: {e}")
            return False
    
    async def _copy_directory_recursive(self, sftp, local_dir: str, remote_dir: str):
        """Recursively copy directory contents"""
        for root, dirs, files in os.walk(local_dir):
            # Create remote directory
            rel_path = os.path.relpath(root, local_dir)
            if rel_path == '.':
                remote_path = remote_dir
            else:
                remote_path = f"{remote_dir}/{rel_path}"
            
            try:
                await sftp.mkdir(remote_path)
            except:
                pass  # Directory might already exist
            
            # Copy files
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = f"{remote_path}/{file}"
                await sftp.put(local_file, remote_file)
    
    async def execute_script(self, host: Dict[str, Any], script_content: str, 
                            script_name: str = "script.sh", timeout: int = 300,
                            profile_name: Optional[str] = None) -> SSHResult:
        """
        Execute a script on the remote host
        
        Args:
            host: Host information
            script_content: Script content to execute
            script_name: Name of the script file
            timeout: Script timeout in seconds
            profile_name: SSH profile name to use
            
        Returns:
            SSHResult with script output
        """
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            try:
                # Copy script to remote host
                remote_script = f"/tmp/{script_name}"
                success = await self.copy_file(host, temp_script, remote_script, profile_name)
                
                if not success:
                    return SSHResult(
                        exit_code=1,
                        stdout='',
                        stderr='Failed to copy script to remote host',
                        duration=0
                    )
                
                # Make script executable
                await self.execute_command(host, f"chmod +x {remote_script}", profile_name=profile_name)
                
                # Execute script
                result = await self.execute_command(host, remote_script, timeout=timeout, profile_name=profile_name)
                
                # Clean up script
                await self.execute_command(host, f"rm -f {remote_script}", profile_name=profile_name)
                
                return result
                
            finally:
                # Clean up local temporary file
                os.unlink(temp_script)
                
        except Exception as e:
            self.logger.error(f"Failed to execute script on {host.get('ansible_host', 'unknown')}: {e}")
            return SSHResult(
                exit_code=1,
                stdout='',
                stderr=str(e),
                duration=0
            )
    
    async def test_connection(self, host: Dict[str, Any], profile_name: Optional[str] = None) -> bool:
        """
        Test SSH connection to host
        
        Args:
            host: Host information
            profile_name: SSH profile name to use
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = await self.execute_command(host, "echo 'connection test'", timeout=10, profile_name=profile_name)
            return result.exit_code == 0
        except Exception as e:
            self.logger.error(f"Connection test failed for {host.get('ansible_host', 'unknown')}: {e}")
            return False
    
    async def close_connection(self, host: Dict[str, Any]):
        """Close SSH connection to host"""
        host_id = host.get('ansible_host', host.get('name', 'unknown'))
        
        if host_id in self.connections:
            try:
                await self.connections[host_id].close()
                del self.connections[host_id]
                self.logger.info(f"SSH connection closed for {host_id}")
            except Exception as e:
                self.logger.warning(f"Error closing connection to {host_id}: {e}")
    
    async def close_all_connections(self):
        """Close all SSH connections"""
        for host_id in list(self.connections.keys()):
            try:
                await self.connections[host_id].close()
                del self.connections[host_id]
            except Exception as e:
                self.logger.warning(f"Error closing connection to {host_id}: {e}")
        
        self.logger.info("All SSH connections closed")
    
    async def get_host_info(self, host: Dict[str, Any], profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get system information from host
        
        Args:
            host: Host information
            profile_name: SSH profile name to use
            
        Returns:
            Dictionary with host information
        """
        info = {}
        
        try:
            # Get OS information
            result = await self.execute_command(host, "uname -a", profile_name=profile_name)
            if result.exit_code == 0:
                info['uname'] = result.stdout.strip()
            
            # Get memory information
            result = await self.execute_command(host, "free -h", profile_name=profile_name)
            if result.exit_code == 0:
                info['memory'] = result.stdout.strip()
            
            # Get disk information
            result = await self.execute_command(host, "df -h", profile_name=profile_name)
            if result.exit_code == 0:
                info['disk'] = result.stdout.strip()
            
            # Get CPU information
            result = await self.execute_command(host, "lscpu", profile_name=profile_name)
            if result.exit_code == 0:
                info['cpu'] = result.stdout.strip()
            
            # Get network information
            result = await self.execute_command(host, "ip addr show", profile_name=profile_name)
            if result.exit_code == 0:
                info['network'] = result.stdout.strip()
            
            # Get running processes
            result = await self.execute_command(host, "ps aux | head -20", profile_name=profile_name)
            if result.exit_code == 0:
                info['processes'] = result.stdout.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to get host info for {host.get('ansible_host', 'unknown')}: {e}")
            info['error'] = str(e)
        
        return info
