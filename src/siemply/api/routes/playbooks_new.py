"""
Playbook Management API routes
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.database import get_db
from ...database.models import Playbook
from ...playbooks.schema import validate_playbook_yaml, SAMPLE_PLAYBOOKS

router = APIRouter()


# Pydantic models for API
class PlaybookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    yaml_content: str = Field(..., min_length=1)


class PlaybookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    yaml_content: Optional[str] = Field(None, min_length=1)


class PlaybookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    yaml_content: str
    created_at: str
    updated_at: str


@router.get("/", response_model=List[PlaybookResponse])
async def list_playbooks(
    search: Optional[str] = Query(None, description="Search by name or description"),
    db: Session = Depends(get_db)
):
    """List all playbooks with optional search"""
    query = db.query(Playbook)
    
    if search:
        query = query.filter(
            (Playbook.name.contains(search)) | 
            (Playbook.description.contains(search))
        )
    
    playbooks = query.all()
    return [PlaybookResponse(**playbook.to_dict()) for playbook in playbooks]


@router.post("/", response_model=PlaybookResponse)
async def create_playbook(playbook_data: PlaybookCreate, db: Session = Depends(get_db)):
    """Create a new playbook"""
    
    # Check if name already exists
    existing = db.query(Playbook).filter(Playbook.name == playbook_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Playbook name already exists")
    
    # Validate YAML content
    is_valid, playbook_schema, error = validate_playbook_yaml(playbook_data.yaml_content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid playbook YAML: {error}")
    
    # Create playbook
    playbook = Playbook(
        name=playbook_data.name,
        description=playbook_data.description,
        yaml_content=playbook_data.yaml_content
    )
    
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    
    return PlaybookResponse(**playbook.to_dict())


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(playbook_id: str, db: Session = Depends(get_db)):
    """Get a specific playbook"""
    try:
        playbook_uuid = uuid.UUID(playbook_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playbook ID")
    
    playbook = db.query(Playbook).filter(Playbook.id == playbook_uuid).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    return PlaybookResponse(**playbook.to_dict())


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(playbook_id: str, playbook_data: PlaybookUpdate, db: Session = Depends(get_db)):
    """Update a playbook"""
    try:
        playbook_uuid = uuid.UUID(playbook_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playbook ID")
    
    playbook = db.query(Playbook).filter(Playbook.id == playbook_uuid).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    # Update fields
    if playbook_data.name is not None:
        # Check if new name already exists
        existing = db.query(Playbook).filter(
            Playbook.name == playbook_data.name,
            Playbook.id != playbook_uuid
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Playbook name already exists")
        playbook.name = playbook_data.name
    
    if playbook_data.description is not None:
        playbook.description = playbook_data.description
    
    if playbook_data.yaml_content is not None:
        # Validate YAML content
        is_valid, playbook_schema, error = validate_playbook_yaml(playbook_data.yaml_content)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid playbook YAML: {error}")
        playbook.yaml_content = playbook_data.yaml_content
    
    db.commit()
    db.refresh(playbook)
    
    return PlaybookResponse(**playbook.to_dict())


@router.delete("/{playbook_id}")
async def delete_playbook(playbook_id: str, db: Session = Depends(get_db)):
    """Delete a playbook"""
    try:
        playbook_uuid = uuid.UUID(playbook_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playbook ID")
    
    playbook = db.query(Playbook).filter(Playbook.id == playbook_uuid).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    db.delete(playbook)
    db.commit()
    
    return {"message": "Playbook deleted successfully"}


@router.post("/validate")
async def validate_playbook(playbook_data: PlaybookCreate):
    """Validate playbook YAML without saving"""
    is_valid, playbook_schema, error = validate_playbook_yaml(playbook_data.yaml_content)
    
    return {
        "valid": is_valid,
        "error": error,
        "parsed": playbook_schema.dict() if is_valid else None
    }


@router.get("/samples/list")
async def list_sample_playbooks():
    """List available sample playbooks"""
    return {
        "samples": list(SAMPLE_PLAYBOOKS.keys()),
        "playbooks": SAMPLE_PLAYBOOKS
    }


@router.post("/samples/{sample_name}")
async def create_from_sample(sample_name: str, db: Session = Depends(get_db)):
    """Create a playbook from a sample"""
    if sample_name not in SAMPLE_PLAYBOOKS:
        raise HTTPException(status_code=404, detail="Sample playbook not found")
    
    sample_data = SAMPLE_PLAYBOOKS[sample_name]
    
    # Check if name already exists
    existing = db.query(Playbook).filter(Playbook.name == sample_data["name"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Playbook name already exists")
    
    # Convert to YAML
    import yaml
    yaml_content = yaml.dump(sample_data, default_flow_style=False)
    
    # Create playbook
    playbook = Playbook(
        name=sample_data["name"],
        description=sample_data.get("description"),
        yaml_content=yaml_content
    )
    
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    
    return PlaybookResponse(**playbook.to_dict())
