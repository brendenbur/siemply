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
# Siemply - Splunk Infrastructure Orchestration Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/siemply/siemply)

A lightweight, opinionated orchestration framework for managing Splunk Universal Forwarder and Splunk Enterprise deployments across Linux hosts.

## 🚀 Quick Start

### CLI Interface
```bash
# Install Siemply
pip install -e .

# Initialize a project
siemply init my-splunk-project
cd my-splunk-project

# Run the demo
python3 siemply_demo.py --group prod-web --version 9.2.2
```

### Web Interface
```bash
# Install dependencies
pip install -e .
cd web && npm install && cd ..

# Build and start web interface
./start_web.sh

# Access at http://localhost:8000
```

## ✨ Features

- **Dual Interface**: Powerful CLI + Modern Web GUI
- **Real-time Monitoring**: Live dashboard with WebSocket updates
- **Idempotent Operations**: Safe, repeatable upgrades and configurations
- **Zero-Agent Architecture**: Uses standard SSH for remote execution
- **Splunk-Optimized**: Built-in tasks for UF and Enterprise upgrades
- **Security-First**: SSH key-based auth, secrets management, audit logging
- **Production-Ready**: Health checks, rollback capabilities, rate limiting
- **Extensible**: Plugin system for custom tasks and integrations

## 📋 Installation

### Prerequisites
- Python 3.11 or higher
- Linux/macOS (Windows support coming soon)
- SSH access to target hosts

### Install from Source
```bash
git clone https://github.com/siemply/siemply.git
cd siemply
pip install -e .
```

### Verify Installation
```bash
siemply --version
siemply --help
```

## 🎯 Demo

Run the included demo to see Siemply in action:

```bash
# Run the demo
python3 siemply_demo.py --group prod-web --version 9.2.2

# Check the generated report
cat reports/siemply_demo_report_*.md
```

## 📚 Documentation

- [Getting Started](docs/getting-started.md) - Installation and quick start
- [Web GUI Guide](WEB_GUI_GUIDE.md) - Complete web interface documentation
- [CLI Examples](CLI_EXAMPLES.md) - 50+ command examples
- [Installation Fix](INSTALLATION_FIXED.md) - Installation troubleshooting
- [Security Hardening](docs/security.md) - Security best practices
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## 🛠️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Siemply CLI   │────│  Orchestrator    │────│  Inventory DB   │
│   (siemply)     │    │   Service/API    │    │  (SQLite/PG)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Task Runner    │    │   SSH Executor   │    │  Secrets Store  │
│  (Idempotent)   │    │  (asyncssh)      │    │  (Vault/Env)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Splunk Tasks   │    │  Remote Hosts    │
│  (UF/Enterprise)│    │  (Linux targets) │
└─────────────────┘    └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Audit/Logs     │
│  (JSON/Reports) │
└─────────────────┘
```

## 🔧 Core Components

- **CLI Interface**: Command-line tool with comprehensive commands
- **Orchestrator Service**: Core coordination and API layer  
- **Task Runner**: Idempotent task execution engine
- **SSH Executor**: Secure remote execution via asyncssh
- **Inventory Store**: Host/group management with SQLite
- **Secrets Backend**: Pluggable secrets management (Vault, env, file)
- **Audit System**: Immutable logging and reporting

## 📖 Example Commands

```bash
# Host management
siemply hosts list
siemply hosts add --name web-01 --ip 192.168.1.10 --group prod-web
siemply hosts test --group prod-web

# Playbook execution
siemply run -p plays/upgrade-uf.yml -g prod-web --version 9.2.2 --dry-run
siemply run -p plays/upgrade-enterprise.yml -g prod-search --batch-size 2

# Health checks
siemply check splunk --hostgroup all --report md
siemply check splunk --group prod-web --report html --output health.html

# Script execution
siemply script run --file scripts/rotate-keys.py --group prod-web
siemply script run --file scripts/backup-config.py --host web-01

# Audit and monitoring
siemply audit events --limit 50 --format json
siemply audit report --format markdown --output audit_report.md
```

## 🔒 Security Features

- **SSH Security**: Key-based auth, cipher selection, bastion support
- **Secrets Management**: Vault integration, encrypted file storage
- **Audit Logging**: Immutable logs with comprehensive tracking
- **RBAC**: Role-based access control
- **Safe Defaults**: Dry-run enabled by default

## ⚡ Performance & Reliability

- **Concurrency Control**: Configurable forks and rate limiting
- **Rolling Strategies**: Safe batch processing with soak times
- **Health Gates**: Automatic rollback on failures
- **Connection Pooling**: Efficient SSH connection management
- **Retry Logic**: Exponential backoff and configurable retries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.siemply.dev](https://docs.siemply.dev)
- **Issues**: [GitHub Issues](https://github.com/siemply/siemply/issues)
- **Discussions**: [GitHub Discussions](https://github.com/siemply/siemply/discussions)

## 🏆 Status

**Siemply** is currently in **Beta** and ready for testing and evaluation. The framework provides everything needed to safely and efficiently manage Splunk deployments at scale, with the security and reliability required for regulated environments.

---

**Ready to orchestrate your Splunk infrastructure?** Start with the [Getting Started Guide](docs/getting-started.md) or run the [demo](siemply_demo.py) to see Siemply in action!
