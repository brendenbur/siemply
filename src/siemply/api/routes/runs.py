"""
Runs API Routes - Playbook execution endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from ...core.orchestrator import Orchestrator, RunConfig, RunResult
from ...core.inventory import Inventory
from ..dependencies import get_orchestrator, get_inventory


router = APIRouter()


# Pydantic models
class RunCreate(BaseModel):
    playbook: str
    target_hosts: Optional[List[str]] = []
    target_groups: Optional[List[str]] = []
    dry_run: bool = False
    limit: Optional[int] = None
    forks: int = 10
    timeout: int = 3600
    batch_size: int = 10
    batch_delay: int = 300
    tags: Optional[List[str]] = None
    skip_tags: Optional[List[str]] = None
    extra_vars: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    run_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: float
    total_hosts: int
    successful_hosts: int
    failed_hosts: int
    skipped_hosts: int
    playbook: str
    target_hosts: List[str]
    target_groups: List[str]
    dry_run: bool


class RunDetail(BaseModel):
    run_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: float
    total_hosts: int
    successful_hosts: int
    failed_hosts: int
    skipped_hosts: int
    playbook: str
    target_hosts: List[str]
    target_groups: List[str]
    dry_run: bool
    results: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class RunProgress(BaseModel):
    run_id: str
    status: str
    current_phase: str
    current_host: Optional[str]
    progress_percentage: float
    completed_hosts: int
    total_hosts: int
    estimated_completion: Optional[str]


# In-memory storage for run progress (in production, use Redis or database)
run_progress: Dict[str, RunProgress] = {}


@router.post("/", response_model=RunResponse)
async def create_run(
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    inventory: Inventory = Depends(get_inventory)
):
    """Create and start a new run"""
    try:
        # Validate playbook exists
        import os
        if not os.path.exists(run_data.playbook):
            raise HTTPException(status_code=400, detail=f"Playbook not found: {run_data.playbook}")
        
        # Create run config
        config = RunConfig(
            playbook=run_data.playbook,
            inventory="config/inventory.yml",
            target_hosts=run_data.target_hosts,
            target_groups=run_data.target_groups,
            dry_run=run_data.dry_run,
            limit=run_data.limit,
            forks=run_data.forks,
            timeout=run_data.timeout,
            batch_size=run_data.batch_size,
            batch_delay=run_data.batch_delay,
            tags=run_data.tags,
            skip_tags=run_data.skip_tags,
            extra_vars=run_data.extra_vars or {}
        )
        
        # Start run in background
        background_tasks.add_task(execute_run, orchestrator, config)
        
        # Generate run ID (in production, this would come from the orchestrator)
        import uuid
        run_id = str(uuid.uuid4())[:8]
        
        # Initialize progress tracking
        run_progress[run_id] = RunProgress(
            run_id=run_id,
            status="starting",
            current_phase="initialization",
            current_host=None,
            progress_percentage=0.0,
            completed_hosts=0,
            total_hosts=len(run_data.target_hosts) + sum(len(inventory.get_group_hosts(g)) for g in run_data.target_groups),
            estimated_completion=None
        )
        
        return RunResponse(
            run_id=run_id,
            status="starting",
            start_time=datetime.now().isoformat(),
            end_time=None,
            duration=0.0,
            total_hosts=run_progress[run_id].total_hosts,
            successful_hosts=0,
            failed_hosts=0,
            skipped_hosts=0,
            playbook=run_data.playbook,
            target_hosts=run_data.target_hosts,
            target_groups=run_data.target_groups,
            dry_run=run_data.dry_run
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")


async def execute_run(orchestrator: Orchestrator, config: RunConfig):
    """Execute a run in the background"""
    run_id = None
    try:
        # Update progress
        if run_id in run_progress:
            run_progress[run_id].status = "running"
            run_progress[run_id].current_phase = "execution"
        
        # Execute run
        result = await orchestrator.run_playbook(config)
        run_id = result.run_id
        
        # Update final progress
        if run_id in run_progress:
            run_progress[run_id].status = result.status
            run_progress[run_id].current_phase = "completed"
            run_progress[run_id].progress_percentage = 100.0
            run_progress[run_id].completed_hosts = result.successful_hosts + result.failed_hosts + result.skipped_hosts
        
    except Exception as e:
        if run_id and run_id in run_progress:
            run_progress[run_id].status = "failed"
            run_progress[run_id].current_phase = "error"
        logging.error(f"Run execution failed: {e}")


@router.get("/", response_model=List[RunResponse])
async def list_runs(
    limit: int = 50,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """List all runs"""
    try:
        runs = await orchestrator.list_runs()
        
        # Convert to response format
        run_responses = []
        for run in runs[:limit]:
            run_responses.append(RunResponse(
                run_id=run['run_id'],
                status=run['status'],
                start_time=run['start_time'],
                end_time=None,  # Would need to get from orchestrator
                duration=run['duration'],
                total_hosts=run['total_hosts'],
                successful_hosts=run['successful_hosts'],
                failed_hosts=run['failed_hosts'],
                skipped_hosts=run['skipped_hosts'],
                playbook="",  # Would need to get from orchestrator
                target_hosts=[],  # Would need to get from orchestrator
                target_groups=[],  # Would need to get from orchestrator
                dry_run=False  # Would need to get from orchestrator
            ))
        
        return run_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(
    run_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get a specific run by ID"""
    try:
        result = await orchestrator.get_run_status(run_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        return RunDetail(
            run_id=result.run_id,
            status=result.status,
            start_time=result.start_time.isoformat(),
            end_time=result.end_time.isoformat(),
            duration=result.duration,
            total_hosts=result.total_hosts,
            successful_hosts=result.successful_hosts,
            failed_hosts=result.failed_hosts,
            skipped_hosts=result.skipped_hosts,
            playbook="",  # Would need to get from orchestrator
            target_hosts=[],  # Would need to get from orchestrator
            target_groups=[],  # Would need to get from orchestrator
            dry_run=False,  # Would need to get from orchestrator
            results=result.results,
            errors=result.errors,
            warnings=result.warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")


@router.get("/{run_id}/progress", response_model=RunProgress)
async def get_run_progress(run_id: str):
    """Get run progress"""
    try:
        if run_id not in run_progress:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        return run_progress[run_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run progress: {str(e)}")


@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Cancel a running run"""
    try:
        # Update progress
        if run_id in run_progress:
            run_progress[run_id].status = "cancelled"
            run_progress[run_id].current_phase = "cancelled"
        
        # In a real implementation, you would cancel the actual run
        # For now, just update the progress
        
        return {"message": f"Run '{run_id}' cancelled"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")


@router.get("/{run_id}/logs")
async def get_run_logs(
    run_id: str,
    host: Optional[str] = None,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get run logs"""
    try:
        result = await orchestrator.get_run_status(run_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        # Filter by host if specified
        if host and host in result.results:
            return {host: result.results[host]}
        
        return result.results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run logs: {str(e)}")


@router.get("/{run_id}/report")
async def get_run_report(
    run_id: str,
    format: str = "json",
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get run report"""
    try:
        result = await orchestrator.get_run_status(run_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        if format == "markdown":
            # Generate markdown report
            report = f"""# Run Report - {run_id}

**Status:** {result.status.upper()}
**Start Time:** {result.start_time.isoformat()}
**End Time:** {result.end_time.isoformat()}
**Duration:** {result.duration:.2f} seconds

## Summary

- **Total Hosts:** {result.total_hosts}
- **Successful:** {result.successful_hosts}
- **Failed:** {result.failed_hosts}
- **Skipped:** {result.skipped_hosts}

## Host Results

"""
            
            for host_id, host_result in result.results.items():
                status_emoji = "✅" if host_result.get('status') == 'success' else "❌"
                report += f"### {status_emoji} {host_id}\n\n"
                report += f"**Status:** {host_result.get('status', 'unknown')}\n"
                report += f"**Duration:** {host_result.get('duration', 0):.2f}s\n"
                
                if host_result.get('error'):
                    report += f"**Error:** {host_result.get('error')}\n"
                
                report += "\n"
            
            return {"report": report, "format": "markdown"}
        
        else:
            # Return JSON report
            return {
                "run_id": result.run_id,
                "status": result.status,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "duration": result.duration,
                "total_hosts": result.total_hosts,
                "successful_hosts": result.successful_hosts,
                "failed_hosts": result.failed_hosts,
                "skipped_hosts": result.skipped_hosts,
                "results": result.results,
                "errors": result.errors,
                "warnings": result.warnings
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run report: {str(e)}")
