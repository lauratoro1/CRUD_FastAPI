from typing import Sequence, Dict, Any, List, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, extract, or_
import random
from faker import Faker
from unidecode import unidecode 
from sqlalchemy import text

from ..models.persona import Persona
from ..views.persona import PersonaCreate, PersonaUpdate
from .errors import PersonaNotFoundError, EmailAlreadyExistsError

def create_persona(db: Session, payload: PersonaCreate) -> Persona:
    """Create a Persona ensuring unique email."""
    # Optimistic check; DB unique constraint is the final guard
    if db.query(Persona).filter(Persona.email == payload.email).first():
        raise EmailAlreadyExistsError()
    obj = Persona(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        birth_date=payload.birth_date,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Catch race conditions on unique email
        raise EmailAlreadyExistsError() from e
    db.refresh(obj)
    return obj


def list_personas(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Persona]:
    """Return paginated list of Personas."""
    return db.query(Persona).offset(skip).limit(limit).all()


def get_persona(db: Session, persona_id: int) -> Persona:
    """Return Persona by ID or raise if not found."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()
    return obj


def update_persona(db: Session, persona_id: int, payload: PersonaUpdate) -> Persona:
    """Update Persona partially, enforcing unique email."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != obj.email:
        if db.query(Persona).filter(Persona.email == data["email"], Persona.id != persona_id).first():
            raise EmailAlreadyExistsError()

    for field, value in data.items():
        setattr(obj, field, value)

    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise EmailAlreadyExistsError() from e
    db.refresh(obj)
    return obj


def delete_persona(db: Session, persona_id: int) -> None:
    """Delete Persona by ID or raise if not found."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()
    db.delete(obj)
    db.commit()


# New function to populate database with Faker data
def poblar_db(db: Session, cantidad: int) -> int:
    """Generate fake persons with Faker and reset ID to 1 for MySQL"""
    
    # SOLUTION TO ERROR: Detect the real table name and disable foreign key checks
    nombre_tabla = Persona.__tablename__
    
    try:
        # 1. Disable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        # 2. Clear table and reset AUTO_INCREMENT
        db.execute(text(f"TRUNCATE TABLE {nombre_tabla};"))
        # 3. Enable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
    except Exception as e:
        db.rollback()
        # If TRUNCATE fails due to severe restrictions, use DELETE + ALTER
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text(f"DELETE FROM {nombre_tabla};"))
        db.execute(text(f"ALTER TABLE {nombre_tabla} AUTO_INCREMENT = 1;"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()

    fake = Faker('es_CO')
    dominios_reales = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com']
    
    emails_existentes = set()
    personas_a_crear = []
    
    for _ in range(cantidad):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        nombre_limpio = unidecode(first_name.lower().replace(" ", ""))
        apellido_limpio = unidecode(last_name.lower().replace(" ", ""))
        
        dominio = random.choice(dominios_reales)
        email_base = f"{nombre_limpio}.{apellido_limpio}"
        email = f"{email_base}@{dominio}"
        
        contador = 1
        while email in emails_existentes:
            email = f"{nombre_limpio}.{apellido_limpio}{contador}@{dominio}"
            contador += 1
            
        emails_existentes.add(email)
        
        prefijo_celular = random.choice(['300', '301', '310', '315', '320', '350'])
        numero_celular = f"{prefijo_celular}{random.randint(1000000, 9999999)}"
        
        persona = Persona(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=numero_celular,
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=85),
            is_active=random.choice([True, False]),
            notes=fake.sentence() if random.random() > 0.2 else None
        )
        personas_a_crear.append(persona)
    
    db.add_all(personas_a_crear)
    db.commit()
    return len(personas_a_crear)


# NEW: Reset database function
def reset_db(db: Session) -> int:
    """Delete all records from the personas table"""
    deleted_count = db.query(Persona).delete()
    db.commit()
    return deleted_count


# NEW: Statistics by email domain function
def estadisticas_for_domain(db: Session) -> Dict[str, int]:
    """Count of people by email domain"""
    resultados = db.query(
        func.substring_index(Persona.email, '@', -1).label('domain'),
        func.count(Persona.id).label('count')
    ).group_by('domain').all()
    return {row.domain: row.count for row in resultados}


# NEW: Age statistics function
def estadisticas_age(db: Session) -> Dict[str, int]:
    """Calculate average, minimum and maximum age"""
    hoy = date.today()
    personas = db.query(Persona.birth_date).all()
    
    if not personas:
        return {"average_age": 0, "min_age": 0, "max_age": 0}
    
    edades = []
    for p in personas:
        edad = hoy.year - p.birth_date.year
        if (hoy.month, hoy.day) < (p.birth_date.month, p.birth_date.day):
            edad -= 1
        edades.append(edad)
    
    return {
        "average_age": round(sum(edades) / len(edades)),
        "min_age": min(edades),
        "max_age": max(edades)
    }

# NEW: General search function
def buscar_termino(db: Session, termino: str) -> List[Persona]:
    """Search in first_name, last_name or email"""
    like_term = f"%{termino}%"
    return db.query(Persona).filter(
        (Persona.first_name.like(like_term)) |
        (Persona.last_name.like(like_term)) |
        (Persona.email.like(like_term))
    ).all()
    
    
# NEW: Report of active users with reduced projection
def reporte_activos(db: Session) -> List[Dict[str, Any]]:
    """Usuarios activos con proyección reducida"""
    resultados = db.query(
        Persona.id,
        Persona.email,
        Persona.phone,
        Persona.is_active
    ).filter(Persona.is_active == True).all()
    
    return [
        {
            "id": r.id,
            "email": r.email,
            "phone": r.phone,
            "is_active": r.is_active
        }
        for r in resultados
    ]
    
#NEW: Function to list people with birthdays in a specific month
def cumpleanios_por_mes(db: Session, numero_mes: int) -> List[Persona]:
    """Personas que cumplen años en el mes especificado"""
    return db.query(Persona).filter(
        extract('month', Persona.birth_date) == numero_mes
    ).all()