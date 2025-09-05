# Getting Started with Siemply

This guide will help you get up and running with Siemply quickly.

## Installation

### Prerequisites

- Python 3.11 or higher
- Linux/macOS (Windows support coming soon)
- SSH access to target hosts
- Splunk Universal Forwarder or Enterprise installed on target hosts

### Install Siemply

```bash
# Install via pip
pip install siemply

# Or install from source
git clone https://github.com/siemply/siemply.git
cd siemply
pip install -e .
```

### Verify Installation

```bash
siemply --version
siemply --help
```

## Quick Start

### 1. Initialize a Project

```bash
# Create a new Siemply project
siemply init my-splunk-project
cd my-splunk-project
```

This creates a project structure with:
- `config/inventory.yml` - Host inventory
- `config/ssh_profiles.yml` - SSH connection profiles
- `plays/` - Playbooks directory
- `scripts/` - Custom scripts directory
- `reports/` - Run reports directory

### 2. Configure Inventory

Edit `config/inventory.yml` with your hosts:

```yaml
all:
  children:
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
```

### 3. Configure SSH Profiles

Edit `config/ssh_profiles.yml` with your SSH settings:

```yaml
profiles:
  prod:
    user: splunk
    port: 22
    auth_method: key
    private_key_file: ~/.ssh/splunk_prod
    timeout: 30
    connect_timeout: 10
```

### 4. Test Connectivity

```bash
# Test SSH connectivity to all hosts
siemply hosts test --all

# Test specific group
siemply hosts test --group prod-web
```

### 5. Run Your First Playbook

```bash
# Run UF upgrade playbook (dry run)
siemply run -p plays/upgrade-uf.yml -g prod-web --dry-run

# Run for real
siemply run -p plays/upgrade-uf.yml -g prod-web --version 9.2.2
```

## Basic Commands

### Host Management

```bash
# List all hosts
siemply hosts list

# Add a host
siemply hosts add --name web-02 --ip 192.168.1.11 --group prod-web

# Test host connectivity
siemply hosts test --name web-01
```

### Running Playbooks

```bash
# Run playbook on specific hosts
siemply run -p plays/upgrade-uf.yml -h web-01 -h web-02

# Run playbook on group
siemply run -p plays/upgrade-uf.yml -g prod-web

# Run with custom variables
siemply run -p plays/upgrade-uf.yml -g prod-web --extra-vars '{"target_version": "9.2.2"}'

# Run with limits and concurrency
siemply run -p plays/upgrade-uf.yml -g prod-web --limit 5 --forks 3
```

### Health Checks

```bash
# Check Splunk health on all hosts
siemply check splunk --hostgroup all

# Generate health report
siemply check splunk --hostgroup prod-web --report md --output health_report.md
```

### Running Scripts

```bash
# Run custom script on hosts
siemply script run --file scripts/rotate-keys.py --group prod-web

# Run script with arguments
siemply script run --file scripts/backup-config.py --group prod-web --args "--retention 30"
```

### Audit and Reports

```bash
# View recent events
siemply audit events --limit 50

# Generate audit report
siemply audit report --format markdown --output audit_report.md

# View run status
siemply audit events --run-id abc123
```

## Configuration

### Inventory Structure

```yaml
all:
  children:
    # Environment groups
    prod:
      children:
        # Service groups
        prod-web:
          hosts:
            # Individual hosts
            web-01:
              ansible_host: 192.168.1.10
              ansible_user: splunk
              ansible_ssh_private_key_file: ~/.ssh/splunk_prod
              splunk_type: uf  # or 'enterprise'
              splunk_version: 9.1.2
              os_family: RedHat  # or 'Ubuntu'
              os_version: "8"
              cpu_arch: x86_64
              memory_gb: 8
              disk_gb: 100
      vars:
        # Group variables
        splunk_home: /opt/splunk
        splunk_user: splunk
        splunk_group: splunk
```

### SSH Profiles

```yaml
profiles:
  prod:
    user: splunk
    port: 22
    auth_method: key
    private_key_file: ~/.ssh/splunk_prod
    timeout: 30
    connect_timeout: 10
    keepalive_interval: 30
    keepalive_count_max: 3
    
    # Security settings
    ciphers:
      - aes256-gcm@openssh.com
      - aes128-gcm@openssh.com
    kex_algorithms:
      - curve25519-sha256
      - curve25519-sha256@libssh.org
    mac_algorithms:
      - hmac-sha2-256
      - hmac-sha2-512
```

## Playbooks

### Basic Playbook Structure

```yaml
name: "My Playbook"
description: "Description of what this playbook does"
version: "1.0.0"

# Execution settings
execution:
  strategy: rolling  # or 'parallel'
  max_failures: 3
  batch_size: 10
  batch_delay: 300
  timeout: 3600

# Variables
vars:
  target_version: "9.2.2"
  backup_enabled: true

# Tasks
tasks:
  - name: "Pre-upgrade checks"
    phase: pre_upgrade
    tasks:
      - name: "Check system requirements"
        task: splunk_precheck
        args:
          check_disk_space: true
          min_disk_space_gb: 10
          check_memory: true
          min_memory_gb: 2
```

### Available Task Types

- `command` - Execute shell commands
- `file` - Manage files and directories
- `package` - Manage packages
- `service` - Manage services
- `template` - Generate files from templates
- `script` - Execute custom scripts
- `splunk_precheck` - Splunk pre-upgrade checks
- `splunk_download` - Download Splunk packages
- `splunk_install` - Install Splunk packages
- `splunk_backup` - Backup Splunk configuration
- `splunk_restore` - Restore Splunk configuration
- `splunk_health_check` - Splunk health checks
- `checkpoint` - Create rollback checkpoints

## Security

### SSH Key Management

```bash
# Generate SSH keys for Splunk user
ssh-keygen -t rsa -b 4096 -f ~/.ssh/splunk_prod -N ""

# Copy public key to target hosts
ssh-copy-id -i ~/.ssh/splunk_prod.pub splunk@192.168.1.10
```

### Secrets Management

Siemply supports multiple secrets backends:

```yaml
# config/secrets.yml
default_backend: env

vault:
  enabled: true
  url: "https://vault.example.com"
  token: "your-vault-token"
  path: "secret/siemply"

file:
  enabled: true
  secrets_file: "config/secrets.json"
  key_file: "config/secrets.key"
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Check SSH key permissions: `chmod 600 ~/.ssh/splunk_prod`
   - Verify SSH connectivity: `ssh -i ~/.ssh/splunk_prod splunk@host`
   - Check SSH profile configuration

2. **Permission Denied**
   - Ensure Splunk user has necessary permissions
   - Check file ownership and permissions
   - Verify sudo access if needed

3. **Package Download Failed**
   - Check network connectivity
   - Verify package URLs in splunk_matrix.yml
   - Check disk space for package cache

4. **Service Won't Start**
   - Check Splunk logs: `tail -f /opt/splunk/var/log/splunk/splunkd.log`
   - Verify configuration files
   - Check port availability

### Debug Mode

```bash
# Enable debug logging
siemply --debug run -p plays/upgrade-uf.yml -g prod-web

# Verbose output
siemply --verbose run -p plays/upgrade-uf.yml -g prod-web
```

### Logs

Siemply logs are stored in:
- `logs/siemply.log` - Main application logs
- `reports/` - Run reports and summaries
- `config/audit.db` - Audit database

## Next Steps

- [Creating Plays](creating-plays.md) - Learn to create custom playbooks
- [Security Hardening](security.md) - Secure your Siemply deployment
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [API Reference](api-reference.md) - Programmatic access to Siemply
