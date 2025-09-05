# Siemply CLI Examples

This document provides comprehensive examples of using the Siemply CLI for various Splunk operations.

## Host Management

### List Hosts
```bash
# List all hosts
siemply hosts list

# List hosts in specific group
siemply hosts list --group prod-web

# List hosts by Splunk type
siemply hosts list --splunk-type uf

# List hosts by OS family
siemply hosts list --os-family RedHat

# Output in different formats
siemply hosts list --format json
siemply hosts list --format yaml
```

### Add Hosts
```bash
# Add a Universal Forwarder host
siemply hosts add \
  --name web-03 \
  --ip 192.168.1.13 \
  --user splunk \
  --key-file ~/.ssh/splunk_prod \
  --group prod-web \
  --splunk-type uf \
  --splunk-version 9.1.2 \
  --os-family RedHat \
  --os-version "8" \
  --cpu-arch x86_64 \
  --memory-gb 8 \
  --disk-gb 100

# Add an Enterprise host
siemply hosts add \
  --name search-03 \
  --ip 192.168.1.23 \
  --user splunk \
  --key-file ~/.ssh/splunk_prod \
  --group prod-search \
  --splunk-type enterprise \
  --splunk-version 9.1.2 \
  --os-family RedHat \
  --os-version "8" \
  --cpu-arch x86_64 \
  --memory-gb 32 \
  --disk-gb 500
```

### Test Connectivity
```bash
# Test all hosts
siemply hosts test --all

# Test specific host
siemply hosts test --name web-01

# Test group
siemply hosts test --group prod-web

# Test with custom inventory
siemply hosts test --all --inventory config/production.yml
```

## Running Playbooks

### Universal Forwarder Upgrades
```bash
# Dry run UF upgrade
siemply run -p plays/upgrade-uf.yml -g prod-web --dry-run

# Upgrade UF to specific version
siemply run -p plays/upgrade-uf.yml -g prod-web --version 9.2.2

# Upgrade with custom variables
siemply run -p plays/upgrade-uf.yml -g prod-web \
  --extra-vars '{"target_version": "9.2.2", "backup_enabled": true}'

# Upgrade with limits and concurrency
siemply run -p plays/upgrade-uf.yml -g prod-web \
  --limit 10 --forks 5 --batch-size 3 --batch-delay 300

# Upgrade specific hosts
siemply run -p plays/upgrade-uf.yml -h web-01 -h web-02

# Upgrade with tags
siemply run -p plays/upgrade-uf.yml -g prod-web --tags "precheck,backup"
```

### Enterprise Upgrades
```bash
# Upgrade Enterprise with rolling strategy
siemply run -p plays/upgrade-enterprise.yml -g prod-search \
  --version 9.2.2 --batch-size 2 --batch-delay 600

# Upgrade with canary deployment
siemply run -p plays/upgrade-enterprise.yml -g prod-search \
  --extra-vars '{"canary_enabled": true, "canary_percentage": 10}'

# Upgrade indexers last
siemply run -p plays/upgrade-enterprise.yml -g prod-indexer \
  --extra-vars '{"rolling_strategy": "indexers_last"}'
```

### Health Checks
```bash
# Run health check playbook
siemply run -p plays/health-check.yml -g prod-web

# Health check with custom settings
siemply run -p plays/health-check.yml -g prod-web \
  --extra-vars '{"check_splunk_cluster": true, "check_splunk_indexes": true}'
```

## Health Checks

### Splunk Health Checks
```bash
# Check all hosts
siemply check splunk --hostgroup all

# Check specific group
siemply check splunk --group prod-web

# Check specific hosts
siemply check splunk -h web-01 -h web-02

# Generate health report
siemply check splunk --hostgroup prod-web --report md --output health_report.md

# Generate HTML report
siemply check splunk --hostgroup all --report html --output health_report.html

# Generate JSON report
siemply check splunk --hostgroup prod-web --report json --output health_report.json
```

## Script Execution

### Run Custom Scripts
```bash
# Run script on group
siemply script run --file scripts/rotate-keys.py --group prod-web

# Run script on specific hosts
siemply script run --file scripts/backup-config.py -h web-01 -h web-02

# Run script with arguments
siemply script run --file scripts/rotate-keys.py --group prod-web \
  --args "--key-type ed25519 --retention-days 30"

# Run script with timeout
siemply script run --file scripts/long-running-script.py --group prod-web \
  --timeout 1800
```

### Example Scripts
```bash
# Rotate SSH keys
siemply script run --file scripts/rotate-keys.py --group prod-web \
  --args "--key-type rsa --key-size 4096 --restart-ssh --test-connectivity"

# Backup Splunk configuration
siemply script run --file scripts/backup-config.py --group prod-web \
  --args "--backup-dir /opt/splunk_backups --retention-days 30"

# Update Splunk configuration
siemply script run --file scripts/update-config.py --group prod-web \
  --args "--config-file inputs.conf --template inputs.conf.j2"
```

## Audit and Monitoring

### View Audit Events
```bash
# View recent events
siemply audit events --limit 50

# View events for specific time range
siemply audit events --start-time "2024-01-01T00:00:00" --end-time "2024-01-31T23:59:59"

# View events by user
siemply audit events --user admin

# View events by host
siemply audit events --host web-01

# View events by run ID
siemply audit events --run-id abc123def

# View events in JSON format
siemply audit events --format json --limit 100
```

### Generate Reports
```bash
# Generate audit report
siemply audit report --format markdown --output audit_report.md

# Generate HTML report
siemply audit report --format html --output audit_report.html

# Generate report for specific time range
siemply audit report --start-time "2024-01-01T00:00:00" \
  --end-time "2024-01-31T23:59:59" --format markdown

# Generate report for specific user
siemply audit report --user admin --format json
```

## Configuration Management

### Validate Configuration
```bash
# Validate inventory
siemply config validate

# Validate with custom inventory
siemply config validate --inventory config/production.yml
```

### Show Configuration
```bash
# Show configuration summary
siemply config show

# Show configuration for specific inventory
siemply config show --inventory config/staging.yml
```

## Advanced Usage

### Custom Playbooks
```bash
# Run custom playbook
siemply run -p custom/backup-and-upgrade.yml -g prod-web

# Run playbook with multiple groups
siemply run -p plays/upgrade-uf.yml -g prod-web -g stage-web

# Run playbook with tags and skip tags
siemply run -p plays/upgrade-uf.yml -g prod-web \
  --tags "precheck,backup,upgrade" --skip-tags "postcheck"

# Run playbook with custom timeout
siemply run -p plays/upgrade-enterprise.yml -g prod-search --timeout 7200
```

### Parallel Execution
```bash
# Run with high concurrency
siemply run -p plays/health-check.yml -g prod-web --forks 20

# Run with specific batch settings
siemply run -p plays/upgrade-uf.yml -g prod-web \
  --batch-size 5 --batch-delay 180 --soak-time 300
```

### Dry Run and Planning
```bash
# Dry run to see what would be done
siemply run -p plays/upgrade-uf.yml -g prod-web --dry-run

# Run with verbose output
siemply run -p plays/upgrade-uf.yml -g prod-web --verbose

# Run with debug output
siemply run -p plays/upgrade-uf.yml -g prod-web --debug
```

## Environment-Specific Examples

### Development Environment
```bash
# Quick health check
siemply check splunk --hostgroup dev --report md

# Test new playbook
siemply run -p plays/test-new-feature.yml -g dev --dry-run

# Run script on dev hosts
siemply script run --file scripts/test-script.py --group dev
```

### Staging Environment
```bash
# Full upgrade test
siemply run -p plays/upgrade-uf.yml -g stage --version 9.2.2

# Health check with detailed report
siemply check splunk --hostgroup stage --report html --output staging_health.html

# Test connectivity
siemply hosts test --group stage
```

### Production Environment
```bash
# Rolling UF upgrade with careful batching
siemply run -p plays/upgrade-uf.yml -g prod-web \
  --version 9.2.2 --batch-size 3 --batch-delay 600 --soak-time 1200

# Enterprise upgrade with canary
siemply run -p plays/upgrade-enterprise.yml -g prod-search \
  --version 9.2.2 --extra-vars '{"canary_enabled": true, "canary_percentage": 5}'

# Comprehensive health check
siemply check splunk --hostgroup prod --report html --output production_health.html

# Audit report for compliance
siemply audit report --format html --output compliance_report.html
```

## Troubleshooting Commands

### Debug Connectivity Issues
```bash
# Test SSH connectivity
siemply hosts test --all --verbose

# Test specific host with debug
siemply hosts test --name web-01 --debug

# Check inventory validation
siemply config validate --verbose
```

### Debug Playbook Issues
```bash
# Run with debug output
siemply run -p plays/upgrade-uf.yml -g prod-web --debug

# Run with verbose output
siemply run -p plays/upgrade-uf.yml -g prod-web --verbose

# Check recent events
siemply audit events --limit 20 --format json
```

### Monitor Long-Running Operations
```bash
# Check run status
siemply audit events --run-id abc123def

# Monitor events in real-time
siemply audit events --limit 10 --format json | jq '.[] | {timestamp, event_type, host, status}'
```

## Integration Examples

### CI/CD Pipeline
```bash
#!/bin/bash
# Example CI/CD script

# Validate configuration
siemply config validate || exit 1

# Test connectivity
siemply hosts test --group staging || exit 1

# Run health check
siemply check splunk --hostgroup staging --report json --output staging_health.json

# Run upgrade if health check passes
if jq '.summary.healthy_hosts == .summary.total_hosts' staging_health.json; then
    siemply run -p plays/upgrade-uf.yml -g staging --version 9.2.2
else
    echo "Health check failed, skipping upgrade"
    exit 1
fi
```

### Monitoring Integration
```bash
#!/bin/bash
# Example monitoring script

# Generate health report
siemply check splunk --hostgroup all --report json --output /tmp/health.json

# Check for failures
if jq '.summary.unhealthy_hosts > 0' /tmp/health.json; then
    # Send alert
    curl -X POST "https://hooks.slack.com/services/..." \
      -H "Content-Type: application/json" \
      -d '{"text": "Splunk health check failed"}'
fi
```

### Backup and Recovery
```bash
#!/bin/bash
# Example backup script

# Backup Splunk configuration
siemply script run --file scripts/backup-config.py --group prod-web \
  --args "--backup-dir /opt/splunk_backups --retention-days 30"

# Verify backup
siemply script run --file scripts/verify-backup.py --group prod-web \
  --args "--backup-dir /opt/splunk_backups"
```
