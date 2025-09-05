"""
Siemply Web API - Main FastAPI application
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .routes import hosts, runs, audit, health, websocket
from .dependencies import set_instances
from ..core.orchestrator import Orchestrator
from ..core.inventory import Inventory
from ..core.audit import AuditLogger
from ..core.secrets import SecretsManager


# Global orchestrator instance
orchestrator: Orchestrator = None
inventory: Inventory = None
audit_logger: AuditLogger = None
secrets_manager: SecretsManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator, inventory, audit_logger, secrets_manager
    
    # Startup
    logging.info("Starting Siemply Web API...")
    
    try:
        # Initialize core components
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        
        inventory = Inventory()
        await inventory.load()
        
        audit_logger = AuditLogger()
        await audit_logger.initialize()
        
        secrets_manager = SecretsManager()
        await secrets_manager.load()
        
        # Set instances for dependency injection
        set_instances(orchestrator, inventory, audit_logger, secrets_manager)
        
        logging.info("Siemply Web API started successfully")
        
    except Exception as e:
        logging.error(f"Failed to start Siemply Web API: {e}")
        raise
    
    yield
    
    # Shutdown
    logging.info("Shutting down Siemply Web API...")
    if orchestrator:
        await orchestrator.ssh_executor.close_all_connections()
    logging.info("Siemply Web API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Siemply Web API",
    description="Web API for Splunk Infrastructure Orchestration Framework",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(hosts.router, prefix="/api/hosts", tags=["hosts"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Serve React app
@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React application"""
    try:
        with open("web/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Siemply Web Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .content { margin: 20px 0; }
                .api-link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Siemply Web Interface</h1>
                    <p>Splunk Infrastructure Orchestration Framework</p>
                </div>
                <div class="content">
                    <h2>API Endpoints</h2>
                    <a href="/docs" class="api-link">📚 API Documentation</a>
                    <a href="/api/health" class="api-link">❤️ Health Check</a>
                    <a href="/api/hosts" class="api-link">🖥️ Hosts</a>
                    <a href="/api/runs" class="api-link">🏃 Runs</a>
                    <a href="/api/audit" class="api-link">📊 Audit</a>
                    
                    <h2>Getting Started</h2>
                    <p>To use the full web interface, build the React frontend:</p>
                    <pre><code>cd web
npm install
npm run build</code></pre>
                </div>
            </div>
        </body>
        </html>
        """)


# Import dependency functions
from .dependencies import get_orchestrator, get_inventory, get_audit_logger, get_secrets_manager


# Health check endpoint
@app.get("/api/status")
async def get_status():
    """Get API status"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "orchestrator": orchestrator is not None,
            "inventory": inventory is not None,
            "audit_logger": audit_logger is not None,
            "secrets_manager": secrets_manager is not None
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "siemply.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
