"""
API Dependencies - Dependency injection functions
"""

from fastapi import HTTPException
from ..core.orchestrator import Orchestrator
from ..core.inventory import Inventory
from ..core.audit import AuditLogger
from ..core.secrets import SecretsManager

# Global instances (will be initialized in main.py)
orchestrator: Orchestrator = None
inventory: Inventory = None
audit_logger: AuditLogger = None
secrets_manager: SecretsManager = None


def set_instances(orch, inv, audit, secrets):
    """Set the global instances"""
    global orchestrator, inventory, audit_logger, secrets_manager
    orchestrator = orch
    inventory = inv
    audit_logger = audit
    secrets_manager = secrets


async def get_orchestrator() -> Orchestrator:
    """Get orchestrator instance"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator


async def get_inventory() -> Inventory:
    """Get inventory instance"""
    if not inventory:
        raise HTTPException(status_code=503, detail="Inventory not initialized")
    return inventory


async def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger not initialized")
    return audit_logger


async def get_secrets_manager() -> SecretsManager:
    """Get secrets manager instance"""
    if not secrets_manager:
        raise HTTPException(status_code=503, detail="Secrets manager not initialized")
    return secrets_manager
