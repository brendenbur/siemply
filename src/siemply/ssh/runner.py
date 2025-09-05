"""
SSH runner using Paramiko for executing commands and file operations
"""
import io
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import paramiko
from jinja2 import Template


class SSHRunner:
    """SSH runner for executing commands and file operations on remote hosts"""
    
    def __init__(self, hostname: str, port: int, username: str, 
                 auth_type: str, private_key: Optional[str] = None,
                 private_key_passphrase: Optional[str] = None,
                 password: Optional[str] = None,
                 connect_timeout: int = 10, command_timeout: int = 60):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.auth_type = auth_type
        self.private_key = private_key
        self.private_key_passphrase = private_key_passphrase
        self.password = password
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        
        self.client = None
        self.sftp = None

    def connect(self) -> Tuple[bool, str]:
        """Connect to the remote host"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare authentication
            auth_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
                'timeout': self.connect_timeout,
            }
            
            if self.auth_type == "key":
                if not self.private_key:
                    return False, "Private key not provided"
                
                # Create key object
                key_obj = None
                try:
                    # Try different key types
                    for key_class in [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                        try:
                            key_obj = key_class.from_private_key(
                                io.StringIO(self.private_key),
                                password=self.private_key_passphrase
                            )
                            break
                        except paramiko.ssh_exception.SSHException:
                            continue
                    
                    if not key_obj:
                        return False, "Invalid private key format"
                    
                    auth_kwargs['pkey'] = key_obj
                except Exception as e:
                    return False, f"Key authentication failed: {str(e)}"
            else:  # password
                if not self.password:
                    return False, "Password not provided"
                auth_kwargs['password'] = self.password
            
            # Connect
            self.client.connect(**auth_kwargs)
            
            # Test connection with a simple command
            stdin, stdout, stderr = self.client.exec_command("echo 'SSH connection successful'", timeout=5)
            stdout.read()
            
            return True, "Connection successful"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        """Disconnect from the remote host"""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.client:
            self.client.close()
            self.client = None

    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Execute a command on the remote host"""
        if not self.client:
            return -1, "", "Not connected"
        
        try:
            timeout = timeout or self.command_timeout
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Read output with size limit
            stdout_data = stdout.read(65536).decode('utf-8', errors='replace')
            stderr_data = stderr.read(65536).decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()
            
            return exit_code, stdout_data, stderr_data
            
        except Exception as e:
            return -1, "", f"Command execution failed: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """Test SSH connection with a simple command"""
        success, message = self.connect()
        if success:
            exit_code, stdout, stderr = self.execute_command("echo 'test'")
            if exit_code == 0:
                self.disconnect()
                return True, "Connection test successful"
            else:
                self.disconnect()
                return False, f"Command failed: {stderr}"
        else:
            return False, message

    def copy_file(self, local_path: str, remote_path: str, mode: Optional[str] = None) -> Tuple[bool, str]:
        """Copy a file to the remote host using SFTP"""
        if not self.client:
            success, message = self.connect()
            if not success:
                return False, message
        
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()
            
            # Upload file
            self.sftp.put(local_path, remote_path)
            
            # Set permissions if specified
            if mode:
                try:
                    # Convert octal mode to integer
                    mode_int = int(mode, 8)
                    self.sftp.chmod(remote_path, mode_int)
                except ValueError:
                    pass  # Invalid mode format
            
            return True, "File copied successfully"
            
        except Exception as e:
            return False, f"File copy failed: {str(e)}"

    def copy_content(self, content: str, remote_path: str, mode: Optional[str] = None) -> Tuple[bool, str]:
        """Copy content directly to a file on the remote host"""
        if not self.client:
            success, message = self.connect()
            if not success:
                return False, message
        
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()
            
            # Write content to remote file
            with self.sftp.open(remote_path, 'w') as remote_file:
                remote_file.write(content)
            
            # Set permissions if specified
            if mode:
                try:
                    mode_int = int(mode, 8)
                    self.sftp.chmod(remote_path, mode_int)
                except ValueError:
                    pass
            
            return True, "Content copied successfully"
            
        except Exception as e:
            return False, f"Content copy failed: {str(e)}"

    def render_template(self, template_content: str, variables: Dict) -> str:
        """Render a Jinja2 template with variables"""
        try:
            template = Template(template_content)
            return template.render(**variables)
        except Exception as e:
            raise Exception(f"Template rendering failed: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class SSHManager:
    """Manager for SSH connections and operations"""
    
    @staticmethod
    def test_host(hostname: str, port: int, username: str, auth_type: str,
                  private_key: Optional[str] = None, private_key_passphrase: Optional[str] = None,
                  password: Optional[str] = None) -> Tuple[bool, str]:
        """Test SSH connection to a host"""
        with SSHRunner(hostname, port, username, auth_type, private_key, 
                      private_key_passphrase, password) as runner:
            return runner.test_connection()

    @staticmethod
    def execute_playbook_task(host: 'Host', task: Dict) -> Tuple[bool, str, str]:
        """Execute a single playbook task on a host"""
        with SSHRunner(
            host.hostname, host.port, host.username, host.auth_type,
            host.get_private_key(), host.get_private_key_passphrase(),
            host.get_password()
        ) as runner:
            
            success, message = runner.connect()
            if not success:
                return False, message, ""
            
            task_type = task.get('type', 'command')
            task_name = task.get('name', 'unnamed')
            
            try:
                if task_type == 'command':
                    cmd = task.get('cmd', '')
                    timeout = task.get('timeout', 60)
                    ignore_errors = task.get('ignore_errors', False)
                    
                    exit_code, stdout, stderr = runner.execute_command(cmd, timeout)
                    
                    if exit_code == 0:
                        return True, f"Task '{task_name}' completed successfully", stdout
                    elif ignore_errors:
                        return True, f"Task '{task_name}' completed with errors (ignored)", stderr
                    else:
                        return False, f"Task '{task_name}' failed with exit code {exit_code}", stderr
                
                elif task_type == 'copy':
                    src = task.get('src', '')
                    dest = task.get('dest', '')
                    mode = task.get('mode', None)
                    
                    if not os.path.exists(src):
                        return False, f"Source file '{src}' not found", ""
                    
                    success, message = runner.copy_file(src, dest, mode)
                    if success:
                        return True, f"Task '{task_name}' completed successfully", message
                    else:
                        return False, f"Task '{task_name}' failed: {message}", ""
                
                elif task_type == 'template':
                    src = task.get('src', '')
                    dest = task.get('dest', '')
                    mode = task.get('mode', None)
                    vars_dict = task.get('vars', {})
                    
                    if not os.path.exists(src):
                        return False, f"Template file '{src}' not found", ""
                    
                    # Read template content
                    with open(src, 'r') as f:
                        template_content = f.read()
                    
                    # Render template
                    rendered_content = runner.render_template(template_content, vars_dict)
                    
                    # Copy rendered content
                    success, message = runner.copy_content(rendered_content, dest, mode)
                    if success:
                        return True, f"Task '{task_name}' completed successfully", message
                    else:
                        return False, f"Task '{task_name}' failed: {message}", ""
                
                else:
                    return False, f"Unknown task type: {task_type}", ""
            
            except Exception as e:
                return False, f"Task '{task_name}' failed with exception: {str(e)}", ""
