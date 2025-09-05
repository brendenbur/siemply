"""
Audit API Routes - Audit and logging endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from ...core.audit import AuditLogger, AuditEvent, TaskExecution
from ..dependencies import get_audit_logger


router = APIRouter()


# Pydantic models
class AuditEventResponse(BaseModel):
    event_id: str
    timestamp: str
    event_type: str
    user: str
    host: str
    action: str
    status: str
    details: Dict[str, Any]
    run_id: Optional[str]
    task_id: Optional[str]
    duration: Optional[float]
    error: Optional[str]


class TaskExecutionResponse(BaseModel):
    task_id: str
    run_id: str
    host: str
    task_name: str
    task_type: str
    start_time: str
    end_time: str
    duration: float
    status: str
    output: str
    error: Optional[str]
    changed: bool
    facts: Dict[str, Any]


class AuditReportResponse(BaseModel):
    report_generated: str
    period: Dict[str, Optional[str]]
    summary: Dict[str, Any]
    event_status_counts: Dict[str, int]
    task_status_counts: Dict[str, int]
    user_counts: Dict[str, int]
    host_counts: Dict[str, int]
    event_type_counts: Dict[str, int]


@router.get("/events", response_model=List[AuditEventResponse])
async def get_audit_events(
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    user: Optional[str] = Query(None, description="User filter"),
    host: Optional[str] = Query(None, description="Host filter"),
    run_id: Optional[str] = Query(None, description="Run ID filter"),
    limit: int = Query(100, description="Maximum number of events"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Get audit events with filters"""
    try:
        # Parse time filters
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Get events
        events = await audit_logger.get_events(
            start_time=start_dt,
            end_time=end_dt,
            event_type=event_type,
            user=user,
            host=host,
            run_id=run_id,
            limit=limit
        )
        
        # Convert to response format
        event_responses = []
        for event in events:
            event_responses.append(AuditEventResponse(
                event_id=event.event_id,
                timestamp=event.timestamp.isoformat(),
                event_type=event.event_type,
                user=event.user,
                host=event.host,
                action=event.action,
                status=event.status,
                details=event.details,
                run_id=event.run_id,
                task_id=event.task_id,
                duration=event.duration,
                error=event.error
            ))
        
        return event_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit events: {str(e)}")


@router.get("/task-executions", response_model=List[TaskExecutionResponse])
async def get_task_executions(
    run_id: Optional[str] = Query(None, description="Run ID filter"),
    host: Optional[str] = Query(None, description="Host filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    limit: int = Query(100, description="Maximum number of executions"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Get task executions with filters"""
    try:
        # Get executions
        executions = await audit_logger.get_task_executions(
            run_id=run_id,
            host=host,
            status=status,
            limit=limit
        )
        
        # Convert to response format
        execution_responses = []
        for execution in executions:
            execution_responses.append(TaskExecutionResponse(
                task_id=execution.task_id,
                run_id=execution.run_id,
                host=execution.host,
                task_name=execution.task_name,
                task_type=execution.task_type,
                start_time=execution.start_time.isoformat(),
                end_time=execution.end_time.isoformat(),
                duration=execution.duration,
                status=execution.status,
                output=execution.output,
                error=execution.error,
                changed=execution.changed,
                facts=execution.facts
            ))
        
        return execution_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task executions: {str(e)}")


@router.get("/report", response_model=AuditReportResponse)
async def get_audit_report(
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    format: str = Query("json", description="Report format"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Generate audit report"""
    try:
        # Parse time filters
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Generate report
        report = await audit_logger.generate_audit_report(
            start_time=start_dt,
            end_time=end_dt,
            format=format
        )
        
        if format == "json":
            return AuditReportResponse(**report)
        else:
            # For markdown/html, return the raw content
            return {"content": report, "format": format}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audit report: {str(e)}")


@router.get("/runs/{run_id}/summary")
async def get_run_summary(
    run_id: str,
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Get summary of a specific run"""
    try:
        summary = await audit_logger.get_run_summary(run_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run summary: {str(e)}")


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(30, description="Number of days to include"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Get audit statistics"""
    try:
        # Calculate date range
        end_time = datetime.now()
        start_time = datetime.fromtimestamp(end_time.timestamp() - (days * 24 * 60 * 60))
        
        # Get events for the period
        events = await audit_logger.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Get task executions for the period
        executions = await audit_logger.get_task_executions(limit=10000)
        
        # Calculate statistics
        total_events = len(events)
        total_tasks = len(executions)
        
        # Event status counts
        event_status_counts = {}
        for event in events:
            status = event.status
            event_status_counts[status] = event_status_counts.get(status, 0) + 1
        
        # Task status counts
        task_status_counts = {}
        for execution in executions:
            status = execution.status
            task_status_counts[status] = task_status_counts.get(status, 0) + 1
        
        # User activity
        user_counts = {}
        for event in events:
            user = event.user
            user_counts[user] = user_counts.get(user, 0) + 1
        
        # Host activity
        host_counts = {}
        for event in events:
            host = event.host
            host_counts[host] = host_counts.get(host, 0) + 1
        
        # Event type counts
        event_type_counts = {}
        for event in events:
            event_type = event.event_type
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Calculate average task duration
        avg_task_duration = 0
        if executions:
            total_duration = sum(execution.duration for execution in executions)
            avg_task_duration = total_duration / len(executions)
        
        return {
            "period_days": days,
            "total_events": total_events,
            "total_tasks": total_tasks,
            "avg_task_duration": avg_task_duration,
            "event_status_counts": event_status_counts,
            "task_status_counts": task_status_counts,
            "user_counts": user_counts,
            "host_counts": host_counts,
            "event_type_counts": event_type_counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit stats: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_events(
    days: int = Query(90, description="Number of days to retain"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Clean up old audit events"""
    try:
        await audit_logger.cleanup_old_events(days)
        return {"message": f"Cleaned up events older than {days} days"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old events: {str(e)}")


@router.get("/export")
async def export_audit_data(
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    format: str = Query("json", description="Export format"),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Export audit data"""
    try:
        # Parse time filters
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Get events
        events = await audit_logger.get_events(
            start_time=start_dt,
            end_time=end_dt,
            limit=10000
        )
        
        # Get task executions
        executions = await audit_logger.get_task_executions(limit=10000)
        
        # Convert to export format
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "period": {
                "start_time": start_time,
                "end_time": end_time
            },
            "events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "user": event.user,
                    "host": event.host,
                    "action": event.action,
                    "status": event.status,
                    "details": event.details,
                    "run_id": event.run_id,
                    "task_id": event.task_id,
                    "duration": event.duration,
                    "error": event.error
                }
                for event in events
            ],
            "task_executions": [
                {
                    "task_id": execution.task_id,
                    "run_id": execution.run_id,
                    "host": execution.host,
                    "task_name": execution.task_name,
                    "task_type": execution.task_type,
                    "start_time": execution.start_time.isoformat(),
                    "end_time": execution.end_time.isoformat(),
                    "duration": execution.duration,
                    "status": execution.status,
                    "output": execution.output,
                    "error": execution.error,
                    "changed": execution.changed,
                    "facts": execution.facts
                }
                for execution in executions
            ]
        }
        
        if format == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io
            
            output = io.StringIO()
            
            # Write events CSV
            if events:
                writer = csv.DictWriter(output, fieldnames=[
                    "event_id", "timestamp", "event_type", "user", "host", 
                    "action", "status", "run_id", "task_id", "duration", "error"
                ])
                writer.writeheader()
                for event in events:
                    writer.writerow({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type,
                        "user": event.user,
                        "host": event.host,
                        "action": event.action,
                        "status": event.status,
                        "run_id": event.run_id or "",
                        "task_id": event.task_id or "",
                        "duration": event.duration or 0,
                        "error": event.error or ""
                    })
            
            return {"content": output.getvalue(), "format": "csv"}
        
        else:
            return export_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export audit data: {str(e)}")
