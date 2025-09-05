"""
Enhanced FastAPI application with Host Management
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from ..database.database import create_tables
from .routes import hosts_new, playbooks_new, runs_new


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Siemply Host Management API...")
    
    # Create database tables
    create_tables()
    print("✅ Database tables created")
    
    # Initialize sample data if needed
    from ..database.database import SessionLocal
    from ..database.models import Host, Playbook
    from ..playbooks.schema import SAMPLE_PLAYBOOKS
    import yaml
    
    db = SessionLocal()
    try:
        # Check if we have any hosts
        host_count = db.query(Host).count()
        if host_count == 0:
            print("📝 No hosts found - ready for first host addition")
        
        # Check if we have any playbooks
        playbook_count = db.query(Playbook).count()
        if playbook_count == 0:
            print("📝 No playbooks found - ready for first playbook creation")
        
        # Create sample playbooks if none exist
        if playbook_count == 0:
            for sample_name, sample_data in SAMPLE_PLAYBOOKS.items():
                yaml_content = yaml.dump(sample_data, default_flow_style=False)
                playbook = Playbook(
                    name=sample_data["name"],
                    description=sample_data.get("description"),
                    yaml_content=yaml_content
                )
                db.add(playbook)
            db.commit()
            print("✅ Sample playbooks created")
        
    finally:
        db.close()
    
    print("✅ Siemply Host Management API ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Siemply Host Management API...")


# Create FastAPI app
app = FastAPI(
    title="Siemply Host Management API",
    description="Enhanced host management and playbook execution for Splunk infrastructure",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hosts_new.router, prefix="/api/hosts", tags=["hosts"])
app.include_router(playbooks_new.router, prefix="/api/playbooks", tags=["playbooks"])
app.include_router(runs_new.router, prefix="/api/runs", tags=["runs"])

# Mount static files
if os.path.exists("web/build/static"):
    app.mount("/static", StaticFiles(directory="web/build/static"), name="static")
elif os.path.exists("web/static"):
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Serve React app
@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React application"""
    try:
        if os.path.exists("web/build/index.html"):
            with open("web/build/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        elif os.path.exists("web/index.html"):
            with open("web/index.html", "r") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Siemply Host Management</title>
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
                        <h1>🚀 Siemply Host Management</h1>
                        <p>Enhanced host management and playbook execution for Splunk infrastructure</p>
                    </div>
                    <div class="content">
                        <h2>API Endpoints</h2>
                        <a href="/docs" class="api-link">API Documentation</a>
                        <a href="/api/hosts" class="api-link">Hosts API</a>
                        <a href="/api/playbooks" class="api-link">Playbooks API</a>
                        <a href="/api/runs" class="api-link">Runs API</a>
                    </div>
                </div>
            </body>
            </html>
            """)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Siemply Host Management API</h1><p>API is running. Check <a href='/docs'>/docs</a> for documentation.</p>")


@app.get("/api/status")
async def get_status():
    """Get API status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["host_management", "playbook_execution", "ssh_connectivity"],
        "components": {
            "database": "connected",
            "ssh_runner": "ready",
            "playbook_engine": "ready"
        }
    }
