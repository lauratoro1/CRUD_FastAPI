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
    
#NEW: Function for bulk deactivation of users by list of IDs
def desactivar_masivo(db: Session, ids: List[int]) -> Tuple[List[int], List[int]]:
    """Desactiva usuarios por lista de IDs"""
    personas = db.query(Persona).filter(Persona.id.in_(ids)).all()
    ids_existentes = [p.id for p in personas]
    ids_no_encontrados = [id for id in ids if id not in ids_existentes]
    
    if ids_existentes:
        db.query(Persona).filter(Persona.id.in_(ids_existentes)).update(
            {"is_active": False}, 
            synchronize_session=False
        )
        db.commit()
    
    return ids_existentes, ids_no_encontrados

#NEW: Function to export all records for CSV
def exportar_todos(db: Session) -> List[Persona]:
    """Retorna todos los registros para exportar a CSV"""
    return db.query(Persona).all()

#NEW: Function to calculate percentage of active/inactive users
def activos_porcentaje(db: Session) -> Dict[str, Any]:
    """Calcula el porcentaje de usuarios activos e inactivos"""
    total = db.query(Persona).count()
    
    if total == 0:
        return {
            "active": 0,
            "inactive": 0,
            "percentage_active": 0,
            "percentage_inactive": 0,
            "total": 0
        }
    
    activos = db.query(Persona).filter(Persona.is_active == True).count()
    inactivos = total - activos
    
    return {
        "active": activos,
        "inactive": inactivos,
        "percentage_active": round((activos / total) * 100, 2),
        "percentage_inactive": round((inactivos / total) * 100, 2),
        "total": total
    }

# New function to calculate age distribution
def rangos_edad(db: Session) -> Dict[str, Any]:
    """Distribution of people by age ranges"""
    hoy = date.today()

    rangos = [
        {"min": 18, "max": 25, "name": "18-25 (Youth)", "color": "#4CAF50"},
        {"min": 26, "max": 35, "name": "26-35 (Young Adults)", "color": "#2196F3"},
        {"min": 36, "max": 50, "name": "36-50 (Adults)", "color": "#FF9800"},
        {"min": 51, "max": 65, "name": "51-65 (Mature Adults)", "color": "#9C27B0"},
        {"min": 66, "max": 100, "name": "66+ (Seniors)", "color": "#F44336"}
    ]

    personas = db.query(Persona).all()

    if not personas:
        return {
            "total": 0,
            "ranges": [],
            "message": "No users registered"
        }

    resultado_rangos = []
    for r in rangos:
        resultado_rangos.append({
            "range": r["name"],
            "min_age": r["min"],
            "max_age": r["max"],
            "color": r["color"],
            "count": 0,
            "percentage": 0
        })

    edades = []
    for p in personas:
        edad = hoy.year - p.birth_date.year
        if (hoy.month, hoy.day) < (p.birth_date.month, p.birth_date.day):
            edad -= 1
        edades.append(edad)

        for i, r in enumerate(rangos):
            if r["min"] <= edad <= r["max"]:
                resultado_rangos[i]["count"] += 1
                break

    total = len(personas)
    for r in resultado_rangos:
        r["percentage"] = round((r["count"] / total) * 100, 2)

    edad_promedio = round(sum(edades) / len(edades)) if edades else 0

    return {
        "total": total,
        "average_age": edad_promedio,
        "min_age": min(edades) if edades else 0,
        "max_age": max(edades) if edades else 0,
        "ranges": resultado_rangos
    }

# NEW: Function to get users without notes
def personas_sin_notas(db: Session, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Retorna personas que no tienen notas (notes = null o vacío)"""
    
    query = db.query(Persona).filter(
        or_(
            Persona.notes == None,
            Persona.notes == ''
        )
    )
    
    total = query.count()
    personas = query.offset(skip).limit(limit).all()
    
    datos = []
    for p in personas:
        datos.append({
            "id": p.id,
            "nombre_completo": f"{p.first_name} {p.last_name}",
            "email": p.email,
            "telefono": p.phone,
            "activo": p.is_active,
            "fecha_nacimiento": str(p.birth_date)
        })
    
    total_general = db.query(Persona).count()
    porcentaje = round((total / total_general) * 100, 2) if total_general > 0 else 0
    
    return {
        "total_sin_notas": total,
        "total_registros": total_general,
        "porcentaje_sin_notas": porcentaje,
        "limit": limit,
        "skip": skip,
        "datos": datos
    }

# NEW: Function to get top email domains
def top_dominios(db: Session, limite: int = 5) -> Dict[str, Any]:
    """Retorna el top N de dominios de email más utilizados"""
    
    resultados = db.query(
        func.substring_index(Persona.email, '@', -1).label('dominio'),
        func.count(Persona.id).label('cantidad')
    ).group_by('dominio').order_by(
        func.count(Persona.id).desc()
    ).limit(limite).all()
    
    total = db.query(Persona).count()
    
    if total == 0:
        return {
            "top_dominios": [],
            "total_usuarios": 0,
            "mensaje": "No hay usuarios registrados"
        }
    
    top_list = []
    for row in resultados:
        porcentaje = round((row.cantidad / total) * 100, 2)
        top_list.append({
            "dominio": row.dominio,
            "cantidad": row.cantidad,
            "porcentaje": porcentaje
        })
    
    otros_total = total - sum(r.cantidad for r in resultados)
    otros_porcentaje = round((otros_total / total) * 100, 2) if otros_total > 0 else 0
    
    return {
        "top_dominios": top_list,
        "otros": {
            "cantidad": otros_total,
            "porcentaje": otros_porcentaje
        },
        "total_usuarios": total,
        "limite_solicitado": limite
    }

# NEW: Function to export all users
def exportar_json(db: Session) -> Dict[str, Any]:
    """Exporta todos los registros a formato JSON estructurado"""
    
    personas = db.query(Persona).all()
    
    if not personas:
        return {
            "total_registros": 0,
            "fecha_exportacion": str(date.today()),
            "mensaje": "No hay usuarios registrados",
            "datos": []
        }
    
    datos_exportados = []
    for p in personas:
        hoy = date.today()
        edad = hoy.year - p.birth_date.year
        if (hoy.month, hoy.day) < (p.birth_date.month, p.birth_date.day):
            edad -= 1
        
        datos_exportados.append({
            "id": p.id,
            "nombre_completo": f"{p.first_name} {p.last_name}",
            "nombre": p.first_name,
            "apellido": p.last_name,
            "email": p.email,
            "telefono": p.phone,
            "fecha_nacimiento": str(p.birth_date),
            "edad": edad,
            "activo": p.is_active,
            "estado": "Activo" if p.is_active else "Inactivo",
            "notas": p.notes if p.notes else "",
            "dominio_email": p.email.split('@')[1] if '@' in p.email else ""
        })
    
    return {
        "total_registros": len(datos_exportados),
        "fecha_exportacion": str(date.today()),
        "version_api": "1.0",
        "datos": datos_exportados
    }





# NEW: Function to get users by birth date
def buscar_por_rango_fechas(db: Session, fecha_inicio: str, fecha_fin: str) -> Dict[str, Any]:
    """Busca personas nacidas entre dos fechas"""
    
    try:
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return {
            "error": "Formato de fecha inválido",
            "mensaje": "Use el formato YYYY-MM-DD (ejemplo: 1990-01-01)",
            "ejemplo": "/fechas/rango/1990-01-01/2000-12-31"
        }
    
    if inicio > fin:
        return {
            "error": "Rango de fechas inválido",
            "mensaje": "La fecha de inicio debe ser menor que la fecha de fin"
        }
    
    personas = db.query(Persona).filter(
        Persona.birth_date >= inicio,
        Persona.birth_date <= fin
    ).all()
    
    hoy = date.today()
    datos = []
    for p in personas:
        edad = hoy.year - p.birth_date.year
        if (hoy.month, hoy.day) < (p.birth_date.month, p.birth_date.day):
            edad -= 1
        
        datos.append({
            "id": p.id,
            "nombre_completo": f"{p.first_name} {p.last_name}",
            "email": p.email,
            "telefono": p.phone,
            "fecha_nacimiento": str(p.birth_date),
            "edad_actual": edad,
            "activo": p.is_active,
            "estado": "Activo" if p.is_active else "Inactivo"
        })
    
    return {
        "filtro": {
            "fecha_inicio": str(inicio),
            "fecha_fin": str(fin),
            "total_registros": len(personas)
        },
        "resultados": datos
    }