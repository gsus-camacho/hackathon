"""Parent resolver service - maps phone numbers to parent identities."""
import logging
from typing import Optional, Dict, List, Any
from core.postgres import fetch_one, fetch_all

logger = logging.getLogger(__name__)

# In-memory cache for phone -> parent mapping (TTL: 1 hour)
_phone_cache: Dict[str, Dict] = {}


async def resolve_parent_by_phone(phone: str) -> Optional[str]:
    """
    Resolve a phone number to a parent identification (identificacion_padre).
    
    Checks:
    1. In-memory cache
    2. PostgreSQL padres_auth table
    3. Hijos module for linked students
    
    Returns:
        identificacion_padre if found, None otherwise
    """
    # Check cache first
    if phone in _phone_cache:
        return _phone_cache[phone].get("identificacion_padre")
    
    # Query PostgreSQL for phone mapping
    # Assuming there's a table that maps phones to parents
    query = """
        SELECT identificacion_padre, nombre_padre, telefono
        FROM hackaton_padres_auth
        WHERE telefono = $1 OR whatsapp = $1
        LIMIT 1
    """
    
    try:
        result = await fetch_one(query, phone)
        if result:
            parent_data = {
                "identificacion_padre": result["identificacion_padre"],
                "nombre_padre": result.get("nombre_padre", ""),
                "telefono": result.get("telefono", phone)
            }
            _phone_cache[phone] = parent_data
            return parent_data["identificacion_padre"]
    except Exception as e:
        logger.warning(f"Failed to resolve parent for phone {phone}: {e}")
    
    # Fallback: Try to find through hijos table
    try:
        query2 = """
            SELECT DISTINCT identificacion_padre, nombre_padre
            FROM hackaton_hijos
            WHERE telefono_padre = $1
            LIMIT 1
        """
        result = await fetch_one(query2, phone)
        if result:
            parent_data = {
                "identificacion_padre": result["identificacion_padre"],
                "nombre_padre": result.get("nombre_padre", ""),
                "telefono": phone
            }
            _phone_cache[phone] = parent_data
            return parent_data["identificacion_padre"]
    except Exception as e:
        logger.warning(f"Failed to resolve parent through hijos: {e}")
    
    return None


async def get_parent_info(identificacion_padre: str) -> Optional[Dict[str, Any]]:
    """Get full parent information by identification."""
    query = """
        SELECT 
            pa.identificacion_padre,
            pa.nombre_padre,
            pa.telefono,
            pa.email,
            pa.nit_colegio,
            pa.colegio
        FROM hackaton_padres_auth pa
        WHERE pa.identificacion_padre = $1
        LIMIT 1
    """
    
    try:
        result = await fetch_one(query, identificacion_padre)
        if result:
            return dict(result)
    except Exception as e:
        logger.error(f"Failed to get parent info: {e}")
    
    return None


async def get_parent_students(identificacion_padre: str) -> List[Dict[str, Any]]:
    """Get all students linked to a parent."""
    query = """
        SELECT 
            h.usuario_identificacion,
            h.nombre_estudiante,
            h.grado,
            h.colegio,
            h.nit_colegio
        FROM hackaton_hijos h
        WHERE h.identificacion_padre = $1
    """
    
    try:
        results = await fetch_all(query, identificacion_padre)
        return [dict(r) for r in results]
    except Exception as e:
        logger.error(f"Failed to get parent students: {e}")
        return []


async def link_phone_to_parent(phone: str, identificacion_padre: str) -> bool:
    """
    Manually link a phone number to a parent.
    Useful for onboarding flow.
    """
    _phone_cache[phone] = {
        "identificacion_padre": identificacion_padre
    }
    return True


def clear_phone_cache():
    """Clear the phone resolution cache."""
    global _phone_cache
    _phone_cache = {}