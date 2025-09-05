"""
Siemply CLI Commands
"""

import asyncio
import click
import json
import yaml
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys

from ..core.orchestrator import Orchestrator, RunConfig
from ..core.inventory import Inventory
from ..core.audit import AuditLogger


@click.group()
def hosts_command():
    """Manage inventory hosts and groups"""
    pass


@hosts_command.command('list')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.option('--group', '-g', help='Filter by group name')
@click.option('--splunk-type', help='Filter by Splunk type (uf, enterprise)')
@click.option('--os-family', help='Filter by OS family')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'yaml']), 
              default='table', help='Output format')
@click.pass_context
def hosts_list(ctx, inventory, group, splunk_type, os_family, format):
    """List all hosts in inventory"""
    async def _list_hosts():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Get hosts
            if group:
                hosts = inv.get_group_hosts(group)
            else:
                hosts = inv.get_all_hosts()
            
            # Apply filters
            if splunk_type:
                hosts = [h for h in hosts if h.splunk_type == splunk_type]
            if os_family:
                hosts = [h for h in hosts if h.os_family == os_family]
            
            if format == 'json':
                hosts_data = []
                for host in hosts:
                    host_data = {
                        'name': host.name,
                        'ansible_host': host.ansible_host,
                        'ansible_user': host.ansible_user,
                        'splunk_type': host.splunk_type,
                        'splunk_version': host.splunk_version,
                        'os_family': host.os_family,
                        'os_version': host.os_version,
                        'cpu_arch': host.cpu_arch,
                        'memory_gb': host.memory_gb,
                        'disk_gb': host.disk_gb
                    }
                    hosts_data.append(host_data)
                click.echo(json.dumps(hosts_data, indent=2))
            elif format == 'yaml':
                hosts_data = []
                for host in hosts:
                    host_data = {
                        'name': host.name,
                        'ansible_host': host.ansible_host,
                        'ansible_user': host.ansible_user,
                        'splunk_type': host.splunk_type,
                        'splunk_version': host.splunk_version,
                        'os_family': host.os_family,
                        'os_version': host.os_version,
                        'cpu_arch': host.cpu_arch,
                        'memory_gb': host.memory_gb,
                        'disk_gb': host.disk_gb
                    }
                    hosts_data.append(host_data)
                click.echo(yaml.dump(hosts_data, default_flow_style=False))
            else:
                # Table format
                if not hosts:
                    click.echo("No hosts found")
                    return
                
                # Print header
                click.echo(f"{'Name':<15} {'Host':<15} {'User':<10} {'Type':<10} {'Version':<10} {'OS':<10} {'Arch':<8} {'Mem':<6} {'Disk':<6}")
                click.echo("-" * 100)
                
                # Print hosts
                for host in hosts:
                    click.echo(f"{host.name:<15} {host.ansible_host:<15} {host.ansible_user:<10} "
                             f"{host.splunk_type or 'N/A':<10} {host.splunk_version or 'N/A':<10} "
                             f"{host.os_family or 'N/A':<10} {host.cpu_arch or 'N/A':<8} "
                             f"{host.memory_gb or 'N/A':<6} {host.disk_gb or 'N/A':<6}")
                
                click.echo(f"\nTotal: {len(hosts)} hosts")
                
        except Exception as e:
            click.echo(f"❌ Error listing hosts: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_list_hosts())


@hosts_command.command('add')
@click.option('--name', '-n', required=True, help='Host name')
@click.option('--ip', '-i', required=True, help='Host IP address')
@click.option('--user', '-u', default='splunk', help='SSH user')
@click.option('--port', '-p', default=22, help='SSH port')
@click.option('--key-file', '-k', help='SSH private key file')
@click.option('--group', '-g', help='Host group')
@click.option('--splunk-type', type=click.Choice(['uf', 'enterprise']), 
              help='Splunk type')
@click.option('--splunk-version', help='Splunk version')
@click.option('--os-family', help='OS family')
@click.option('--os-version', help='OS version')
@click.option('--cpu-arch', help='CPU architecture')
@click.option('--memory-gb', type=int, help='Memory in GB')
@click.option('--disk-gb', type=int, help='Disk space in GB')
@click.option('--inventory', default='config/inventory.yml',
              help='Inventory file path')
@click.pass_context
def hosts_add(ctx, name, ip, user, port, key_file, group, splunk_type, 
              splunk_version, os_family, os_version, cpu_arch, memory_gb, 
              disk_gb, inventory):
    """Add a host to inventory"""
    async def _add_host():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Create host
            from ..core.inventory import Host
            host = Host(
                name=name,
                ansible_host=ip,
                ansible_user=user,
                ansible_port=port,
                ansible_ssh_private_key_file=key_file,
                splunk_type=splunk_type,
                splunk_version=splunk_version,
                os_family=os_family,
                os_version=os_version,
                cpu_arch=cpu_arch,
                memory_gb=memory_gb,
                disk_gb=disk_gb
            )
            
            # Add host
            if inv.add_host(host):
                click.echo(f"✅ Host '{name}' added successfully")
            else:
                click.echo(f"❌ Failed to add host '{name}'", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"❌ Error adding host: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_add_host())


@hosts_command.command('remove')
@click.option('--name', '-n', required=True, help='Host name')
@click.option('--inventory', default='config/inventory.yml',
              help='Inventory file path')
@click.pass_context
def hosts_remove(ctx, name, inventory):
    """Remove a host from inventory"""
    async def _remove_host():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Remove host
            if inv.remove_host(name):
                click.echo(f"✅ Host '{name}' removed successfully")
            else:
                click.echo(f"❌ Host '{name}' not found", err=True)
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"❌ Error removing host: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_remove_host())


@hosts_command.command('test')
@click.option('--name', '-n', help='Test specific host')
@click.option('--group', '-g', help='Test all hosts in group')
@click.option('--all', 'test_all', is_flag=True, help='Test all hosts')
@click.option('--inventory', default='config/inventory.yml',
              help='Inventory file path')
@click.pass_context
def hosts_test(ctx, name, group, test_all, inventory):
    """Test SSH connectivity to hosts"""
    async def _test_hosts():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Get hosts to test
            if name:
                host = inv.get_host(name)
                if not host:
                    click.echo(f"❌ Host '{name}' not found", err=True)
                    sys.exit(1)
                hosts = [host]
            elif group:
                hosts = inv.get_group_hosts(group)
            elif test_all:
                hosts = inv.get_all_hosts()
            else:
                click.echo("❌ Specify --name, --group, or --all", err=True)
                sys.exit(1)
            
            if not hosts:
                click.echo("No hosts to test")
                return
            
            # Test hosts
            from ..core.ssh_executor import SSHExecutor
            from ..core.secrets import SecretsManager
            
            secrets = SecretsManager(ctx.obj['config_dir'])
            await secrets.load()
            
            ssh_executor = SSHExecutor(secrets)
            
            click.echo(f"Testing {len(hosts)} hosts...")
            click.echo()
            
            success_count = 0
            for host in hosts:
                try:
                    result = await ssh_executor.test_connection(host)
                    if result:
                        click.echo(f"✅ {host.name} ({host.ansible_host}) - OK")
                        success_count += 1
                    else:
                        click.echo(f"❌ {host.name} ({host.ansible_host}) - FAILED")
                except Exception as e:
                    click.echo(f"❌ {host.name} ({host.ansible_host}) - ERROR: {e}")
            
            click.echo()
            click.echo(f"Results: {success_count}/{len(hosts)} hosts successful")
            
        except Exception as e:
            click.echo(f"❌ Error testing hosts: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_test_hosts())


@click.group()
def run_command():
    """Execute playbooks against hosts"""
    pass


@run_command.command('playbook')
@click.option('--playbook', '-p', required=True, help='Playbook file path')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.option('--host', '-h', multiple=True, help='Target hosts')
@click.option('--group', '-g', multiple=True, help='Target groups')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--limit', type=int, help='Limit number of hosts')
@click.option('--forks', type=int, default=10, help='Number of parallel forks')
@click.option('--timeout', type=int, default=3600, help='Run timeout in seconds')
@click.option('--batch-size', type=int, default=10, help='Batch size for rolling updates')
@click.option('--batch-delay', type=int, default=300, help='Delay between batches in seconds')
@click.option('--tags', help='Comma-separated list of tags to run')
@click.option('--skip-tags', help='Comma-separated list of tags to skip')
@click.option('--extra-vars', help='Extra variables in JSON format')
@click.pass_context
def run_playbook(ctx, playbook, inventory, host, group, dry_run, limit, forks,
                 timeout, batch_size, batch_delay, tags, skip_tags, extra_vars):
    """Run a playbook against target hosts"""
    async def _run_playbook():
        try:
            # Initialize orchestrator
            orchestrator = Orchestrator(ctx.obj['config_dir'])
            await orchestrator.initialize()
            
            # Parse extra vars
            extra_vars_dict = {}
            if extra_vars:
                try:
                    extra_vars_dict = json.loads(extra_vars)
                except json.JSONDecodeError as e:
                    click.echo(f"❌ Invalid JSON in extra-vars: {e}", err=True)
                    sys.exit(1)
            
            # Parse tags
            tags_list = tags.split(',') if tags else None
            skip_tags_list = skip_tags.split(',') if skip_tags else None
            
            # Create run config
            config = RunConfig(
                playbook=playbook,
                inventory=inventory,
                target_hosts=list(host),
                target_groups=list(group),
                dry_run=dry_run,
                limit=limit,
                forks=forks,
                timeout=timeout,
                batch_size=batch_size,
                batch_delay=batch_delay,
                tags=tags_list,
                skip_tags=skip_tags_list,
                extra_vars=extra_vars_dict
            )
            
            # Run playbook
            click.echo(f"🚀 Running playbook: {playbook}")
            if dry_run:
                click.echo("🔍 DRY RUN MODE - No changes will be made")
            click.echo()
            
            result = await orchestrator.run_playbook(config)
            
            # Display results
            click.echo()
            click.echo("=" * 60)
            click.echo("RUN SUMMARY")
            click.echo("=" * 60)
            click.echo(f"Run ID: {result.run_id}")
            click.echo(f"Status: {result.status.upper()}")
            click.echo(f"Duration: {result.duration:.2f} seconds")
            click.echo(f"Total Hosts: {result.total_hosts}")
            click.echo(f"Successful: {result.successful_hosts}")
            click.echo(f"Failed: {result.failed_hosts}")
            click.echo(f"Skipped: {result.skipped_hosts}")
            
            if result.errors:
                click.echo()
                click.echo("ERRORS:")
                for error in result.errors:
                    click.echo(f"  - {error}")
            
            if result.warnings:
                click.echo()
                click.echo("WARNINGS:")
                for warning in result.warnings:
                    click.echo(f"  - {warning}")
            
            # Exit with appropriate code
            if result.status == 'failed':
                sys.exit(1)
            elif result.status == 'partial':
                sys.exit(2)
            else:
                sys.exit(0)
                
        except Exception as e:
            click.echo(f"❌ Error running playbook: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_run_playbook())


@click.group()
def script_command():
    """Run custom Python scripts on hosts"""
    pass


@script_command.command('run')
@click.option('--file', '-f', required=True, help='Script file path')
@click.option('--host', '-h', multiple=True, help='Target hosts')
@click.option('--group', '-g', multiple=True, help='Target groups')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.option('--timeout', type=int, default=300, help='Script timeout in seconds')
@click.option('--args', help='Script arguments')
@click.pass_context
def script_run(ctx, file, host, group, inventory, timeout, args):
    """Run a Python script on target hosts"""
    async def _run_script():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Get target hosts
            hosts = []
            if host:
                for host_name in host:
                    h = inv.get_host(host_name)
                    if h:
                        hosts.append(h)
                    else:
                        click.echo(f"❌ Host '{host_name}' not found", err=True)
                        sys.exit(1)
            elif group:
                for group_name in group:
                    hosts.extend(inv.get_group_hosts(group_name))
            else:
                click.echo("❌ Specify --host or --group", err=True)
                sys.exit(1)
            
            if not hosts:
                click.echo("No hosts to run script on")
                return
            
            # Read script
            script_path = Path(file)
            if not script_path.exists():
                click.echo(f"❌ Script file not found: {file}", err=True)
                sys.exit(1)
            
            script_content = script_path.read_text()
            
            # Run script on hosts
            from ..core.ssh_executor import SSHExecutor
            from ..core.secrets import SecretsManager
            
            secrets = SecretsManager(ctx.obj['config_dir'])
            await secrets.load()
            
            ssh_executor = SSHExecutor(secrets)
            
            click.echo(f"🚀 Running script on {len(hosts)} hosts...")
            click.echo()
            
            success_count = 0
            for host in hosts:
                try:
                    click.echo(f"Running on {host.name} ({host.ansible_host})...")
                    
                    # Prepare script with arguments
                    full_script = script_content
                    if args:
                        full_script = f"import sys\nsys.argv = ['{script_path.name}'] + '{args}'.split()\n{script_content}"
                    
                    result = await ssh_executor.execute_script(
                        host, full_script, script_path.name, timeout
                    )
                    
                    if result.exit_code == 0:
                        click.echo(f"✅ {host.name} - SUCCESS")
                        if result.stdout:
                            click.echo(f"Output: {result.stdout}")
                        success_count += 1
                    else:
                        click.echo(f"❌ {host.name} - FAILED (exit code: {result.exit_code})")
                        if result.stderr:
                            click.echo(f"Error: {result.stderr}")
                    
                    click.echo()
                    
                except Exception as e:
                    click.echo(f"❌ {host.name} - ERROR: {e}")
                    click.echo()
            
            click.echo(f"Results: {success_count}/{len(hosts)} hosts successful")
            
        except Exception as e:
            click.echo(f"❌ Error running script: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_run_script())


@click.group()
def check_command():
    """Perform health checks on hosts"""
    pass


@check_command.command('splunk')
@click.option('--host', '-h', multiple=True, help='Target hosts')
@click.option('--group', '-g', multiple=True, help='Target groups')
@click.option('--hostgroup', help='Target hostgroup (alias for --group)')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.option('--report', type=click.Choice(['md', 'html', 'json']), 
              help='Generate report in specified format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def check_splunk(ctx, host, group, hostgroup, inventory, report, output):
    """Check Splunk health on target hosts"""
    async def _check_splunk():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Get target hosts
            hosts = []
            if host:
                for host_name in host:
                    h = inv.get_host(host_name)
                    if h:
                        hosts.append(h)
                    else:
                        click.echo(f"❌ Host '{host_name}' not found", err=True)
                        sys.exit(1)
            elif group or hostgroup:
                target_groups = group if group else hostgroup
                for group_name in target_groups:
                    hosts.extend(inv.get_group_hosts(group_name))
            else:
                click.echo("❌ Specify --host, --group, or --hostgroup", err=True)
                sys.exit(1)
            
            if not hosts:
                click.echo("No hosts to check")
                return
            
            # Run health checks
            from ..core.ssh_executor import SSHExecutor
            from ..core.secrets import SecretsManager
            
            secrets = SecretsManager(ctx.obj['config_dir'])
            await secrets.load()
            
            ssh_executor = SSHExecutor(secrets)
            
            click.echo(f"🔍 Checking Splunk health on {len(hosts)} hosts...")
            click.echo()
            
            results = []
            success_count = 0
            
            for host in hosts:
                try:
                    click.echo(f"Checking {host.name} ({host.ansible_host})...")
                    
                    # Run Splunk health checks
                    health_checks = [
                        ("Version", f"{host.splunk_home or '/opt/splunk'}/bin/splunk version"),
                        ("Status", f"{host.splunk_home or '/opt/splunk'}/bin/splunk status"),
                        ("Management Port", f"netstat -tlnp | grep :{host.splunk_mgmt_port or 8089}"),
                        ("Forwarder Port", f"netstat -tlnp | grep :{host.splunk_forwarder_port or 9997}"),
                    ]
                    
                    if host.splunk_type == 'enterprise':
                        health_checks.append(("Web Port", f"netstat -tlnp | grep :{host.splunk_web_port or 8000}"))
                    
                    host_result = {
                        'host': host.name,
                        'ansible_host': host.ansible_host,
                        'splunk_type': host.splunk_type,
                        'splunk_version': host.splunk_version,
                        'checks': {}
                    }
                    
                    all_passed = True
                    for check_name, check_cmd in health_checks:
                        try:
                            result = await ssh_executor.execute_command(host, check_cmd, timeout=30)
                            if result.exit_code == 0:
                                host_result['checks'][check_name] = {
                                    'status': 'PASS',
                                    'output': result.stdout.strip()
                                }
                            else:
                                host_result['checks'][check_name] = {
                                    'status': 'FAIL',
                                    'output': result.stderr.strip()
                                }
                                all_passed = False
                        except Exception as e:
                            host_result['checks'][check_name] = {
                                'status': 'ERROR',
                                'output': str(e)
                            }
                            all_passed = False
                    
                    if all_passed:
                        click.echo(f"✅ {host.name} - ALL CHECKS PASSED")
                        success_count += 1
                    else:
                        click.echo(f"❌ {host.name} - SOME CHECKS FAILED")
                    
                    results.append(host_result)
                    click.echo()
                    
                except Exception as e:
                    click.echo(f"❌ {host.name} - ERROR: {e}")
                    click.echo()
            
            # Generate report if requested
            if report:
                report_content = _generate_health_report(results, report)
                
                if output:
                    output_path = Path(output)
                    output_path.write_text(report_content)
                    click.echo(f"📊 Report saved to: {output_path}")
                else:
                    click.echo(report_content)
            
            click.echo(f"Results: {success_count}/{len(hosts)} hosts healthy")
            
        except Exception as e:
            click.echo(f"❌ Error checking Splunk health: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_check_splunk())


def _generate_health_report(results: List[Dict[str, Any]], format: str) -> str:
    """Generate health check report"""
    if format == 'json':
        import json
        return json.dumps(results, indent=2)
    elif format == 'html':
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Splunk Health Check Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .host { margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }
        .host-header { background-color: #e8f4f8; padding: 10px; font-weight: bold; }
        .host-content { padding: 15px; }
        .check { margin: 10px 0; }
        .check-name { font-weight: bold; }
        .pass { color: green; }
        .fail { color: red; }
        .error { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Splunk Health Check Report</h1>
        <p>Generated: {datetime.now().isoformat()}</p>
    </div>
"""
        
        for result in results:
            html += f"""
    <div class="host">
        <div class="host-header">
            {result['host']} ({result['ansible_host']}) - {result['splunk_type']} {result['splunk_version']}
        </div>
        <div class="host-content">
"""
            
            for check_name, check_result in result['checks'].items():
                status_class = check_result['status'].lower()
                html += f"""
            <div class="check">
                <div class="check-name {status_class}">{check_name}: {check_result['status']}</div>
                <div>{check_result['output']}</div>
            </div>
"""
            
            html += """
        </div>
    </div>
"""
        
        html += """
</body>
</html>"""
        return html
    else:  # markdown
        md = f"""# Splunk Health Check Report

**Generated:** {datetime.now().isoformat()}

## Summary

- **Total Hosts:** {len(results)}
- **Healthy Hosts:** {sum(1 for r in results if all(c['status'] == 'PASS' for c in r['checks'].values()))}
- **Unhealthy Hosts:** {len(results) - sum(1 for r in results if all(c['status'] == 'PASS' for c in r['checks'].values()))}

## Host Details

"""
        
        for result in results:
            md += f"""### {result['host']} ({result['ansible_host']})

- **Splunk Type:** {result['splunk_type']}
- **Version:** {result['splunk_version']}

#### Health Checks

"""
            
            for check_name, check_result in result['checks'].items():
                status_emoji = "✅" if check_result['status'] == 'PASS' else "❌" if check_result['status'] == 'FAIL' else "⚠️"
                md += f"- {status_emoji} **{check_name}:** {check_result['status']}\n"
                if check_result['output']:
                    md += f"  ```\n  {check_result['output']}\n  ```\n"
            
            md += "\n"
        
        return md


@click.group()
def audit_command():
    """View audit logs and reports"""
    pass


@audit_command.command('events')
@click.option('--start-time', help='Start time filter (ISO format)')
@click.option('--end-time', help='End time filter (ISO format)')
@click.option('--event-type', help='Event type filter')
@click.option('--user', help='User filter')
@click.option('--host', help='Host filter')
@click.option('--run-id', help='Run ID filter')
@click.option('--limit', type=int, default=100, help='Maximum number of events')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def audit_events(ctx, start_time, end_time, event_type, user, host, run_id, limit, format):
    """View audit events"""
    async def _audit_events():
        try:
            from datetime import datetime
            
            # Parse time filters
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
            
            # Load audit logger
            audit = AuditLogger(ctx.obj['config_dir'])
            await audit.initialize()
            
            # Get events
            events = await audit.get_events(
                start_time=start_dt,
                end_time=end_dt,
                event_type=event_type,
                user=user,
                host=host,
                run_id=run_id,
                limit=limit
            )
            
            if format == 'json':
                events_data = []
                for event in events:
                    event_data = {
                        'event_id': event.event_id,
                        'timestamp': event.timestamp.isoformat(),
                        'event_type': event.event_type,
                        'user': event.user,
                        'host': event.host,
                        'action': event.action,
                        'status': event.status,
                        'details': event.details,
                        'run_id': event.run_id,
                        'task_id': event.task_id,
                        'duration': event.duration,
                        'error': event.error
                    }
                    events_data.append(event_data)
                click.echo(json.dumps(events_data, indent=2))
            else:
                # Table format
                if not events:
                    click.echo("No events found")
                    return
                
                # Print header
                click.echo(f"{'Timestamp':<20} {'Type':<15} {'User':<10} {'Host':<15} {'Action':<20} {'Status':<10}")
                click.echo("-" * 100)
                
                # Print events
                for event in events:
                    click.echo(f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} "
                             f"{event.event_type:<15} {event.user:<10} {event.host:<15} "
                             f"{event.action:<20} {event.status:<10}")
                
                click.echo(f"\nTotal: {len(events)} events")
                
        except Exception as e:
            click.echo(f"❌ Error viewing audit events: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_audit_events())


@audit_command.command('report')
@click.option('--start-time', help='Start time filter (ISO format)')
@click.option('--end-time', help='End time filter (ISO format)')
@click.option('--format', type=click.Choice(['json', 'markdown', 'html']), 
              default='markdown', help='Report format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def audit_report(ctx, start_time, end_time, format, output):
    """Generate audit report"""
    async def _audit_report():
        try:
            from datetime import datetime
            
            # Parse time filters
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
            
            # Load audit logger
            audit = AuditLogger(ctx.obj['config_dir'])
            await audit.initialize()
            
            # Generate report
            report = await audit.generate_audit_report(
                start_time=start_dt,
                end_time=end_dt,
                format=format
            )
            
            if output:
                output_path = Path(output)
                output_path.write_text(report)
                click.echo(f"📊 Report saved to: {output_path}")
            else:
                click.echo(report)
                
        except Exception as e:
            click.echo(f"❌ Error generating audit report: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_audit_report())


@click.group()
def config_command():
    """Manage configuration"""
    pass


@config_command.command('validate')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.pass_context
def config_validate(ctx, inventory):
    """Validate configuration files"""
    async def _validate_config():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Validate inventory
            issues = inv.validate_inventory()
            
            if issues:
                click.echo("❌ Configuration validation failed:")
                for issue in issues:
                    click.echo(f"  - {issue}")
                sys.exit(1)
            else:
                click.echo("✅ Configuration validation passed")
                
        except Exception as e:
            click.echo(f"❌ Error validating configuration: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_validate_config())


@config_command.command('show')
@click.option('--inventory', '-i', default='config/inventory.yml',
              help='Inventory file path')
@click.pass_context
def config_show(ctx, inventory):
    """Show configuration summary"""
    async def _show_config():
        try:
            # Load inventory
            inv = Inventory(ctx.obj['config_dir'])
            await inv.load(inventory)
            
            # Get summary
            summary = inv.get_inventory_summary()
            
            click.echo("📊 Configuration Summary")
            click.echo("=" * 30)
            click.echo(f"Total Hosts: {summary['total_hosts']}")
            click.echo(f"Total Groups: {summary['total_groups']}")
            click.echo()
            
            click.echo("Hosts by Splunk Type:")
            for splunk_type, count in summary['hosts_by_splunk_type'].items():
                click.echo(f"  {splunk_type}: {count}")
            click.echo()
            
            click.echo("Hosts by OS Family:")
            for os_family, count in summary['hosts_by_os_family'].items():
                click.echo(f"  {os_family}: {count}")
            click.echo()
            
            click.echo("Hosts by Group:")
            for group_name, count in summary['hosts_by_group'].items():
                click.echo(f"  {group_name}: {count}")
                
        except Exception as e:
            click.echo(f"❌ Error showing configuration: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_show_config())
