from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import csv
import io

from ..database import get_db
from ..views.persona import PersonaCreate, PersonaUpdate, PersonaRead, PoblarRequest
from ..services import persona_service

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
def create_persona(persona_in: PersonaCreate, db: Session = Depends(get_db)):
    """Create a new Persona delegating to service layer."""
    # Let domain errors bubble up to global handlers
    return persona_service.create_persona(db, persona_in)


@router.get("", response_model=List[PersonaRead])
def list_personas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List Personas with pagination via service layer."""
    return persona_service.list_personas(db, skip=skip, limit=limit)


@router.get("/{persona_id}", response_model=PersonaRead)
def get_persona(persona_id: int, db: Session = Depends(get_db)):
    """Retrieve a Persona by ID via service layer."""
    return persona_service.get_persona(db, persona_id)


@router.put("/{persona_id}", response_model=PersonaRead)
def update_persona(persona_id: int, persona_in: PersonaUpdate, db: Session = Depends(get_db)):
    """Update an existing Persona (partial) via service layer."""
    return persona_service.update_persona(db, persona_id, persona_in)

# NEW: Reset database endpoint
# IMPORTANT: /reset must go BEFORE /{persona_id}
@router.delete("/reset")
def resetear_base(db: Session = Depends(get_db)):
    """NEW: Delete all records (RESET)"""
    deleted_count = persona_service.reset_db(db)
    return {
        "message": "Database cleaned. All records deleted.",
        "deleted_count": deleted_count
    }

@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    """Delete a Persona by ID via service layer."""
    persona_service.delete_persona(db, persona_id)
    return None


# NEW: Endpoint for populating database with Faker data
@router.post("/poblar", status_code=status.HTTP_201_CREATED)
def poblar_datos(request: PoblarRequest, db: Session = Depends(get_db)):
    """NEW: Populate database with Faker data"""
    created = persona_service.poblar_db(db, request.cantidad)
    return {"message": f"{created} users created successfully", "status": 201}
