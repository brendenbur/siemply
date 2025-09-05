#!/usr/bin/env python3
"""
Siemply PoC - Splunk Infrastructure Orchestration Framework
Demonstrates: inventory load → prechecks → rolling UF upgrade → postchecks → Markdown report
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from siemply.core.orchestrator import Orchestrator, RunConfig
from siemply.core.inventory import Inventory
from siemply.core.ssh_executor import SSHExecutor
from siemply.core.secrets import SecretsManager
from siemply.core.audit import AuditLogger


class SiemplyPoC:
    """Siemply Proof of Concept"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.orchestrator = Orchestrator(config_dir)
        self.inventory = Inventory(config_dir)
        self.secrets = SecretsManager(config_dir)
        self.ssh_executor = SSHExecutor(self.secrets)
        self.audit = AuditLogger(config_dir)
        
        # Results storage
        self.results = {
            'start_time': None,
            'end_time': None,
            'duration': 0,
            'phases': {},
            'hosts': {},
            'errors': [],
            'warnings': []
        }
    
    async def initialize(self):
        """Initialize Siemply components"""
        try:
            await self.orchestrator.initialize()
            self.logger.info("Siemply PoC initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Siemply PoC: {e}")
            raise
    
    async def run_demo(self, target_group: str = "prod-web", target_version: str = "9.2.2"):
        """Run the complete demo workflow"""
        self.results['start_time'] = datetime.now()
        
        try:
            self.logger.info("🚀 Starting Siemply PoC Demo")
            self.logger.info(f"Target Group: {target_group}")
            self.logger.info(f"Target Version: {target_version}")
            
            # Phase 1: Load and validate inventory
            await self._phase_inventory_load(target_group)
            
            # Phase 2: Pre-upgrade checks
            await self._phase_prechecks(target_group)
            
            # Phase 3: Rolling UF upgrade simulation
            await self._phase_rolling_upgrade(target_group, target_version)
            
            # Phase 4: Post-upgrade validation
            await self._phase_postchecks(target_group)
            
            # Phase 5: Generate report
            await self._phase_generate_report()
            
            self.results['end_time'] = datetime.now()
            self.results['duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()
            
            self.logger.info("✅ Siemply PoC Demo completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Siemply PoC Demo failed: {e}")
            self.results['errors'].append(str(e))
            raise
    
    async def _phase_inventory_load(self, target_group: str):
        """Phase 1: Load and validate inventory"""
        phase_name = "inventory_load"
        self.logger.info(f"📋 Phase 1: Loading inventory for group '{target_group}'")
        
        try:
            # Load inventory
            await self.inventory.load()
            
            # Get target hosts
            hosts = self.inventory.get_group_hosts(target_group)
            if not hosts:
                raise ValueError(f"No hosts found in group '{target_group}'")
            
            self.results['phases'][phase_name] = {
                'status': 'success',
                'hosts_found': len(hosts),
                'hosts': [h.name for h in hosts]
            }
            
            self.logger.info(f"✅ Found {len(hosts)} hosts in group '{target_group}'")
            
            # Store hosts for later phases
            self.results['hosts'] = {h.name: {
                'ansible_host': h.ansible_host,
                'splunk_type': h.splunk_type,
                'splunk_version': h.splunk_version,
                'os_family': h.os_family,
                'status': 'pending'
            } for h in hosts}
            
        except Exception as e:
            self.logger.error(f"❌ Phase 1 failed: {e}")
            self.results['phases'][phase_name] = {'status': 'failed', 'error': str(e)}
            raise
    
    async def _phase_prechecks(self, target_group: str):
        """Phase 2: Pre-upgrade system checks"""
        phase_name = "prechecks"
        self.logger.info(f"🔍 Phase 2: Running pre-upgrade checks")
        
        try:
            hosts = self.inventory.get_group_hosts(target_group)
            precheck_results = {}
            
            for host in hosts:
                self.logger.info(f"  Checking {host.name} ({host.ansible_host})...")
                
                # Simulate prechecks (in real implementation, these would be actual checks)
                host_checks = {
                    'disk_space': self._simulate_check('disk_space', host),
                    'memory': self._simulate_check('memory', host),
                    'ulimits': self._simulate_check('ulimits', host),
                    'selinux': self._simulate_check('selinux', host),
                    'ports': self._simulate_check('ports', host),
                    'python': self._simulate_check('python', host)
                }
                
                # Determine overall status
                all_passed = all(check['status'] == 'PASS' for check in host_checks.values())
                host_status = 'PASS' if all_passed else 'FAIL'
                
                precheck_results[host.name] = {
                    'status': host_status,
                    'checks': host_checks
                }
                
                self.results['hosts'][host.name]['precheck_status'] = host_status
                
                if host_status == 'PASS':
                    self.logger.info(f"    ✅ {host.name} - All prechecks passed")
                else:
                    self.logger.warning(f"    ⚠️ {host.name} - Some prechecks failed")
            
            self.results['phases'][phase_name] = {
                'status': 'success',
                'results': precheck_results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Phase 2 failed: {e}")
            self.results['phases'][phase_name] = {'status': 'failed', 'error': str(e)}
            raise
    
    async def _phase_rolling_upgrade(self, target_group: str, target_version: str):
        """Phase 3: Rolling UF upgrade simulation"""
        phase_name = "rolling_upgrade"
        self.logger.info(f"🔄 Phase 3: Rolling UF upgrade to version {target_version}")
        
        try:
            hosts = self.inventory.get_group_hosts(target_group)
            batch_size = 2  # Simulate small batches
            batch_delay = 5  # 5 seconds between batches
            
            upgrade_results = {}
            
            # Process hosts in batches
            for i in range(0, len(hosts), batch_size):
                batch = hosts[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                self.logger.info(f"  Processing batch {batch_num}: {len(batch)} hosts")
                
                # Process batch
                for host in batch:
                    self.logger.info(f"    Upgrading {host.name} ({host.ansible_host})...")
                    
                    # Simulate upgrade steps
                    upgrade_steps = [
                        ('stop_service', 'Stopping Splunk service'),
                        ('backup_config', 'Backing up configuration'),
                        ('download_package', f'Downloading UF {target_version}'),
                        ('install_package', 'Installing new version'),
                        ('restore_config', 'Restoring configuration'),
                        ('start_service', 'Starting Splunk service'),
                        ('verify_version', 'Verifying version')
                    ]
                    
                    host_upgrade = {
                        'status': 'success',
                        'steps': {},
                        'start_time': datetime.now().isoformat(),
                        'end_time': None,
                        'duration': 0
                    }
                    
                    step_start = time.time()
                    
                    for step_name, step_desc in upgrade_steps:
                        self.logger.info(f"      {step_desc}...")
                        
                        # Simulate step execution
                        step_result = self._simulate_upgrade_step(step_name, host, target_version)
                        
                        host_upgrade['steps'][step_name] = {
                            'description': step_desc,
                            'status': step_result['status'],
                            'duration': step_result['duration'],
                            'output': step_result['output']
                        }
                        
                        if step_result['status'] == 'failed':
                            host_upgrade['status'] = 'failed'
                            host_upgrade['error'] = step_result['error']
                            break
                        
                        # Simulate step duration
                        await asyncio.sleep(0.5)
                    
                    step_end = time.time()
                    host_upgrade['end_time'] = datetime.now().isoformat()
                    host_upgrade['duration'] = step_end - step_start
                    
                    upgrade_results[host.name] = host_upgrade
                    self.results['hosts'][host.name]['upgrade_status'] = host_upgrade['status']
                    
                    if host_upgrade['status'] == 'success':
                        self.logger.info(f"    ✅ {host.name} - Upgrade completed successfully")
                    else:
                        self.logger.error(f"    ❌ {host.name} - Upgrade failed: {host_upgrade.get('error', 'Unknown error')}")
                
                # Wait between batches (except for last batch)
                if i + batch_size < len(hosts):
                    self.logger.info(f"  Waiting {batch_delay} seconds before next batch...")
                    await asyncio.sleep(batch_delay)
            
            self.results['phases'][phase_name] = {
                'status': 'success',
                'results': upgrade_results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Phase 3 failed: {e}")
            self.results['phases'][phase_name] = {'status': 'failed', 'error': str(e)}
            raise
    
    async def _phase_postchecks(self, target_group: str):
        """Phase 4: Post-upgrade validation"""
        phase_name = "postchecks"
        self.logger.info(f"✅ Phase 4: Running post-upgrade validation")
        
        try:
            hosts = self.inventory.get_group_hosts(target_group)
            postcheck_results = {}
            
            for host in hosts:
                self.logger.info(f"  Validating {host.name} ({host.ansible_host})...")
                
                # Simulate postchecks
                host_checks = {
                    'service_status': self._simulate_check('service_status', host),
                    'version_check': self._simulate_check('version_check', host),
                    'port_check': self._simulate_check('port_check', host),
                    'health_check': self._simulate_check('health_check', host),
                    'connectivity_check': self._simulate_check('connectivity_check', host)
                }
                
                # Determine overall status
                all_passed = all(check['status'] == 'PASS' for check in host_checks.values())
                host_status = 'PASS' if all_passed else 'FAIL'
                
                postcheck_results[host.name] = {
                    'status': host_status,
                    'checks': host_checks
                }
                
                self.results['hosts'][host.name]['postcheck_status'] = host_status
                self.results['hosts'][host.name]['status'] = 'completed' if host_status == 'PASS' else 'failed'
                
                if host_status == 'PASS':
                    self.logger.info(f"    ✅ {host.name} - All postchecks passed")
                else:
                    self.logger.warning(f"    ⚠️ {host.name} - Some postchecks failed")
            
            self.results['phases'][phase_name] = {
                'status': 'success',
                'results': postcheck_results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Phase 4 failed: {e}")
            self.results['phases'][phase_name] = {'status': 'failed', 'error': str(e)}
            raise
    
    async def _phase_generate_report(self):
        """Phase 5: Generate Markdown report"""
        phase_name = "generate_report"
        self.logger.info(f"📊 Phase 5: Generating Markdown report")
        
        try:
            # Create reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Generate report
            report_content = self._generate_markdown_report()
            
            # Save report
            report_file = reports_dir / f"siemply_poc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.write_text(report_content)
            
            self.results['phases'][phase_name] = {
                'status': 'success',
                'report_file': str(report_file)
            }
            
            self.logger.info(f"✅ Report generated: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Phase 5 failed: {e}")
            self.results['phases'][phase_name] = {'status': 'failed', 'error': str(e)}
            raise
    
    def _simulate_check(self, check_type: str, host) -> Dict[str, Any]:
        """Simulate a health check"""
        # Simulate different check results based on check type
        if check_type in ['disk_space', 'memory', 'ulimits', 'python']:
            return {'status': 'PASS', 'output': f'{check_type} check passed'}
        elif check_type == 'selinux':
            return {'status': 'WARN', 'output': 'SELinux in permissive mode'}
        elif check_type == 'ports':
            return {'status': 'PASS', 'output': 'Required ports are available'}
        elif check_type in ['service_status', 'version_check', 'port_check', 'health_check', 'connectivity_check']:
            return {'status': 'PASS', 'output': f'{check_type} check passed'}
        else:
            return {'status': 'PASS', 'output': f'{check_type} check completed'}
    
    def _simulate_upgrade_step(self, step_name: str, host, target_version: str) -> Dict[str, Any]:
        """Simulate an upgrade step"""
        # Simulate different step results
        if step_name == 'stop_service':
            return {'status': 'success', 'duration': 2.5, 'output': 'Splunk service stopped successfully'}
        elif step_name == 'backup_config':
            return {'status': 'success', 'duration': 5.0, 'output': 'Configuration backed up successfully'}
        elif step_name == 'download_package':
            return {'status': 'success', 'duration': 15.0, 'output': f'Package downloaded: splunkforwarder-{target_version}.rpm'}
        elif step_name == 'install_package':
            return {'status': 'success', 'duration': 8.0, 'output': 'Package installed successfully'}
        elif step_name == 'restore_config':
            return {'status': 'success', 'duration': 3.0, 'output': 'Configuration restored successfully'}
        elif step_name == 'start_service':
            return {'status': 'success', 'duration': 4.0, 'output': 'Splunk service started successfully'}
        elif step_name == 'verify_version':
            return {'status': 'success', 'duration': 1.0, 'output': f'Version verified: {target_version}'}
        else:
            return {'status': 'success', 'duration': 1.0, 'output': f'{step_name} completed successfully'}
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown report"""
        report = f"""# Siemply PoC Demo Report

**Generated:** {datetime.now().isoformat()}  
**Duration:** {self.results['duration']:.2f} seconds  
**Status:** {'SUCCESS' if not self.results['errors'] else 'FAILED'}

## Summary

- **Total Phases:** {len(self.results['phases'])}
- **Total Hosts:** {len(self.results['hosts'])}
- **Successful Hosts:** {sum(1 for h in self.results['hosts'].values() if h.get('status') == 'completed')}
- **Failed Hosts:** {sum(1 for h in self.results['hosts'].values() if h.get('status') == 'failed')}

## Phase Results

"""
        
        for phase_name, phase_data in self.results['phases'].items():
            status_emoji = "✅" if phase_data['status'] == 'success' else "❌"
            report += f"### {status_emoji} {phase_name.replace('_', ' ').title()}\n\n"
            report += f"**Status:** {phase_data['status'].upper()}\n"
            
            if 'error' in phase_data:
                report += f"**Error:** {phase_data['error']}\n"
            
            if 'hosts_found' in phase_data:
                report += f"**Hosts Found:** {phase_data['hosts_found']}\n"
            
            report += "\n"
        
        report += "## Host Results\n\n"
        
        for host_name, host_data in self.results['hosts'].items():
            status_emoji = "✅" if host_data.get('status') == 'completed' else "❌" if host_data.get('status') == 'failed' else "⏳"
            report += f"### {status_emoji} {host_name}\n\n"
            report += f"**Host:** {host_data['ansible_host']}\n"
            report += f"**Splunk Type:** {host_data['splunk_type']}\n"
            report += f"**Splunk Version:** {host_data['splunk_version']}\n"
            report += f"**OS Family:** {host_data['os_family']}\n"
            report += f"**Status:** {host_data.get('status', 'unknown')}\n"
            
            if 'precheck_status' in host_data:
                report += f"**Precheck Status:** {host_data['precheck_status']}\n"
            
            if 'upgrade_status' in host_data:
                report += f"**Upgrade Status:** {host_data['upgrade_status']}\n"
            
            if 'postcheck_status' in host_data:
                report += f"**Postcheck Status:** {host_data['postcheck_status']}\n"
            
            report += "\n"
        
        if self.results['errors']:
            report += "## Errors\n\n"
            for error in self.results['errors']:
                report += f"- {error}\n"
            report += "\n"
        
        if self.results['warnings']:
            report += "## Warnings\n\n"
            for warning in self.results['warnings']:
                report += f"- {warning}\n"
            report += "\n"
        
        report += "## Next Steps\n\n"
        report += "1. Review the results above\n"
        report += "2. Check individual host statuses\n"
        report += "3. Address any failed checks or upgrades\n"
        report += "4. Run additional validation if needed\n"
        
        return report


async def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Siemply PoC Demo')
    parser.add_argument('--group', '-g', default='prod-web', help='Target group')
    parser.add_argument('--version', '-v', default='9.2.2', help='Target version')
    parser.add_argument('--config-dir', '-c', default='config', help='Config directory')
    
    args = parser.parse_args()
    
    # Create and run PoC
    poc = SiemplyPoC(args.config_dir)
    
    try:
        await poc.initialize()
        await poc.run_demo(args.group, args.version)
        print("\n🎉 Siemply PoC Demo completed successfully!")
        print(f"📊 Check the reports/ directory for detailed results")
    except Exception as e:
        print(f"\n💥 Siemply PoC Demo failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
