"""
Playbook Run Management API routes
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json
import asyncio

from ...database.database import get_db
from ...database.models import Run, Host, Playbook, RunStatus
from ...playbooks.executor import PlaybookExecutor

router = APIRouter()


# Pydantic models for API
class RunCreate(BaseModel):
    playbook_id: str = Field(..., description="Playbook ID to execute")
    host_ids: List[str] = Field(..., min_items=1, description="List of host IDs to run on")


class RunResponse(BaseModel):
    id: str
    playbook_id: str
    host_ids: List[str]
    started_at: str
    ended_at: Optional[str]
    status: str
    logs: List[dict]
    created_at: str


class RunStatusResponse(BaseModel):
    id: str
    status: str
    progress: dict
    logs: List[dict]


@router.get("/", response_model=List[RunResponse])
async def list_runs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    db: Session = Depends(get_db)
):
    """List all runs with optional filtering"""
    query = db.query(Run)
    
    if status:
        query = query.filter(Run.status == status)
    
    runs = query.order_by(Run.created_at.desc()).offset(offset).limit(limit).all()
    return [RunResponse(**run.to_dict()) for run in runs]


@router.post("/", response_model=RunResponse)
async def create_run(run_data: RunCreate, db: Session = Depends(get_db)):
    """Start a new playbook run"""
    
    # Validate playbook exists
    try:
        playbook_uuid = uuid.UUID(run_data.playbook_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playbook ID")
    
    playbook = db.query(Playbook).filter(Playbook.id == playbook_uuid).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    # Validate hosts exist
    try:
        host_uuids = [uuid.UUID(host_id) for host_id in run_data.host_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID in list")
    
    hosts = db.query(Host).filter(Host.id.in_(host_uuids)).all()
    if not hosts:
        raise HTTPException(status_code=404, detail="No hosts found")
    
    if len(hosts) != len(run_data.host_ids):
        found_ids = [str(host.id) for host in hosts]
        missing_ids = [host_id for host_id in run_data.host_ids if host_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Hosts not found: {missing_ids}")
    
    # Create run
    run = Run(
        playbook_id=run_data.playbook_id,
        host_ids=run_data.host_ids,
        status=RunStatus.RUNNING
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Start execution in background
    executor = PlaybookExecutor(db)
    try:
        run_id = executor.execute_playbook(run_data.playbook_id, run_data.host_ids, str(run.id))
        return RunResponse(**run.to_dict())
    except Exception as e:
        # Update run status to failed
        run.status = RunStatus.FAILED
        run.add_log("system", "error", f"Run failed to start: {str(e)}")
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start run: {str(e)}")


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get a specific run"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return RunResponse(**run.to_dict())


@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """Get run status and progress"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Calculate progress
    total_hosts = len(run.host_ids)
    completed_tasks = 0
    failed_tasks = 0
    
    for log in run.logs or []:
        if log.get("level") == "success":
            completed_tasks += 1
        elif log.get("level") == "error":
            failed_tasks += 1
    
    progress = {
        "total_hosts": total_hosts,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "percentage": (completed_tasks / max(total_hosts, 1)) * 100
    }
    
    return RunStatusResponse(
        id=str(run.id),
        status=run.status,
        progress=progress,
        logs=run.logs or []
    )


@router.get("/{run_id}/stream")
async def stream_run_logs(run_id: str, db: Session = Depends(get_db)):
    """Stream run logs via Server-Sent Events"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    async def generate_logs():
        last_log_count = 0
        
        while True:
            # Refresh run from database
            db.refresh(run)
            current_logs = run.logs or []
            
            # Send new logs
            if len(current_logs) > last_log_count:
                new_logs = current_logs[last_log_count:]
                for log in new_logs:
                    yield f"data: {json.dumps(log)}\n\n"
                last_log_count = len(current_logs)
            
            # Check if run is complete
            if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.PARTIAL]:
                yield f"data: {json.dumps({'type': 'run_complete', 'status': run.status})}\n\n"
                break
            
            # Wait before next check
            await asyncio.sleep(1)
    
    return StreamingResponse(
        generate_logs(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.delete("/{run_id}")
async def delete_run(run_id: str, db: Session = Depends(get_db)):
    """Delete a run"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    db.delete(run)
    db.commit()
    
    return {"message": "Run deleted successfully"}


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, db: Session = Depends(get_db)):
    """Cancel a running playbook"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status != RunStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Run is not running")
    
    # Mark as failed
    run.status = RunStatus.FAILED
    run.add_log("system", "info", "Run cancelled by user")
    db.commit()
    
    return {"message": "Run cancelled successfully"}
