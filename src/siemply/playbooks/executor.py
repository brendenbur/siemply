"""
Playbook execution engine
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from ..database.models import Host, Playbook, Run, RunStatus
from ..ssh.runner import SSHManager
from ..playbooks.schema import PlaybookSchema


class PlaybookExecutor:
    """Executes playbooks on multiple hosts with concurrency control"""
    
    def __init__(self, db: Session, max_concurrency: int = 5):
        self.db = db
        self.max_concurrency = max_concurrency
        self.executor = ThreadPoolExecutor(max_workers=max_concurrency)
    
    def execute_playbook(self, playbook_id: str, host_ids: List[str], 
                        run_id: Optional[str] = None) -> str:
        """Execute a playbook on multiple hosts"""
        
        # Get playbook
        playbook = self.db.query(Playbook).filter(Playbook.id == playbook_id).first()
        if not playbook:
            raise ValueError("Playbook not found")
        
        # Get hosts
        hosts = self.db.query(Host).filter(Host.id.in_(host_ids)).all()
        if not hosts:
            raise ValueError("No hosts found")
        
        # Create run record
        if not run_id:
            run = Run(
                playbook_id=playbook_id,
                host_ids=host_ids,
                status=RunStatus.RUNNING
            )
            self.db.add(run)
            self.db.commit()
            run_id = str(run.id)
        else:
            run = self.db.query(Run).filter(Run.id == run_id).first()
            if not run:
                raise ValueError("Run not found")
        
        try:
            # Parse playbook YAML
            playbook_schema = PlaybookSchema.parse_obj(yaml.safe_load(playbook.yaml_content))
            
            # Execute tasks on all hosts
            self._execute_tasks_on_hosts(run, hosts, playbook_schema.tasks)
            
            # Update run status
            run.status = RunStatus.COMPLETED
            run.ended_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            # Update run status to failed
            run.status = RunStatus.FAILED
            run.ended_at = datetime.utcnow()
            run.add_log("system", "error", f"Playbook execution failed: {str(e)}")
            self.db.commit()
            raise
        
        return run_id
    
    def _execute_tasks_on_hosts(self, run: Run, hosts: List[Host], tasks: List[Dict]):
        """Execute tasks on all hosts with concurrency control"""
        
        # Create futures for each host
        futures = []
        for host in hosts:
            future = self.executor.submit(self._execute_tasks_on_host, run, host, tasks)
            futures.append((host.id, future))
        
        # Wait for completion and collect results
        completed_hosts = 0
        failed_hosts = 0
        
        for host_id, future in futures:
            try:
                success, message = future.result(timeout=300)  # 5 minute timeout per host
                if success:
                    completed_hosts += 1
                else:
                    failed_hosts += 1
            except Exception as e:
                failed_hosts += 1
                run.add_log(str(host_id), "error", f"Host execution failed: {str(e)}")
        
        # Update run status based on results
        if failed_hosts == 0:
            run.status = RunStatus.COMPLETED
        elif completed_hosts == 0:
            run.status = RunStatus.FAILED
        else:
            run.status = RunStatus.PARTIAL
    
    def _execute_tasks_on_host(self, run: Run, host: Host, tasks: List[Dict]) -> tuple[bool, str]:
        """Execute all tasks on a single host"""
        host_id = str(host.id)
        
        try:
            run.add_log(host_id, "info", f"Starting execution on {host.hostname}")
            
            for task in tasks:
                task_name = task.get('name', 'unnamed')
                run.add_log(host_id, "info", f"Executing task: {task_name}")
                
                success, message, output = SSHManager.execute_playbook_task(host, task)
                
                if success:
                    run.add_log(host_id, "success", f"Task '{task_name}' completed: {message}")
                    if output:
                        run.add_log(host_id, "output", output)
                else:
                    run.add_log(host_id, "error", f"Task '{task_name}' failed: {message}")
                    if output:
                        run.add_log(host_id, "error", output)
                    
                    # Check if we should ignore errors
                    if not task.get('ignore_errors', False):
                        run.add_log(host_id, "error", f"Stopping execution due to task failure")
                        return False, f"Task '{task_name}' failed: {message}"
            
            run.add_log(host_id, "success", f"All tasks completed successfully on {host.hostname}")
            return True, "Execution completed successfully"
            
        except Exception as e:
            run.add_log(host_id, "error", f"Execution failed: {str(e)}")
            return False, str(e)
    
    def get_run_logs(self, run_id: str) -> List[Dict]:
        """Get logs for a specific run"""
        run = self.db.query(Run).filter(Run.id == run_id).first()
        if not run:
            return []
        
        return run.logs or []
    
    def get_run_status(self, run_id: str) -> Optional[Dict]:
        """Get status of a specific run"""
        run = self.db.query(Run).filter(Run.id == run_id).first()
        if not run:
            return None
        
        return run.to_dict()
    
    def cleanup(self):
        """Cleanup executor resources"""
        self.executor.shutdown(wait=True)
