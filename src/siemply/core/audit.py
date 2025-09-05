"""
Siemply Audit Logger - Immutable audit logging and reporting
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
import hashlib


@dataclass
class AuditEvent:
    """Represents an audit event"""
    event_id: str
    timestamp: datetime
    event_type: str
    user: str
    host: str
    action: str
    status: str
    details: Dict[str, Any]
    run_id: Optional[str] = None
    task_id: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


@dataclass
class TaskExecution:
    """Represents a task execution"""
    task_id: str
    run_id: str
    host: str
    task_name: str
    task_type: str
    start_time: datetime
    end_time: datetime
    duration: float
    status: str
    output: str
    error: Optional[str] = None
    changed: bool = False
    facts: Dict[str, Any] = None


class AuditLogger:
    """
    Immutable audit logging system for Siemply operations
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # Audit database
        self.audit_db = os.path.join(config_dir, "audit.db")
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize audit database"""
        try:
            os.makedirs(os.path.dirname(self.audit_db), exist_ok=True)
            
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                # Create audit_events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        user TEXT NOT NULL,
                        host TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT NOT NULL,
                        run_id TEXT,
                        task_id TEXT,
                        duration REAL,
                        error TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create task_executions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_executions (
                        task_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        host TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        duration REAL NOT NULL,
                        status TEXT NOT NULL,
                        output TEXT NOT NULL,
                        error TEXT,
                        changed BOOLEAN NOT NULL,
                        facts TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_host ON audit_events(host)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_run_id ON audit_events(run_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_executions_run_id ON task_executions(run_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_executions_host ON task_executions(host)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status)")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize audit database: {e}")
            raise
    
    async def initialize(self):
        """Initialize audit logger"""
        self.logger.info("Audit logger initialized")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def log_event(self, event_type: str, user: str, host: str, action: str, 
                       status: str, details: Dict[str, Any], run_id: Optional[str] = None,
                       task_id: Optional[str] = None, duration: Optional[float] = None,
                       error: Optional[str] = None) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event (run_started, run_completed, task_executed, etc.)
            user: User who performed the action
            host: Host affected by the action
            action: Action performed
            status: Status of the action (success, failed, skipped)
            details: Additional details about the event
            run_id: Associated run ID
            task_id: Associated task ID
            duration: Duration of the action
            error: Error message if applicable
            
        Returns:
            Event ID
        """
        event_id = self._generate_event_id()
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            user=user,
            host=host,
            action=action,
            status=status,
            details=details,
            run_id=run_id,
            task_id=task_id,
            duration=duration,
            error=error
        )
        
        try:
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO audit_events 
                    (event_id, timestamp, event_type, user, host, action, status, 
                     details, run_id, task_id, duration, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.user,
                    event.host,
                    event.action,
                    event.status,
                    json.dumps(event.details),
                    event.run_id,
                    event.task_id,
                    event.duration,
                    event.error
                ))
                
                conn.commit()
                
            self.logger.debug(f"Audit event logged: {event_id}")
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            raise
    
    async def log_task_execution(self, host: Dict[str, Any], task_config: Dict[str, Any], 
                                task_result: Any, run_id: str) -> str:
        """
        Log a task execution
        
        Args:
            host: Host information
            task_config: Task configuration
            task_result: Task result
            run_id: Run ID
            
        Returns:
            Task ID
        """
        task_id = self._generate_task_id()
        
        execution = TaskExecution(
            task_id=task_id,
            run_id=run_id,
            host=host.get('ansible_host', host.get('name', 'unknown')),
            task_name=task_config.get('name', 'unnamed_task'),
            task_type=task_config.get('task', 'command'),
            start_time=task_result.start_time,
            end_time=task_result.end_time,
            duration=task_result.duration,
            status=task_result.status,
            output=task_result.output,
            error=task_result.error,
            changed=task_result.changed,
            facts=task_result.facts or {}
        )
        
        try:
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO task_executions 
                    (task_id, run_id, host, task_name, task_type, start_time, end_time, 
                     duration, status, output, error, changed, facts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.task_id,
                    execution.run_id,
                    execution.host,
                    execution.task_name,
                    execution.task_type,
                    execution.start_time.isoformat(),
                    execution.end_time.isoformat(),
                    execution.duration,
                    execution.status,
                    execution.output,
                    execution.error,
                    execution.changed,
                    json.dumps(execution.facts)
                ))
                
                conn.commit()
                
            self.logger.debug(f"Task execution logged: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to log task execution: {e}")
            raise
    
    async def get_events(self, start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None,
                        event_type: Optional[str] = None,
                        user: Optional[str] = None,
                        host: Optional[str] = None,
                        run_id: Optional[str] = None,
                        limit: int = 1000) -> List[AuditEvent]:
        """
        Get audit events with filters
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            event_type: Event type filter
            user: User filter
            host: Host filter
            run_id: Run ID filter
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        try:
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = "SELECT * FROM audit_events WHERE 1=1"
                params = []
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                if user:
                    query += " AND user = ?"
                    params.append(user)
                
                if host:
                    query += " AND host = ?"
                    params.append(host)
                
                if run_id:
                    query += " AND run_id = ?"
                    params.append(run_id)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for row in rows:
                    event = AuditEvent(
                        event_id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        event_type=row[2],
                        user=row[3],
                        host=row[4],
                        action=row[5],
                        status=row[6],
                        details=json.loads(row[7]),
                        run_id=row[8],
                        task_id=row[9],
                        duration=row[10],
                        error=row[11]
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            self.logger.error(f"Failed to get audit events: {e}")
            return []
    
    async def get_task_executions(self, run_id: Optional[str] = None,
                                 host: Optional[str] = None,
                                 status: Optional[str] = None,
                                 limit: int = 1000) -> List[TaskExecution]:
        """
        Get task executions with filters
        
        Args:
            run_id: Run ID filter
            host: Host filter
            status: Status filter
            limit: Maximum number of executions to return
            
        Returns:
            List of task executions
        """
        try:
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = "SELECT * FROM task_executions WHERE 1=1"
                params = []
                
                if run_id:
                    query += " AND run_id = ?"
                    params.append(run_id)
                
                if host:
                    query += " AND host = ?"
                    params.append(host)
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY start_time DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                executions = []
                for row in rows:
                    execution = TaskExecution(
                        task_id=row[0],
                        run_id=row[1],
                        host=row[2],
                        task_name=row[3],
                        task_type=row[4],
                        start_time=datetime.fromisoformat(row[5]),
                        end_time=datetime.fromisoformat(row[6]),
                        duration=row[7],
                        status=row[8],
                        output=row[9],
                        error=row[10],
                        changed=bool(row[11]),
                        facts=json.loads(row[12]) if row[12] else {}
                    )
                    executions.append(execution)
                
                return executions
                
        except Exception as e:
            self.logger.error(f"Failed to get task executions: {e}")
            return []
    
    async def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Get summary of a run
        
        Args:
            run_id: Run ID
            
        Returns:
            Run summary
        """
        try:
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                # Get run events
                cursor.execute("""
                    SELECT event_type, status, COUNT(*) as count
                    FROM audit_events 
                    WHERE run_id = ?
                    GROUP BY event_type, status
                """, (run_id,))
                
                event_counts = {}
                for row in cursor.fetchall():
                    event_type, status, count = row
                    if event_type not in event_counts:
                        event_counts[event_type] = {}
                    event_counts[event_type][status] = count
                
                # Get task executions
                cursor.execute("""
                    SELECT status, COUNT(*) as count, AVG(duration) as avg_duration
                    FROM task_executions 
                    WHERE run_id = ?
                    GROUP BY status
                """, (run_id,))
                
                task_counts = {}
                for row in cursor.fetchall():
                    status, count, avg_duration = row
                    task_counts[status] = {
                        'count': count,
                        'avg_duration': avg_duration
                    }
                
                # Get run duration
                cursor.execute("""
                    SELECT MIN(timestamp) as start_time, MAX(timestamp) as end_time
                    FROM audit_events 
                    WHERE run_id = ?
                """, (run_id,))
                
                row = cursor.fetchone()
                start_time = datetime.fromisoformat(row[0]) if row[0] else None
                end_time = datetime.fromisoformat(row[1]) if row[1] else None
                
                duration = None
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds()
                
                return {
                    'run_id': run_id,
                    'start_time': start_time.isoformat() if start_time else None,
                    'end_time': end_time.isoformat() if end_time else None,
                    'duration': duration,
                    'event_counts': event_counts,
                    'task_counts': task_counts
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get run summary: {e}")
            return {}
    
    async def generate_audit_report(self, start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None,
                                   format: str = 'json') -> Union[Dict[str, Any], str]:
        """
        Generate audit report
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            format: Report format (json, markdown, html)
            
        Returns:
            Audit report
        """
        try:
            # Get events
            events = await self.get_events(start_time, end_time, limit=10000)
            
            # Get task executions
            task_executions = await self.get_task_executions(limit=10000)
            
            # Generate summary statistics
            total_events = len(events)
            total_tasks = len(task_executions)
            
            # Count by status
            event_status_counts = {}
            for event in events:
                status = event.status
                event_status_counts[status] = event_status_counts.get(status, 0) + 1
            
            task_status_counts = {}
            for execution in task_executions:
                status = execution.status
                task_status_counts[status] = task_status_counts.get(status, 0) + 1
            
            # Count by user
            user_counts = {}
            for event in events:
                user = event.user
                user_counts[user] = user_counts.get(user, 0) + 1
            
            # Count by host
            host_counts = {}
            for event in events:
                host = event.host
                host_counts[host] = host_counts.get(host, 0) + 1
            
            # Count by event type
            event_type_counts = {}
            for event in events:
                event_type = event.event_type
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Calculate average task duration
            avg_task_duration = 0
            if task_executions:
                total_duration = sum(execution.duration for execution in task_executions)
                avg_task_duration = total_duration / len(task_executions)
            
            # Generate report data
            report_data = {
                'report_generated': datetime.now().isoformat(),
                'period': {
                    'start_time': start_time.isoformat() if start_time else None,
                    'end_time': end_time.isoformat() if end_time else None
                },
                'summary': {
                    'total_events': total_events,
                    'total_tasks': total_tasks,
                    'avg_task_duration': avg_task_duration
                },
                'event_status_counts': event_status_counts,
                'task_status_counts': task_status_counts,
                'user_counts': user_counts,
                'host_counts': host_counts,
                'event_type_counts': event_type_counts,
                'events': [asdict(event) for event in events],
                'task_executions': [asdict(execution) for execution in task_executions]
            }
            
            if format == 'json':
                return report_data
            elif format == 'markdown':
                return self._generate_markdown_report(report_data)
            elif format == 'html':
                return self._generate_html_report(report_data)
            else:
                raise ValueError(f"Unsupported report format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate audit report: {e}")
            return {}
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown audit report"""
        md = f"""# Siemply Audit Report

**Generated:** {report_data['report_generated']}  
**Period:** {report_data['period']['start_time']} to {report_data['period']['end_time']}

## Summary

- **Total Events:** {report_data['summary']['total_events']}
- **Total Tasks:** {report_data['summary']['total_tasks']}
- **Average Task Duration:** {report_data['summary']['avg_task_duration']:.2f} seconds

## Event Status Distribution

"""
        
        for status, count in report_data['event_status_counts'].items():
            md += f"- **{status.title()}:** {count}\n"
        
        md += "\n## Task Status Distribution\n\n"
        
        for status, count in report_data['task_status_counts'].items():
            md += f"- **{status.title()}:** {count}\n"
        
        md += "\n## User Activity\n\n"
        
        for user, count in report_data['user_counts'].items():
            md += f"- **{user}:** {count} events\n"
        
        md += "\n## Host Activity\n\n"
        
        for host, count in report_data['host_counts'].items():
            md += f"- **{host}:** {count} events\n"
        
        md += "\n## Event Types\n\n"
        
        for event_type, count in report_data['event_type_counts'].items():
            md += f"- **{event_type}:** {count}\n"
        
        return md
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML audit report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Siemply Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .summary {{ display: flex; gap: 20px; }}
        .summary-item {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Siemply Audit Report</h1>
        <p><strong>Generated:</strong> {report_data['report_generated']}</p>
        <p><strong>Period:</strong> {report_data['period']['start_time']} to {report_data['period']['end_time']}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="summary">
            <div class="summary-item">
                <h3>{report_data['summary']['total_events']}</h3>
                <p>Total Events</p>
            </div>
            <div class="summary-item">
                <h3>{report_data['summary']['total_tasks']}</h3>
                <p>Total Tasks</p>
            </div>
            <div class="summary-item">
                <h3>{report_data['summary']['avg_task_duration']:.2f}s</h3>
                <p>Avg Task Duration</p>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Event Status Distribution</h2>
        <table>
            <tr><th>Status</th><th>Count</th></tr>
"""
        
        for status, count in report_data['event_status_counts'].items():
            html += f"            <tr><td class='{status}'>{status.title()}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Task Status Distribution</h2>
        <table>
            <tr><th>Status</th><th>Count</th></tr>
"""
        
        for status, count in report_data['task_status_counts'].items():
            html += f"            <tr><td class='{status}'>{status.title()}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>User Activity</h2>
        <table>
            <tr><th>User</th><th>Events</th></tr>
"""
        
        for user, count in report_data['user_counts'].items():
            html += f"            <tr><td>{user}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Host Activity</h2>
        <table>
            <tr><th>Host</th><th>Events</th></tr>
"""
        
        for host, count in report_data['host_counts'].items():
            html += f"            <tr><td>{host}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Event Types</h2>
        <table>
            <tr><th>Event Type</th><th>Count</th></tr>
"""
        
        for event_type, count in report_data['event_type_counts'].items():
            html += f"            <tr><td>{event_type}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
    </div>
</body>
</html>"""
        
        return html
    
    async def cleanup_old_events(self, days: int = 90):
        """Clean up old audit events"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            with sqlite3.connect(self.audit_db) as conn:
                cursor = conn.cursor()
                
                # Delete old events
                cursor.execute("DELETE FROM audit_events WHERE timestamp < ?", (cutoff_iso,))
                events_deleted = cursor.rowcount
                
                # Delete old task executions
                cursor.execute("DELETE FROM task_executions WHERE start_time < ?", (cutoff_iso,))
                tasks_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Cleaned up {events_deleted} events and {tasks_deleted} task executions older than {days} days")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old events: {e}")
            raise
