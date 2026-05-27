from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import csv
import io

from ..database import get_db
from ..views.persona import PersonaCreate, PersonaUpdate, PersonaRead, PoblarRequest, BulkDesactivarRequest
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


# NEW: Endpoint for statistics by email domain
@router.get("/estadisticas/dominios")
def estadisticas_dominios(db: Session = Depends(get_db)):
    """NEW: Statistics by email domain"""
    return persona_service.estadisticas_for_domain(db)


# NEW: Endpoint for age statistics
@router.get("/estadisticas/edad")
def estadisticas_age(db: Session = Depends(get_db)):
    """NEW: Age statistics (average, minimum, maximum)"""
    return persona_service.estadisticas_age(db)

# NEW: Endpoint for general search
@router.get("/buscar/{termino}")
def buscar_termino(termino: str, db: Session = Depends(get_db)):
    """NEW: General search (name, last name, email)"""
    resultados = persona_service.buscar_termino(db, termino)
    return resultados

# NEW: Endpoint for active users report with reduced projection
@router.get("/reporte/activos")
def reporte_activos(db: Session = Depends(get_db)):
    """NEW: REPORT of active users with reduced projection (id, name, email)"""
    return persona_service.reporte_activos(db)

#NEW: Endpoint for birthdays in a specific month 
@router.get("/cumpleanios/mes/{numero_mes}")
def cumpleanios_mes(numero_mes: int, db: Session = Depends(get_db)):
    """NEW 7: List of people with birthdays in a specific month (1-12)"""
    if numero_mes < 1 or numero_mes > 12:
        raise HTTPException(status_code=400, detail="Número de mes inválido. Debe estar entre 1 y 12.")
    resultados = persona_service.cumpleanios_por_mes(db, numero_mes)
    return resultados

#NEW: Endpoint for bulk deactivation of users by list of IDs
@router.patch("/bulk/desactivar")
def desactivar_masivo(request: BulkDesactivarRequest, db: Session = Depends(get_db)):
    """NEW 8: Bulk deactivation of users by list of IDs (max 100)"""
    if not request.ids or len(request.ids) > 100:
        raise HTTPException(
            status_code=400, 
            detail="La lista de IDs debe tener entre 1 y 100 elementos."
        )
    
    desactivados, no_encontrados = persona_service.desactivar_masivo(db, request.ids)
    
    return {
        "message": "Operación completada.",
        "desactivados": desactivados,
        "no_encontrados": no_encontrados,
        "total_desactivados": len(desactivados)
    }
    
#NEW: Endpoint to export all records to CSV
@router.get("/exportar/csv")
def exportar_csv(db: Session = Depends(get_db)):
    """NEW: Export all records to CSV file for download"""
    personas = persona_service.exportar_todos(db)
    
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['id', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'is_active', 'notes'])
    
    for p in personas:
        writer.writerow([p.id, p.first_name, p.last_name, p.email, p.phone, p.birth_date, p.is_active, p.notes if p.notes else ''])
    
    buffer.seek(0)
    headers = {'Content-Disposition': 'attachment; filename="personas.csv"'}
    
    return StreamingResponse(buffer, media_type="text/csv", headers=headers)