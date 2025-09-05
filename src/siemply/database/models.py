"""
SQLAlchemy models for Siemply Host Management
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from .encryption import encrypt_value, decrypt_value

Base = declarative_base()


class AuthType(str, Enum):
    KEY = "key"
    PASSWORD = "password"


class HostStatus(str, Enum):
    UNKNOWN = "unknown"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"


class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Host(Base):
    __tablename__ = "hosts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname = Column(String(255), unique=True, nullable=False, index=True)
    ip = Column(String(45), nullable=False)  # IPv4/IPv6
    port = Column(Integer, default=22, nullable=False)
    username = Column(String(100), nullable=False)
    auth_type = Column(String(20), nullable=False)  # AuthType enum
    private_key = Column(Text, nullable=True)  # Encrypted
    private_key_passphrase = Column(Text, nullable=True)  # Encrypted
    password = Column(Text, nullable=True)  # Encrypted
    labels = Column(JSON, default=list)  # List of strings
    last_seen = Column(DateTime, nullable=True)
    status = Column(String(20), default=HostStatus.UNKNOWN)  # HostStatus enum
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("Run", back_populates="hosts")

    def set_private_key(self, key: str) -> None:
        """Encrypt and store private key"""
        self.private_key = encrypt_value(key) if key else None

    def get_private_key(self) -> Optional[str]:
        """Decrypt and return private key"""
        return decrypt_value(self.private_key) if self.private_key else None

    def set_private_key_passphrase(self, passphrase: str) -> None:
        """Encrypt and store private key passphrase"""
        self.private_key_passphrase = encrypt_value(passphrase) if passphrase else None

    def get_private_key_passphrase(self) -> Optional[str]:
        """Decrypt and return private key passphrase"""
        return decrypt_value(self.private_key_passphrase) if self.private_key_passphrase else None

    def set_password(self, password: str) -> None:
        """Encrypt and store password"""
        self.password = encrypt_value(password) if password else None

    def get_password(self) -> Optional[str]:
        """Decrypt and return password"""
        return decrypt_value(self.password) if self.password else None

    def to_dict(self, include_secrets: bool = False) -> dict:
        """Convert to dictionary, optionally including secrets"""
        data = {
            "id": str(self.id),
            "hostname": self.hostname,
            "ip": self.ip,
            "port": self.port,
            "username": self.username,
            "auth_type": self.auth_type,
            "labels": self.labels or [],
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_secrets:
            data.update({
                "private_key": self.get_private_key(),
                "private_key_passphrase": self.get_private_key_passphrase(),
                "password": self.get_password(),
            })
        
        return data


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    yaml_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("Run", back_populates="playbook")

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "yaml_content": self.yaml_content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id"), nullable=False)
    host_ids = Column(JSON, nullable=False)  # List of UUIDs
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), default=RunStatus.RUNNING)  # RunStatus enum
    logs = Column(JSON, default=list)  # List of log entries
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    playbook = relationship("Playbook", back_populates="runs")
    hosts = relationship("Host", secondary="run_hosts", back_populates="runs")

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "playbook_id": str(self.playbook_id),
            "host_ids": self.host_ids,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "logs": self.logs or [],
            "created_at": self.created_at.isoformat(),
        }

    def add_log(self, host_id: str, level: str, message: str) -> None:
        """Add a log entry"""
        if not self.logs:
            self.logs = []
        
        log_entry = {
            "host_id": host_id,
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        self.logs.append(log_entry)


# Association table for many-to-many relationship between runs and hosts
from sqlalchemy import Table

run_hosts = Table(
    "run_hosts",
    Base.metadata,
    Column("run_id", UUID(as_uuid=True), ForeignKey("runs.id"), primary_key=True),
    Column("host_id", UUID(as_uuid=True), ForeignKey("hosts.id"), primary_key=True),
)
