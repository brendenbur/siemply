"""
Siemply CLI - Main entry point
"""

import asyncio
import logging
import sys
from typing import List, Optional
import click
from pathlib import Path

from .commands import (
    hosts_command,
    run_command,
    script_command,
    check_command,
    audit_command,
    config_command
)


@click.group()
@click.option('--config-dir', '-c', default='config', 
              help='Configuration directory')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose logging')
@click.option('--debug', '-d', is_flag=True, 
              help='Enable debug logging')
@click.pass_context
def main(ctx, config_dir, verbose, debug):
    """
    Siemply - Splunk Infrastructure Orchestration Framework
    
    A lightweight, opinionated orchestration framework for managing Splunk
    Universal Forwarder and Splunk Enterprise deployments across Linux hosts.
    """
    # Set up logging
    log_level = logging.WARNING
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['config_dir'] = config_dir
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug


# Add command groups
main.add_command(hosts_command)
main.add_command(run_command)
main.add_command(script_command)
main.add_command(check_command)
main.add_command(audit_command)
main.add_command(config_command)


@main.command()
@click.option('--version', is_flag=True, help='Show version information')
def info(version):
    """Show Siemply information"""
    if version:
        click.echo("Siemply v1.0.0")
        click.echo("Splunk Infrastructure Orchestration Framework")
        click.echo("https://github.com/siemply/siemply")
    else:
        click.echo("Siemply - Splunk Infrastructure Orchestration Framework")
        click.echo("")
        click.echo("Commands:")
        click.echo("  hosts     Manage inventory hosts and groups")
        click.echo("  run       Execute playbooks against hosts")
        click.echo("  script    Run custom Python scripts on hosts")
        click.echo("  check     Perform health checks on hosts")
        click.echo("  audit     View audit logs and reports")
        click.echo("  config    Manage configuration")
        click.echo("")
        click.echo("Use 'siemply <command> --help' for more information.")


@main.command()
@click.option('--project-name', '-n', required=True, 
              help='Name of the project to initialize')
@click.option('--template', '-t', 
              help='Template to use for initialization')
@click.pass_context
def init(ctx, project_name, template):
    """Initialize a new Siemply project"""
    config_dir = ctx.obj['config_dir']
    
    try:
        # Create project directory
        project_dir = Path(project_name)
        project_dir.mkdir(exist_ok=True)
        
        # Create config directory
        config_path = project_dir / config_dir
        config_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (project_dir / 'plays').mkdir(exist_ok=True)
        (project_dir / 'scripts').mkdir(exist_ok=True)
        (project_dir / 'reports').mkdir(exist_ok=True)
        (project_dir / 'logs').mkdir(exist_ok=True)
        
        # Create default inventory
        inventory_file = config_path / 'inventory.yml'
        if not inventory_file.exists():
            inventory_content = """# Siemply Inventory Configuration
all:
  children:
    # Production environments
    prod:
      children:
        prod-web:
          hosts:
            web-01:
              ansible_host: 192.168.1.10
              ansible_user: splunk
              ansible_ssh_private_key_file: ~/.ssh/splunk_prod
              splunk_type: uf
              splunk_version: 9.1.2
              os_family: RedHat
              os_version: "8"
              cpu_arch: x86_64
              memory_gb: 8
              disk_gb: 100
        prod-search:
          hosts:
            search-01:
              ansible_host: 192.168.1.20
              ansible_user: splunk
              ansible_ssh_private_key_file: ~/.ssh/splunk_prod
              splunk_type: enterprise
              splunk_version: 9.1.2
              os_family: RedHat
              os_version: "8"
              cpu_arch: x86_64
              memory_gb: 32
              disk_gb: 500
              splunk_role: search_head
      
      vars:
        splunk_home: /opt/splunk
        splunk_user: splunk
        splunk_group: splunk
        splunk_mgmt_port: 8089
        splunk_web_port: 8000
        splunk_forwarder_port: 9997
        splunk_indexer_port: 8080
        upgrade_timeout: 1800
        health_check_timeout: 300
        backup_retention_days: 7
        
    # Staging environment
    stage:
      children:
        stage-all:
          hosts:
            stage-01:
              ansible_host: 192.168.2.10
              ansible_user: splunk
              ansible_ssh_private_key_file: ~/.ssh/splunk_stage
              splunk_type: uf
              splunk_version: 9.2.2
              os_family: Ubuntu
              os_version: "22.04"
              cpu_arch: x86_64
              memory_gb: 4
              disk_gb: 50
      
      vars:
        splunk_home: /opt/splunk
        splunk_user: splunk
        splunk_group: splunk
        upgrade_timeout: 900
        health_check_timeout: 180

  vars:
    # Global variables
    ansible_ssh_common_args: '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    ansible_ssh_retries: 3
    ansible_ssh_timeout: 30
    ansible_python_interpreter: /usr/bin/python3
    
    # Splunk global settings
    splunk_download_base_url: "https://download.splunk.com/products"
    splunk_package_cache_dir: "/tmp/splunk_packages"
    splunk_backup_dir: "/opt/splunk_backups"
    
    # Security settings
    ssh_cipher_preference: "aes256-gcm@openssh.com,aes128-gcm@openssh.com"
    ssh_kex_preference: "curve25519-sha256,curve25519-sha256@libssh.org"
    ssh_mac_preference: "hmac-sha2-256,hmac-sha2-512"
    
    # Rate limiting
    max_concurrent_upgrades: 5
    upgrade_batch_size: 10
    upgrade_batch_delay: 300  # 5 minutes between batches
    
    # Monitoring
    enable_health_checks: true
    enable_rollback_on_failure: true
    max_failures_before_quarantine: 3
"""
            inventory_file.write_text(inventory_content)
        
        # Create default SSH profiles
        ssh_profiles_file = config_path / 'ssh_profiles.yml'
        if not ssh_profiles_file.exists():
            ssh_profiles_content = """# SSH Connection Profiles
profiles:
  # Production SSH profile with high security
  prod:
    user: splunk
    port: 22
    auth_method: key
    private_key_file: ~/.ssh/splunk_prod
    public_key_file: ~/.ssh/splunk_prod.pub
    key_passphrase: null
    timeout: 30
    connect_timeout: 10
    keepalive_interval: 30
    keepalive_count_max: 3
    
    # Security settings
    ciphers:
      - aes256-gcm@openssh.com
      - aes128-gcm@openssh.com
      - aes256-ctr
      - aes128-ctr
    kex_algorithms:
      - curve25519-sha256
      - curve25519-sha256@libssh.org
      - ecdh-sha2-nistp521
      - ecdh-sha2-nistp384
    mac_algorithms:
      - hmac-sha2-256
      - hmac-sha2-512
      - hmac-sha1
    
    # Host key verification
    host_key_checking: true
    known_hosts_file: ~/.ssh/known_hosts
    strict_host_key_checking: true
    
    # Compression
    compression: true
    compression_level: 6
    
    # Connection multiplexing
    control_master: auto
    control_path: ~/.ssh/siemply_%h_%p_%r
    control_persist: 300
    
    # Bastion/Jump host configuration
    bastion:
      enabled: false
      host: null
      user: null
      port: 22
      private_key_file: null
    
    # Retry settings
    retry_attempts: 3
    retry_delay: 5
    exponential_backoff: true

# Default profile selection based on environment
default_profiles:
  prod: prod
  stage: stage
  dev: dev
  emergency: emergency

# Global SSH settings
global:
  # Connection pooling
  max_connections_per_host: 5
  connection_pool_timeout: 300
  
  # Logging
  log_level: INFO
  log_ssh_commands: false
  log_ssh_output: false
  
  # Performance tuning
  tcp_keepalive: true
  tcp_keepalive_idle: 60
  tcp_keepalive_interval: 30
  tcp_keepalive_count: 3
  
  # Security defaults
  preferred_authentications: "publickey,password"
  password_authentication: false
  challenge_response_authentication: false
  gssapi_authentication: false
  gssapi_key_exchange: false
  gssapi_delegate_credentials: false
"""
            ssh_profiles_file.write_text(ssh_profiles_content)
        
        # Create default playbook
        playbook_file = project_dir / 'plays' / 'upgrade-uf.yml'
        if not playbook_file.exists():
            playbook_content = """# Siemply Play Configuration
name: "Splunk Universal Forwarder Upgrade"
description: "Upgrade Splunk Universal Forwarder to specified version with health checks and rollback"
version: "1.0.0"
author: "Siemply Framework"
created: "2024-01-15"

# Execution settings
execution:
  strategy: rolling
  max_failures: 3
  max_failures_percentage: 10
  batch_size: 10
  batch_delay: 300  # 5 minutes between batches
  soak_time: 600    # 10 minutes soak time before next batch
  timeout: 3600     # 1 hour total timeout
  retry_attempts: 3
  retry_delay: 30
  exponential_backoff: true

# Variables
vars:
  target_version: "9.2.2"
  backup_enabled: true
  health_check_enabled: true
  rollback_enabled: true
  pre_upgrade_checks: true
  post_upgrade_checks: true
  
  # Package settings
  package_download_timeout: 1800
  package_checksum_verification: true
  package_cache_dir: "/tmp/splunk_packages"
  
  # Service settings
  service_stop_timeout: 60
  service_start_timeout: 120
  service_restart_timeout: 180
  
  # Backup settings
  backup_retention_days: 7
  backup_compression: true
  
  # Health check settings
  health_check_retries: 5
  health_check_interval: 30
  health_check_timeout: 300

# Tasks
tasks:
  # Pre-upgrade phase
  - name: "Pre-upgrade system checks"
    phase: pre_upgrade
    tasks:
      - name: "Check system requirements"
        task: splunk_precheck
        args:
          check_disk_space: true
          min_disk_space_gb: 10
          check_memory: true
          min_memory_gb: 2
          check_ulimits: true
          check_selinux: true
          check_ports: true
          check_python: true
        retries: 3
        retry_delay: 10
        timeout: 300
        
      - name: "Check current Splunk version"
        task: command
        args:
          cmd: "{{ splunk_home }}/bin/splunk version"
        register: current_version
        timeout: 30
        
      - name: "Validate version upgrade path"
        task: splunk_validate_upgrade
        args:
          current_version: "{{ current_version.stdout }}"
          target_version: "{{ target_version }}"
        timeout: 60
        
      - name: "Check for running processes"
        task: splunk_status_check
        args:
          check_splunkd: true
          check_web: false
          check_forwarder: true
        timeout: 30
        
      - name: "Create upgrade checkpoint"
        task: checkpoint
        args:
          checkpoint_name: "pre_upgrade_{{ target_version }}"
          checkpoint_data:
            current_version: "{{ current_version.stdout }}"
            timestamp: "{{ ansible_date_time.iso8601 }}"
            host: "{{ inventory_hostname }}"
        timeout: 30

  # Download phase
  - name: "Download Splunk package"
    phase: download
    tasks:
      - name: "Create package cache directory"
        task: file
        args:
          path: "{{ package_cache_dir }}"
          state: directory
          mode: "0755"
          owner: "{{ splunk_user }}"
          group: "{{ splunk_group }}"
        timeout: 30
        
      - name: "Download Splunk Universal Forwarder package"
        task: splunk_download
        args:
          version: "{{ target_version }}"
          package_type: "uf"
          os_family: "{{ os_family }}"
          os_version: "{{ os_version }}"
          cpu_arch: "{{ cpu_arch }}"
          download_url: "{{ splunk_download_base_url }}"
          cache_dir: "{{ package_cache_dir }}"
          verify_checksum: "{{ package_checksum_verification }}"
        retries: 3
        retry_delay: 60
        timeout: "{{ package_download_timeout }}"
        
      - name: "Verify package integrity"
        task: splunk_verify_package
        args:
          package_path: "{{ package_cache_dir }}/splunkforwarder-{{ target_version }}-{{ os_family }}-{{ os_version }}-{{ cpu_arch }}.rpm"
          verify_checksum: true
        timeout: 120

  # Backup phase
  - name: "Backup current installation"
    phase: backup
    when: "{{ backup_enabled }}"
    tasks:
      - name: "Stop Splunk service"
        task: service
        args:
          name: "SplunkForwarder"
          state: stopped
        timeout: "{{ service_stop_timeout }}"
        
      - name: "Create backup of Splunk configuration"
        task: splunk_backup
        args:
          backup_dir: "{{ splunk_backup_dir }}"
          backup_name: "pre_upgrade_{{ target_version }}_{{ ansible_date_time.epoch }}"
          include_configs: true
          include_apps: true
          include_users: true
          include_indexes: false
          compression: "{{ backup_compression }}"
        timeout: 600
        
      - name: "Verify backup integrity"
        task: splunk_verify_backup
        args:
          backup_path: "{{ splunk_backup_dir }}/pre_upgrade_{{ target_version }}_{{ ansible_date_time.epoch }}.tar.gz"
        timeout: 120

  # Upgrade phase
  - name: "Install new version"
    phase: upgrade
    tasks:
      - name: "Install Splunk Universal Forwarder package"
        task: splunk_install
        args:
          package_path: "{{ package_cache_dir }}/splunkforwarder-{{ target_version }}-{{ os_family }}-{{ os_version }}-{{ cpu_arch }}.rpm"
          install_method: "upgrade"
          preserve_configs: true
          preserve_apps: true
          preserve_users: true
        retries: 2
        retry_delay: 30
        timeout: 900
        
      - name: "Restore Splunk configuration"
        task: splunk_restore_config
        args:
          backup_path: "{{ splunk_backup_dir }}/pre_upgrade_{{ target_version }}_{{ ansible_date_time.epoch }}.tar.gz"
          restore_configs: true
          restore_apps: true
          restore_users: true
        timeout: 300
        
      - name: "Set Splunk ownership and permissions"
        task: splunk_set_permissions
        args:
          splunk_home: "{{ splunk_home }}"
          splunk_user: "{{ splunk_user }}"
          splunk_group: "{{ splunk_group }}"
          recursive: true
        timeout: 180

  # Post-upgrade phase
  - name: "Post-upgrade configuration and validation"
    phase: post_upgrade
    tasks:
      - name: "Start Splunk service"
        task: service
        args:
          name: "SplunkForwarder"
          state: started
          enabled: true
        timeout: "{{ service_start_timeout }}"
        
      - name: "Wait for Splunk to be ready"
        task: splunk_wait_ready
        args:
          splunk_home: "{{ splunk_home }}"
          mgmt_port: "{{ splunk_mgmt_port }}"
          timeout: "{{ health_check_timeout }}"
          retries: "{{ health_check_retries }}"
          interval: "{{ health_check_interval }}"
        timeout: "{{ health_check_timeout }}"
        
      - name: "Verify Splunk version"
        task: splunk_version_check
        args:
          expected_version: "{{ target_version }}"
          splunk_home: "{{ splunk_home }}"
        timeout: 60
        
      - name: "Run Splunk health checks"
        task: splunk_health_check
        args:
          check_splunkd: true
          check_web: false
          check_forwarder: true
          check_license: true
          check_connectivity: true
          check_logs: true
        timeout: 300
        
      - name: "Create post-upgrade checkpoint"
        task: checkpoint
        args:
          checkpoint_name: "post_upgrade_{{ target_version }}"
          checkpoint_data:
            target_version: "{{ target_version }}"
            timestamp: "{{ ansible_date_time.iso8601 }}"
            host: "{{ inventory_hostname }}"
            status: "success"
        timeout: 30

# Handlers
handlers:
  - name: "Rollback on failure"
    when: "{{ rollback_enabled and task_result.failed }}"
    tasks:
      - name: "Stop Splunk service"
        task: service
        args:
          name: "SplunkForwarder"
          state: stopped
        timeout: 60
        
      - name: "Restore from backup"
        task: splunk_restore
        args:
          backup_path: "{{ splunk_backup_dir }}/pre_upgrade_{{ target_version }}_{{ ansible_date_time.epoch }}.tar.gz"
          restore_configs: true
          restore_apps: true
          restore_users: true
        timeout: 600
        
      - name: "Start Splunk service"
        task: service
        args:
          name: "SplunkForwarder"
          state: started
        timeout: 120
        
      - name: "Verify rollback success"
        task: splunk_health_check
        args:
          check_splunkd: true
          check_forwarder: true
        timeout: 180

  - name: "Cleanup on success"
    when: "{{ task_result.success }}"
    tasks:
      - name: "Clean up package cache"
        task: file
        args:
          path: "{{ package_cache_dir }}/splunkforwarder-{{ target_version }}-{{ os_family }}-{{ os_version }}-{{ cpu_arch }}.rpm"
          state: absent
        timeout: 30
        
      - name: "Clean up old backups"
        task: splunk_cleanup_backups
        args:
          backup_dir: "{{ splunk_backup_dir }}"
          retention_days: "{{ backup_retention_days }}"
        timeout: 300
"""
            playbook_file.write_text(playbook_content)
        
        # Create README
        readme_file = project_dir / 'README.md'
        if not readme_file.exists():
            readme_content = f"""# {project_name}

Siemply project for Splunk infrastructure orchestration.

## Quick Start

1. **Configure inventory**: Edit `{config_dir}/inventory.yml` with your hosts
2. **Configure SSH**: Edit `{config_dir}/ssh_profiles.yml` with your SSH settings
3. **Run a playbook**: `siemply run -p plays/upgrade-uf.yml -g prod-web`

## Project Structure

```
{project_name}/
├── {config_dir}/           # Configuration files
│   ├── inventory.yml       # Host inventory
│   └── ssh_profiles.yml    # SSH connection profiles
├── plays/                  # Playbooks
│   └── upgrade-uf.yml      # UF upgrade playbook
├── scripts/                # Custom scripts
├── reports/                # Run reports
└── logs/                   # Log files
```

## Commands

- `siemply hosts list` - List all hosts
- `siemply run -p plays/upgrade-uf.yml -g prod-web` - Run playbook
- `siemply check splunk --hostgroup all` - Health check
- `siemply audit report` - View audit report

For more information, see the [Siemply documentation](https://docs.siemply.dev).
"""
            readme_file.write_text(readme_content)
        
        click.echo(f"✅ Project '{project_name}' initialized successfully!")
        click.echo(f"📁 Project directory: {project_dir.absolute()}")
        click.echo(f"📋 Configuration: {config_path.absolute()}")
        click.echo(f"📖 Playbooks: {project_dir / 'plays'}")
        click.echo(f"🔧 Scripts: {project_dir / 'scripts'}")
        click.echo("")
        click.echo("Next steps:")
        click.echo(f"1. Edit {config_dir}/inventory.yml with your hosts")
        click.echo(f"2. Edit {config_dir}/ssh_profiles.yml with your SSH settings")
        click.echo("3. Run: siemply hosts list")
        click.echo("4. Run: siemply run -p plays/upgrade-uf.yml -g prod-web --dry-run")
        
    except Exception as e:
        click.echo(f"❌ Failed to initialize project: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
