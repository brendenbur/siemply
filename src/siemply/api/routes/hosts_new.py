"""
Enhanced Host Management API routes
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.database import get_db
from ...database.models import Host, HostStatus, AuthType
from ...ssh.runner import SSHManager

router = APIRouter()


# Pydantic models for API
class HostCreate(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    ip: str = Field(..., min_length=1, max_length=45)
    port: int = Field(22, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=100)
    auth_type: str = Field(..., regex="^(key|password)$")
    private_key: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    password: Optional[str] = None
    labels: List[str] = Field(default_factory=list)


class HostUpdate(BaseModel):
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip: Optional[str] = Field(None, min_length=1, max_length=45)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    auth_type: Optional[str] = Field(None, regex="^(key|password)$")
    private_key: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    password: Optional[str] = None
    labels: Optional[List[str]] = None


class HostResponse(BaseModel):
    id: str
    hostname: str
    ip: str
    port: int
    username: str
    auth_type: str
    labels: List[str]
    last_seen: Optional[str]
    status: str
    created_at: str
    updated_at: str


class TestSSHRequest(BaseModel):
    host_ids: List[str]


class TestSSHResponse(BaseModel):
    host_id: str
    hostname: str
    success: bool
    message: str


@router.get("/", response_model=List[HostResponse])
async def list_hosts(
    search: Optional[str] = Query(None, description="Search by hostname or IP"),
    label: Optional[str] = Query(None, description="Filter by label"),
    db: Session = Depends(get_db)
):
    """List all hosts with optional search and filter"""
    query = db.query(Host)
    
    if search:
        query = query.filter(
            (Host.hostname.contains(search)) | 
            (Host.ip.contains(search))
        )
    
    if label:
        query = query.filter(Host.labels.contains([label]))
    
    hosts = query.all()
    return [HostResponse(**host.to_dict()) for host in hosts]


@router.post("/", response_model=HostResponse)
async def create_host(host_data: HostCreate, db: Session = Depends(get_db)):
    """Create a new host"""
    
    # Check if hostname already exists
    existing = db.query(Host).filter(Host.hostname == host_data.hostname).first()
    if existing:
        raise HTTPException(status_code=400, detail="Hostname already exists")
    
    # Validate authentication data
    if host_data.auth_type == "key" and not host_data.private_key:
        raise HTTPException(status_code=400, detail="Private key required for key authentication")
    if host_data.auth_type == "password" and not host_data.password:
        raise HTTPException(status_code=400, detail="Password required for password authentication")
    
    # Create host
    host = Host(
        hostname=host_data.hostname,
        ip=host_data.ip,
        port=host_data.port,
        username=host_data.username,
        auth_type=host_data.auth_type,
        labels=host_data.labels
    )
    
    # Set authentication data
    if host_data.auth_type == "key":
        host.set_private_key(host_data.private_key)
        if host_data.private_key_passphrase:
            host.set_private_key_passphrase(host_data.private_key_passphrase)
    else:
        host.set_password(host_data.password)
    
    db.add(host)
    db.commit()
    db.refresh(host)
    
    return HostResponse(**host.to_dict())


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: str, db: Session = Depends(get_db)):
    """Get a specific host"""
    try:
        host_uuid = uuid.UUID(host_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID")
    
    host = db.query(Host).filter(Host.id == host_uuid).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    return HostResponse(**host.to_dict())


@router.put("/{host_id}", response_model=HostResponse)
async def update_host(host_id: str, host_data: HostUpdate, db: Session = Depends(get_db)):
    """Update a host"""
    try:
        host_uuid = uuid.UUID(host_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID")
    
    host = db.query(Host).filter(Host.id == host_uuid).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Update fields
    if host_data.hostname is not None:
        # Check if new hostname already exists
        existing = db.query(Host).filter(
            Host.hostname == host_data.hostname,
            Host.id != host_uuid
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Hostname already exists")
        host.hostname = host_data.hostname
    
    if host_data.ip is not None:
        host.ip = host_data.ip
    if host_data.port is not None:
        host.port = host_data.port
    if host_data.username is not None:
        host.username = host_data.username
    if host_data.auth_type is not None:
        host.auth_type = host_data.auth_type
    if host_data.labels is not None:
        host.labels = host_data.labels
    
    # Update authentication data
    if host_data.private_key is not None:
        host.set_private_key(host_data.private_key)
    if host_data.private_key_passphrase is not None:
        host.set_private_key_passphrase(host_data.private_key_passphrase)
    if host_data.password is not None:
        host.set_password(host_data.password)
    
    db.commit()
    db.refresh(host)
    
    return HostResponse(**host.to_dict())


@router.delete("/{host_id}")
async def delete_host(host_id: str, db: Session = Depends(get_db)):
    """Delete a host"""
    try:
        host_uuid = uuid.UUID(host_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID")
    
    host = db.query(Host).filter(Host.id == host_uuid).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    db.delete(host)
    db.commit()
    
    return {"message": "Host deleted successfully"}


@router.post("/{host_id}/test-ssh", response_model=TestSSHResponse)
async def test_host_ssh(host_id: str, db: Session = Depends(get_db)):
    """Test SSH connectivity to a specific host"""
    try:
        host_uuid = uuid.UUID(host_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID")
    
    host = db.query(Host).filter(Host.id == host_uuid).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    # Test SSH connection
    success, message = SSHManager.test_host(
        host.hostname, host.port, host.username, host.auth_type,
        host.get_private_key(), host.get_private_key_passphrase(),
        host.get_password()
    )
    
    # Update host status
    host.status = HostStatus.REACHABLE if success else HostStatus.UNREACHABLE
    if success:
        from datetime import datetime
        host.last_seen = datetime.utcnow()
    
    db.commit()
    
    return TestSSHResponse(
        host_id=host_id,
        hostname=host.hostname,
        success=success,
        message=message
    )


@router.post("/test-ssh-bulk", response_model=List[TestSSHResponse])
async def test_hosts_ssh_bulk(request: TestSSHRequest, db: Session = Depends(get_db)):
    """Test SSH connectivity to multiple hosts"""
    try:
        host_uuids = [uuid.UUID(host_id) for host_id in request.host_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid host ID in list")
    
    hosts = db.query(Host).filter(Host.id.in_(host_uuids)).all()
    if not hosts:
        raise HTTPException(status_code=404, detail="No hosts found")
    
    results = []
    for host in hosts:
        success, message = SSHManager.test_host(
            host.hostname, host.port, host.username, host.auth_type,
            host.get_private_key(), host.get_private_key_passphrase(),
            host.get_password()
        )
        
        # Update host status
        host.status = HostStatus.REACHABLE if success else HostStatus.UNREACHABLE
        if success:
            from datetime import datetime
            host.last_seen = datetime.utcnow()
        
        results.append(TestSSHResponse(
            host_id=str(host.id),
            hostname=host.hostname,
            success=success,
            message=message
        ))
    
    db.commit()
    return results
