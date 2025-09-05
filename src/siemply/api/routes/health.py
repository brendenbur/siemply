"""
Health API Routes - Health check endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from ...core.orchestrator import Orchestrator
from ...core.inventory import Inventory
from ...core.ssh_executor import SSHExecutor
from ...core.secrets import SecretsManager
from ..dependencies import get_orchestrator, get_inventory, get_secrets_manager


router = APIRouter()


# Pydantic models
class HealthCheckResponse(BaseModel):
    check_name: str
    status: str
    message: str
    duration: float
    details: Dict[str, Any]


class HostHealthResponse(BaseModel):
    host: str
    ip: str
    status: str
    checks: List[HealthCheckResponse]
    overall_status: str
    last_check: str


class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]
    hosts: List[HostHealthResponse]
    summary: Dict[str, Any]


@router.get("/", response_model=SystemHealthResponse)
async def get_system_health(
    orchestrator: Orchestrator = Depends(get_orchestrator),
    inventory: Inventory = Depends(get_inventory),
    secrets_manager: SecretsManager = Depends(get_secrets_manager)
):
    """Get overall system health"""
    try:
        # Check component health
        components = {
            "orchestrator": "healthy" if orchestrator else "unhealthy",
            "inventory": "healthy" if inventory else "unhealthy",
            "secrets_manager": "healthy" if secrets_manager else "unhealthy"
        }
        
        # Get all hosts
        hosts = inventory.get_all_hosts()
        
        # Check host health
        host_health = []
        for host in hosts:
            try:
                # Basic connectivity check
                ssh_executor = SSHExecutor(secrets_manager)
                start_time = datetime.now()
                
                # Test connection
                success = await ssh_executor.test_connection(host)
                duration = (datetime.now() - start_time).total_seconds()
                
                checks = [
                    HealthCheckResponse(
                        check_name="ssh_connectivity",
                        status="pass" if success else "fail",
                        message="SSH connection successful" if success else "SSH connection failed",
                        duration=duration,
                        details={"host": host.name, "ip": host.ansible_host}
                    )
                ]
                
                # Additional checks if SSH is working
                if success:
                    # Check Splunk service
                    try:
                        splunk_check = await ssh_executor.execute_command(
                            host, "sudo systemctl is-active splunk"
                        )
                        splunk_status = "pass" if splunk_check.returncode == 0 else "fail"
                        splunk_message = "Splunk service is running" if splunk_check.returncode == 0 else "Splunk service is not running"
                        
                        checks.append(HealthCheckResponse(
                            check_name="splunk_service",
                            status=splunk_status,
                            message=splunk_message,
                            duration=0.1,  # Quick check
                            details={"returncode": splunk_check.returncode}
                        ))
                    except Exception as e:
                        checks.append(HealthCheckResponse(
                            check_name="splunk_service",
                            status="fail",
                            message=f"Splunk service check failed: {str(e)}",
                            duration=0.0,
                            details={"error": str(e)}
                        ))
                    
                    # Check disk space
                    try:
                        disk_check = await ssh_executor.execute_command(
                            host, "df -h /opt/splunk | tail -1 | awk '{print $5}' | sed 's/%//'"
                        )
                        if disk_check.returncode == 0:
                            disk_usage = int(disk_check.stdout.strip())
                            disk_status = "pass" if disk_usage < 90 else "warn"
                            disk_message = f"Disk usage: {disk_usage}%" if disk_usage < 90 else f"Disk usage high: {disk_usage}%"
                        else:
                            disk_status = "fail"
                            disk_message = "Failed to check disk usage"
                            disk_usage = 0
                        
                        checks.append(HealthCheckResponse(
                            check_name="disk_space",
                            status=disk_status,
                            message=disk_message,
                            duration=0.1,
                            details={"usage_percent": disk_usage}
                        ))
                    except Exception as e:
                        checks.append(HealthCheckResponse(
                            check_name="disk_space",
                            status="fail",
                            message=f"Disk space check failed: {str(e)}",
                            duration=0.0,
                            details={"error": str(e)}
                        ))
                
                # Determine overall host status
                overall_status = "healthy"
                if not success:
                    overall_status = "unhealthy"
                elif any(check.status == "fail" for check in checks):
                    overall_status = "unhealthy"
                elif any(check.status == "warn" for check in checks):
                    overall_status = "warning"
                
                host_health.append(HostHealthResponse(
                    host=host.name,
                    ip=host.ansible_host,
                    status=overall_status,
                    checks=checks,
                    overall_status=overall_status,
                    last_check=datetime.now().isoformat()
                ))
                
            except Exception as e:
                # Host check failed
                host_health.append(HostHealthResponse(
                    host=host.name,
                    ip=host.ansible_host,
                    status="unhealthy",
                    checks=[
                        HealthCheckResponse(
                            check_name="host_check",
                            status="fail",
                            message=f"Host check failed: {str(e)}",
                            duration=0.0,
                            details={"error": str(e)}
                        )
                    ],
                    overall_status="unhealthy",
                    last_check=datetime.now().isoformat()
                ))
        
        # Calculate summary
        total_hosts = len(host_health)
        healthy_hosts = len([h for h in host_health if h.overall_status == "healthy"])
        warning_hosts = len([h for h in host_health if h.overall_status == "warning"])
        unhealthy_hosts = len([h for h in host_health if h.overall_status == "unhealthy"])
        
        # Determine overall system status
        if unhealthy_hosts > 0:
            system_status = "unhealthy"
        elif warning_hosts > 0:
            system_status = "warning"
        else:
            system_status = "healthy"
        
        summary = {
            "total_hosts": total_hosts,
            "healthy_hosts": healthy_hosts,
            "warning_hosts": warning_hosts,
            "unhealthy_hosts": unhealthy_hosts,
            "health_percentage": (healthy_hosts / total_hosts * 100) if total_hosts > 0 else 0
        }
        
        return SystemHealthResponse(
            status=system_status,
            timestamp=datetime.now().isoformat(),
            components=components,
            hosts=host_health,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/hosts/{host_name}", response_model=HostHealthResponse)
async def get_host_health(
    host_name: str,
    inventory: Inventory = Depends(get_inventory),
    secrets_manager: SecretsManager = Depends(get_secrets_manager)
):
    """Get health status for a specific host"""
    try:
        # Get host
        host = inventory.get_host(host_name)
        if not host:
            raise HTTPException(status_code=404, detail=f"Host '{host_name}' not found")
        
        # Check host health
        ssh_executor = SSHExecutor(secrets_manager)
        start_time = datetime.now()
        
        # Test connection
        success = await ssh_executor.test_connection(host)
        duration = (datetime.now() - start_time).total_seconds()
        
        checks = [
            HealthCheckResponse(
                check_name="ssh_connectivity",
                status="pass" if success else "fail",
                message="SSH connection successful" if success else "SSH connection failed",
                duration=duration,
                details={"host": host.name, "ip": host.ansible_host}
            )
        ]
        
        # Additional checks if SSH is working
        if success:
            # Check Splunk service
            try:
                splunk_check = await ssh_executor.execute_command(
                    host, "sudo systemctl is-active splunk"
                )
                splunk_status = "pass" if splunk_check.returncode == 0 else "fail"
                splunk_message = "Splunk service is running" if splunk_check.returncode == 0 else "Splunk service is not running"
                
                checks.append(HealthCheckResponse(
                    check_name="splunk_service",
                    status=splunk_status,
                    message=splunk_message,
                    duration=0.1,
                    details={"returncode": splunk_check.returncode}
                ))
            except Exception as e:
                checks.append(HealthCheckResponse(
                    check_name="splunk_service",
                    status="fail",
                    message=f"Splunk service check failed: {str(e)}",
                    duration=0.0,
                    details={"error": str(e)}
                ))
            
            # Check disk space
            try:
                disk_check = await ssh_executor.execute_command(
                    host, "df -h /opt/splunk | tail -1 | awk '{print $5}' | sed 's/%//'"
                )
                if disk_check.returncode == 0:
                    disk_usage = int(disk_check.stdout.strip())
                    disk_status = "pass" if disk_usage < 90 else "warn"
                    disk_message = f"Disk usage: {disk_usage}%" if disk_usage < 90 else f"Disk usage high: {disk_usage}%"
                else:
                    disk_status = "fail"
                    disk_message = "Failed to check disk usage"
                    disk_usage = 0
                
                checks.append(HealthCheckResponse(
                    check_name="disk_space",
                    status=disk_status,
                    message=disk_message,
                    duration=0.1,
                    details={"usage_percent": disk_usage}
                ))
            except Exception as e:
                checks.append(HealthCheckResponse(
                    check_name="disk_space",
                    status="fail",
                    message=f"Disk space check failed: {str(e)}",
                    duration=0.0,
                    details={"error": str(e)}
                ))
        
        # Determine overall host status
        overall_status = "healthy"
        if not success:
            overall_status = "unhealthy"
        elif any(check.status == "fail" for check in checks):
            overall_status = "unhealthy"
        elif any(check.status == "warn" for check in checks):
            overall_status = "warning"
        
        return HostHealthResponse(
            host=host.name,
            ip=host.ansible_host,
            status=overall_status,
            checks=checks,
            overall_status=overall_status,
            last_check=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get host health: {str(e)}")


@router.post("/hosts/{host_name}/check")
async def run_host_health_check(
    host_name: str,
    check_types: Optional[List[str]] = Query(None, description="Specific checks to run"),
    inventory: Inventory = Depends(get_inventory),
    secrets_manager: SecretsManager = Depends(get_secrets_manager)
):
    """Run health checks on a specific host"""
    try:
        # Get host
        host = inventory.get_host(host_name)
        if not host:
            raise HTTPException(status_code=404, detail=f"Host '{host_name}' not found")
        
        # Run checks
        ssh_executor = SSHExecutor(secrets_manager)
        checks = []
        
        # Default checks if none specified
        if not check_types:
            check_types = ["ssh_connectivity", "splunk_service", "disk_space"]
        
        for check_type in check_types:
            try:
                if check_type == "ssh_connectivity":
                    start_time = datetime.now()
                    success = await ssh_executor.test_connection(host)
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    checks.append(HealthCheckResponse(
                        check_name="ssh_connectivity",
                        status="pass" if success else "fail",
                        message="SSH connection successful" if success else "SSH connection failed",
                        duration=duration,
                        details={"host": host.name, "ip": host.ansible_host}
                    ))
                
                elif check_type == "splunk_service":
                    try:
                        splunk_check = await ssh_executor.execute_command(
                            host, "sudo systemctl is-active splunk"
                        )
                        splunk_status = "pass" if splunk_check.returncode == 0 else "fail"
                        splunk_message = "Splunk service is running" if splunk_check.returncode == 0 else "Splunk service is not running"
                        
                        checks.append(HealthCheckResponse(
                            check_name="splunk_service",
                            status=splunk_status,
                            message=splunk_message,
                            duration=0.1,
                            details={"returncode": splunk_check.returncode}
                        ))
                    except Exception as e:
                        checks.append(HealthCheckResponse(
                            check_name="splunk_service",
                            status="fail",
                            message=f"Splunk service check failed: {str(e)}",
                            duration=0.0,
                            details={"error": str(e)}
                        ))
                
                elif check_type == "disk_space":
                    try:
                        disk_check = await ssh_executor.execute_command(
                            host, "df -h /opt/splunk | tail -1 | awk '{print $5}' | sed 's/%//'"
                        )
                        if disk_check.returncode == 0:
                            disk_usage = int(disk_check.stdout.strip())
                            disk_status = "pass" if disk_usage < 90 else "warn"
                            disk_message = f"Disk usage: {disk_usage}%" if disk_usage < 90 else f"Disk usage high: {disk_usage}%"
                        else:
                            disk_status = "fail"
                            disk_message = "Failed to check disk usage"
                            disk_usage = 0
                        
                        checks.append(HealthCheckResponse(
                            check_name="disk_space",
                            status=disk_status,
                            message=disk_message,
                            duration=0.1,
                            details={"usage_percent": disk_usage}
                        ))
                    except Exception as e:
                        checks.append(HealthCheckResponse(
                            check_name="disk_space",
                            status="fail",
                            message=f"Disk space check failed: {str(e)}",
                            duration=0.0,
                            details={"error": str(e)}
                        ))
                
                else:
                    checks.append(HealthCheckResponse(
                        check_name=check_type,
                        status="fail",
                        message=f"Unknown check type: {check_type}",
                        duration=0.0,
                        details={"error": "Unknown check type"}
                    ))
                    
            except Exception as e:
                checks.append(HealthCheckResponse(
                    check_name=check_type,
                    status="fail",
                    message=f"Check failed: {str(e)}",
                    duration=0.0,
                    details={"error": str(e)}
                ))
        
        # Determine overall status
        overall_status = "healthy"
        if any(check.status == "fail" for check in checks):
            overall_status = "unhealthy"
        elif any(check.status == "warn" for check in checks):
            overall_status = "warning"
        
        return {
            "host": host.name,
            "ip": host.ansible_host,
            "status": overall_status,
            "checks": checks,
            "overall_status": overall_status,
            "last_check": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run host health check: {str(e)}")
