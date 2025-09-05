"""
Siemply Orchestrator - Core coordination and execution engine
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import yaml
import json

from .task_runner import TaskRunner
from .ssh_executor import SSHExecutor
from .inventory import Inventory
from .secrets import SecretsManager
from .audit import AuditLogger


@dataclass
class RunConfig:
    """Configuration for a Siemply run"""
    playbook: str
    inventory: str
    target_hosts: List[str]
    target_groups: List[str]
    dry_run: bool = False
    limit: Optional[int] = None
    forks: int = 10
    timeout: int = 3600
    retry_attempts: int = 3
    retry_delay: int = 30
    batch_size: int = 10
    batch_delay: int = 300
    soak_time: int = 600
    max_failures: int = 3
    max_failures_percentage: float = 10.0
    tags: List[str] = None
    skip_tags: List[str] = None
    extra_vars: Dict[str, Any] = None


@dataclass
class RunResult:
    """Result of a Siemply run"""
    run_id: str
    status: str  # success, failed, partial
    start_time: datetime
    end_time: datetime
    duration: float
    total_hosts: int
    successful_hosts: int
    failed_hosts: int
    skipped_hosts: int
    results: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class Orchestrator:
    """
    Main orchestrator class that coordinates task execution across hosts
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.inventory = Inventory(config_dir)
        self.secrets = SecretsManager(config_dir)
        self.audit = AuditLogger(config_dir)
        self.ssh_executor = SSHExecutor(self.secrets)
        self.task_runner = TaskRunner(self.ssh_executor, self.audit)
        
        # Runtime state
        self.active_runs: Dict[str, RunConfig] = {}
        self.run_results: Dict[str, RunResult] = {}
        
    async def initialize(self):
        """Initialize the orchestrator and load configuration"""
        try:
            await self.inventory.load()
            await self.secrets.load()
            await self.audit.initialize()
            self.logger.info("Orchestrator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def run_playbook(self, config: RunConfig) -> RunResult:
        """
        Execute a playbook against target hosts
        
        Args:
            config: Run configuration
            
        Returns:
            RunResult with execution details
        """
        run_id = self._generate_run_id()
        start_time = datetime.now()
        
        self.logger.info(f"Starting playbook run {run_id}: {config.playbook}")
        
        try:
            # Load playbook
            playbook = await self._load_playbook(config.playbook)
            
            # Resolve target hosts
            target_hosts = await self._resolve_target_hosts(config)
            
            # Apply limits and concurrency
            if config.limit:
                target_hosts = target_hosts[:config.limit]
            
            # Execute playbook
            results = await self._execute_playbook(playbook, target_hosts, config)
            
            # Calculate final status
            status = self._calculate_run_status(results)
            
            # Create run result
            end_time = datetime.now()
            run_result = RunResult(
                run_id=run_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration=(end_time - start_time).total_seconds(),
                total_hosts=len(target_hosts),
                successful_hosts=len([r for r in results.values() if r.get('status') == 'success']),
                failed_hosts=len([r for r in results.values() if r.get('status') == 'failed']),
                skipped_hosts=len([r for r in results.values() if r.get('status') == 'skipped']),
                results=results,
                errors=[r.get('error') for r in results.values() if r.get('error')],
                warnings=[r.get('warning') for r in results.values() if r.get('warning')]
            )
            
            # Store result
            self.run_results[run_id] = run_result
            
            # Generate report
            await self._generate_run_report(run_result)
            
            self.logger.info(f"Playbook run {run_id} completed: {status}")
            return run_result
            
        except Exception as e:
            self.logger.error(f"Playbook run {run_id} failed: {e}")
            raise
    
    async def _load_playbook(self, playbook_path: str) -> Dict[str, Any]:
        """Load and validate playbook configuration"""
        try:
            with open(playbook_path, 'r') as f:
                playbook = yaml.safe_load(f)
            
            # Validate playbook structure
            required_fields = ['name', 'tasks', 'execution']
            for field in required_fields:
                if field not in playbook:
                    raise ValueError(f"Playbook missing required field: {field}")
            
            return playbook
            
        except Exception as e:
            self.logger.error(f"Failed to load playbook {playbook_path}: {e}")
            raise
    
    async def _resolve_target_hosts(self, config: RunConfig) -> List[Dict[str, Any]]:
        """Resolve target hosts from inventory based on config"""
        hosts = []
        
        # Add specific hosts
        for host_name in config.target_hosts:
            host = self.inventory.get_host(host_name)
            if host:
                hosts.append(host)
            else:
                self.logger.warning(f"Host {host_name} not found in inventory")
        
        # Add hosts from groups
        for group_name in config.target_groups:
            group_hosts = self.inventory.get_group_hosts(group_name)
            hosts.extend(group_hosts)
        
        # Remove duplicates
        seen = set()
        unique_hosts = []
        for host in hosts:
            host_id = host.get('ansible_host', host.get('name'))
            if host_id not in seen:
                seen.add(host_id)
                unique_hosts.append(host)
        
        return unique_hosts
    
    async def _execute_playbook(self, playbook: Dict[str, Any], hosts: List[Dict[str, Any]], config: RunConfig) -> Dict[str, Any]:
        """Execute playbook tasks against hosts"""
        results = {}
        
        # Get execution strategy
        execution = playbook.get('execution', {})
        strategy = execution.get('strategy', 'rolling')
        batch_size = config.batch_size or execution.get('batch_size', 10)
        batch_delay = config.batch_delay or execution.get('batch_delay', 300)
        
        if strategy == 'rolling':
            results = await self._execute_rolling(playbook, hosts, config, batch_size, batch_delay)
        elif strategy == 'parallel':
            results = await self._execute_parallel(playbook, hosts, config)
        else:
            raise ValueError(f"Unknown execution strategy: {strategy}")
        
        return results
    
    async def _execute_rolling(self, playbook: Dict[str, Any], hosts: List[Dict[str, Any]], config: RunConfig, batch_size: int, batch_delay: int) -> Dict[str, Any]:
        """Execute playbook using rolling strategy"""
        results = {}
        tasks = playbook.get('tasks', [])
        
        # Process hosts in batches
        for i in range(0, len(hosts), batch_size):
            batch = hosts[i:i + batch_size]
            batch_results = {}
            
            self.logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} hosts")
            
            # Execute tasks for batch
            for host in batch:
                host_id = host.get('ansible_host', host.get('name'))
                try:
                    host_result = await self._execute_host_tasks(playbook, host, config)
                    batch_results[host_id] = host_result
                except Exception as e:
                    self.logger.error(f"Failed to execute tasks on {host_id}: {e}")
                    batch_results[host_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'tasks': []
                    }
            
            # Update results
            results.update(batch_results)
            
            # Wait between batches (except for last batch)
            if i + batch_size < len(hosts):
                self.logger.info(f"Waiting {batch_delay} seconds before next batch")
                await asyncio.sleep(batch_delay)
        
        return results
    
    async def _execute_parallel(self, playbook: Dict[str, Any], hosts: List[Dict[str, Any]], config: RunConfig) -> Dict[str, Any]:
        """Execute playbook using parallel strategy"""
        tasks = []
        
        # Create tasks for all hosts
        for host in hosts:
            task = asyncio.create_task(
                self._execute_host_tasks(playbook, host, config)
            )
            tasks.append((host, task))
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(config.forks)
        
        async def execute_with_semaphore(host, task):
            async with semaphore:
                return await task
        
        # Wait for all tasks to complete
        results = {}
        for host, task in tasks:
            host_id = host.get('ansible_host', host.get('name'))
            try:
                result = await execute_with_semaphore(host, task)
                results[host_id] = result
            except Exception as e:
                self.logger.error(f"Failed to execute tasks on {host_id}: {e}")
                results[host_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'tasks': []
                }
        
        return results
    
    async def _execute_host_tasks(self, playbook: Dict[str, Any], host: Dict[str, Any], config: RunConfig) -> Dict[str, Any]:
        """Execute all tasks for a single host"""
        host_id = host.get('ansible_host', host.get('name'))
        host_results = {
            'status': 'success',
            'tasks': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration': 0
        }
        
        try:
            tasks = playbook.get('tasks', [])
            
            for task_config in tasks:
                task_result = await self.task_runner.execute_task(
                    task_config, host, config
                )
                host_results['tasks'].append(task_result)
                
                # Check for task failure
                if task_result.get('status') == 'failed':
                    host_results['status'] = 'failed'
                    host_results['error'] = task_result.get('error')
                    break
            
            host_results['end_time'] = datetime.now().isoformat()
            host_results['duration'] = (
                datetime.fromisoformat(host_results['end_time']) - 
                datetime.fromisoformat(host_results['start_time'])
            ).total_seconds()
            
        except Exception as e:
            self.logger.error(f"Error executing tasks on {host_id}: {e}")
            host_results['status'] = 'failed'
            host_results['error'] = str(e)
            host_results['end_time'] = datetime.now().isoformat()
        
        return host_results
    
    def _calculate_run_status(self, results: Dict[str, Any]) -> str:
        """Calculate overall run status from individual host results"""
        total = len(results)
        if total == 0:
            return 'skipped'
        
        successful = len([r for r in results.values() if r.get('status') == 'success'])
        failed = len([r for r in results.values() if r.get('status') == 'failed'])
        
        if failed == 0:
            return 'success'
        elif successful == 0:
            return 'failed'
        else:
            return 'partial'
    
    async def _generate_run_report(self, run_result: RunResult):
        """Generate run report in Markdown format"""
        report_path = f"reports/run_{run_result.run_id}.md"
        
        # Ensure reports directory exists
        import os
        os.makedirs("reports", exist_ok=True)
        
        report_content = f"""# Siemply Run Report

**Run ID:** {run_result.run_id}  
**Status:** {run_result.status.upper()}  
**Start Time:** {run_result.start_time.isoformat()}  
**End Time:** {run_result.end_time.isoformat()}  
**Duration:** {run_result.duration:.2f} seconds  

## Summary

- **Total Hosts:** {run_result.total_hosts}
- **Successful:** {run_result.successful_hosts}
- **Failed:** {run_result.failed_hosts}
- **Skipped:** {run_result.skipped_hosts}

## Host Results

"""
        
        for host_id, result in run_result.results.items():
            status_emoji = "✅" if result.get('status') == 'success' else "❌" if result.get('status') == 'failed' else "⏭️"
            report_content += f"### {status_emoji} {host_id}\n\n"
            report_content += f"**Status:** {result.get('status', 'unknown')}\n"
            report_content += f"**Duration:** {result.get('duration', 0):.2f}s\n"
            
            if result.get('error'):
                report_content += f"**Error:** {result.get('error')}\n"
            
            if result.get('tasks'):
                report_content += "\n**Tasks:**\n"
                for task in result.get('tasks', []):
                    task_status = "✅" if task.get('status') == 'success' else "❌"
                    report_content += f"- {task_status} {task.get('name', 'Unknown')}\n"
            
            report_content += "\n"
        
        # Write report
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Run report generated: {report_path}")
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    async def get_run_status(self, run_id: str) -> Optional[RunResult]:
        """Get status of a specific run"""
        return self.run_results.get(run_id)
    
    async def list_runs(self) -> List[Dict[str, Any]]:
        """List all runs with basic information"""
        runs = []
        for run_id, result in self.run_results.items():
            runs.append({
                'run_id': run_id,
                'status': result.status,
                'start_time': result.start_time.isoformat(),
                'duration': result.duration,
                'total_hosts': result.total_hosts,
                'successful_hosts': result.successful_hosts,
                'failed_hosts': result.failed_hosts
            })
        return runs
