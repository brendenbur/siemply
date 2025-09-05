# Siemply - Splunk Infrastructure Orchestration Framework

A lightweight, opinionated orchestration framework for managing Splunk Universal Forwarder and Splunk Enterprise deployments across Linux hosts.

## Features

- **Idempotent Operations**: Safe, repeatable upgrades and configurations
- **Zero-Agent Architecture**: Uses standard SSH for remote execution
- **Splunk-Optimized**: Built-in tasks for UF and Enterprise upgrades
- **Security-First**: SSH key-based auth, secrets management, audit logging
- **Production-Ready**: Health checks, rollback capabilities, rate limiting
- **Extensible**: Plugin system for custom tasks and integrations

## Quick Start

```bash
# Install
pipx install siemply

# Initialize project
siemply init my-splunk-project
cd my-splunk-project

# Add hosts
siemply hosts add --name web-01 --ip 192.168.1.10 --group prod-web

# Run UF upgrade
siemply run --play upgrade-uf.yml --group prod-web --version 9.2.2 --dry-run
```

## Architecture

- **CLI**: Command-line interface (`siemply`)
- **Orchestrator**: Core service and API layer
- **Task Engine**: Idempotent task execution
- **SSH Executor**: Secure remote execution
- **Inventory**: Host and group management
- **Secrets**: Pluggable secrets backend (Vault, env, file)
- **Audit**: Immutable logging and reporting

## Documentation

- [Getting Started](docs/getting-started.md)
- [Creating Plays](docs/creating-plays.md)
- [Security Hardening](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
# siemply
