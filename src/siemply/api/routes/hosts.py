"""
Hosts API Routes - Host management endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ...core.inventory import Inventory, Host
from ...core.ssh_executor import SSHExecutor
from ...core.secrets import SecretsManager
from ..dependencies import get_inventory, get_secrets_manager


router = APIRouter()


# Pydantic models
class HostCreate(BaseModel):
    name: str
    ip: str
    user: str = "splunk"
    port: int = 22
    key_file: Optional[str] = None
    group: Optional[str] = None
    splunk_type: Optional[str] = None
    splunk_version: Optional[str] = None
    os_family: Optional[str] = None
    os_version: Optional[str] = None
    cpu_arch: Optional[str] = None
    memory_gb: Optional[int] = None
    disk_gb: Optional[int] = None


class HostUpdate(BaseModel):
    ip: Optional[str] = None
    user: Optional[str] = None
    port: Optional[int] = None
    key_file: Optional[str] = None
    group: Optional[str] = None
    splunk_type: Optional[str] = None
    splunk_version: Optional[str] = None
    os_family: Optional[str] = None
    os_version: Optional[str] = None
    cpu_arch: Optional[str] = None
    memory_gb: Optional[int] = None
    disk_gb: Optional[int] = None


class HostResponse(BaseModel):
    name: str
    ip: str
    user: str
    port: int
    splunk_type: Optional[str]
    splunk_version: Optional[str]
    os_family: Optional[str]
    os_version: Optional[str]
    cpu_arch: Optional[str]
    memory_gb: Optional[int]
    disk_gb: Optional[int]
    status: Optional[str] = None
    last_seen: Optional[str] = None


class HostTestResult(BaseModel):
    host: str
    status: str
    message: str
    duration: float


@router.get("/", response_model=List[HostResponse])
async def list_hosts(
    group: Optional[str] = Query(None, description="Filter by group"),
    splunk_type: Optional[str] = Query(None, description="Filter by Splunk type"),
    os_family: Optional[str] = Query(None, description="Filter by OS family"),
    inventory: Inventory = Depends(get_inventory)
):
    """List all hosts with optional filters"""
    try:
        if group:
            hosts = inventory.get_group_hosts(group)
        else:
            hosts = inventory.get_all_hosts()
        
        # Apply filters
        if splunk_type:
            hosts = [h for h in hosts if h.splunk_type == splunk_type]
        if os_family:
            hosts = [h for h in hosts if h.os_family == os_family]
        
        # Convert to response format
        host_responses = []
        for host in hosts:
            host_responses.append(HostResponse(
                name=host.name,
                ip=host.ansible_host,
                user=host.ansible_user,
                port=host.ansible_port,
                splunk_type=host.splunk_type,
                splunk_version=host.splunk_version,
                os_family=host.os_family,
                os_version=host.os_version,
                cpu_arch=host.cpu_arch,
                memory_gb=host.memory_gb,
                disk_gb=host.disk_gb,
                status="unknown"
            ))
        
        return host_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list hosts: {str(e)}")


@router.get("/{host_name}", response_model=HostResponse)
async def get_host(
    host_name: str,
    inventory: Inventory = Depends(get_inventory)
):
    """Get a specific host by name"""
    try:
        host = inventory.get_host(host_name)
        if not host:
            raise HTTPException(status_code=404, detail=f"Host '{host_name}' not found")
        
        return HostResponse(
            name=host.name,
            ip=host.ansible_host,
            user=host.ansible_user,
            port=host.ansible_port,
            splunk_type=host.splunk_type,
            splunk_version=host.splunk_version,
            os_family=host.os_family,
            os_version=host.os_version,
            cpu_arch=host.cpu_arch,
            memory_gb=host.memory_gb,
            disk_gb=host.disk_gb,
            status="unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get host: {str(e)}")


@router.post("/", response_model=HostResponse)
async def create_host(
    host_data: HostCreate,
    inventory: Inventory = Depends(get_inventory)
):
    """Create a new host"""
    try:
        # Create host object
        host = Host(
            name=host_data.name,
            ansible_host=host_data.ip,
            ansible_user=host_data.user,
            ansible_port=host_data.port,
            ansible_ssh_private_key_file=host_data.key_file,
            splunk_type=host_data.splunk_type,
            splunk_version=host_data.splunk_version,
            os_family=host_data.os_family,
            os_version=host_data.os_version,
            cpu_arch=host_data.cpu_arch,
            memory_gb=host_data.memory_gb,
            disk_gb=host_data.disk_gb
        )
        
        # Add host to inventory
        if not inventory.add_host(host):
            raise HTTPException(status_code=400, detail="Failed to add host")
        
        return HostResponse(
            name=host.name,
            ip=host.ansible_host,
            user=host.ansible_user,
            port=host.ansible_port,
            splunk_type=host.splunk_type,
            splunk_version=host.splunk_version,
            os_family=host.os_family,
            os_version=host.os_version,
            cpu_arch=host.cpu_arch,
            memory_gb=host.memory_gb,
            disk_gb=host.disk_gb,
            status="unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create host: {str(e)}")


@router.put("/{host_name}", response_model=HostResponse)
async def update_host(
    host_name: str,
    host_data: HostUpdate,
    inventory: Inventory = Depends(get_inventory)
):
    """Update an existing host"""
    try:
        # Get existing host
        host = inventory.get_host(host_name)
        if not host:
            raise HTTPException(status_code=404, detail=f"Host '{host_name}' not found")
        
        # Prepare update data
        updates = {}
        if host_data.ip is not None:
            updates['ansible_host'] = host_data.ip
        if host_data.user is not None:
            updates['ansible_user'] = host_data.user
        if host_data.port is not None:
            updates['ansible_port'] = host_data.port
        if host_data.key_file is not None:
            updates['ansible_ssh_private_key_file'] = host_data.key_file
        if host_data.splunk_type is not None:
            updates['splunk_type'] = host_data.splunk_type
        if host_data.splunk_version is not None:
            updates['splunk_version'] = host_data.splunk_version
        if host_data.os_family is not None:
            updates['os_family'] = host_data.os_family
        if host_data.os_version is not None:
            updates['os_version'] = host_data.os_version
        if host_data.cpu_arch is not None:
            updates['cpu_arch'] = host_data.cpu_arch
        if host_data.memory_gb is not None:
            updates['memory_gb'] = host_data.memory_gb
        if host_data.disk_gb is not None:
            updates['disk_gb'] = host_data.disk_gb
        
        # Update host
        if not inventory.update_host(host_name, updates):
            raise HTTPException(status_code=400, detail="Failed to update host")
        
        # Get updated host
        updated_host = inventory.get_host(host_name)
        
        return HostResponse(
            name=updated_host.name,
            ip=updated_host.ansible_host,
            user=updated_host.ansible_user,
            port=updated_host.ansible_port,
            splunk_type=updated_host.splunk_type,
            splunk_version=updated_host.splunk_version,
            os_family=updated_host.os_family,
            os_version=updated_host.os_version,
            cpu_arch=updated_host.cpu_arch,
            memory_gb=updated_host.memory_gb,
            disk_gb=updated_host.disk_gb,
            status="unknown"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update host: {str(e)}")


@router.delete("/{host_name}")
async def delete_host(
    host_name: str,
    inventory: Inventory = Depends(get_inventory)
):
    """Delete a host"""
    try:
        if not inventory.remove_host(host_name):
            raise HTTPException(status_code=404, detail=f"Host '{host_name}' not found")
        
        return {"message": f"Host '{host_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete host: {str(e)}")


@router.post("/test", response_model=List[HostTestResult])
async def test_hosts(
    host_names: List[str],
    inventory: Inventory = Depends(get_inventory),
    secrets_manager: SecretsManager = Depends(get_secrets_manager)
):
    """Test SSH connectivity to hosts"""
    try:
        results = []
        ssh_executor = SSHExecutor(secrets_manager)
        
        for host_name in host_names:
            host = inventory.get_host(host_name)
            if not host:
                results.append(HostTestResult(
                    host=host_name,
                    status="error",
                    message="Host not found",
                    duration=0.0
                ))
                continue
            
            # Test connection
            import time
            start_time = time.time()
            
            try:
                success = await ssh_executor.test_connection(host)
                duration = time.time() - start_time
                
                if success:
                    results.append(HostTestResult(
                        host=host_name,
                        status="success",
                        message="Connection successful",
                        duration=duration
                    ))
                else:
                    results.append(HostTestResult(
                        host=host_name,
                        status="failed",
                        message="Connection failed",
                        duration=duration
                    ))
            except Exception as e:
                duration = time.time() - start_time
                results.append(HostTestResult(
                    host=host_name,
                    status="error",
                    message=str(e),
                    duration=duration
                ))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test hosts: {str(e)}")


@router.get("/groups/", response_model=List[str])
async def list_groups(
    inventory: Inventory = Depends(get_inventory)
):
    """List all groups"""
    try:
        groups = list(inventory.groups.keys())
        return groups
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {str(e)}")


@router.get("/groups/{group_name}/hosts", response_model=List[HostResponse])
async def get_group_hosts(
    group_name: str,
    inventory: Inventory = Depends(get_inventory)
):
    """Get all hosts in a group"""
    try:
        hosts = inventory.get_group_hosts(group_name)
        
        host_responses = []
        for host in hosts:
            host_responses.append(HostResponse(
                name=host.name,
                ip=host.ansible_host,
                user=host.ansible_user,
                port=host.ansible_port,
                splunk_type=host.splunk_type,
                splunk_version=host.splunk_version,
                os_family=host.os_family,
                os_version=host.os_version,
                cpu_arch=host.cpu_arch,
                memory_gb=host.memory_gb,
                disk_gb=host.disk_gb,
                status="unknown"
            ))
        
        return host_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group hosts: {str(e)}")


@router.get("/summary/", response_model=Dict[str, Any])
async def get_hosts_summary(
    inventory: Inventory = Depends(get_inventory)
):
    """Get hosts summary statistics"""
    try:
        summary = inventory.get_inventory_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hosts summary: {str(e)}")
