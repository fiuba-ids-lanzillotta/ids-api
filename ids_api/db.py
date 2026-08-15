from supabase import create_client, Client

from .constants import SUPABASE_URL, SUPABASE_KEY

# Cliente de Supabase compartido por toda la aplicación (habla PostgREST).
cliente: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------
# Docentes
# ---------------------------------------------------------------

CAMPOS_DOCENTE = 'id, nombre, apellido, email, rol, foto'


def obtener_todos_los_docentes() -> list[dict]:
    """Retorna todos los docentes ordenados por id."""
    return cliente.table('docentes').select(CAMPOS_DOCENTE).order('id').execute().data


def obtener_docente_por_id(docente_id: int) -> dict:
    """Retorna el docente con el id dado, o un dict vacío si no existe."""
    filas = cliente.table('docentes').select(CAMPOS_DOCENTE).eq('id', docente_id).execute().data

    return filas[0] if filas else {}


def obtener_docente_por_email(email: str) -> dict:
    """Retorna el docente con el email dado, o un dict vacío si no existe."""
    filas = cliente.table('docentes').select(CAMPOS_DOCENTE).eq('email', email).execute().data

    return filas[0] if filas else {}


def insertar_docente(nombre: str, apellido: str, email: str, rol: str, foto: str) -> int:
    """Inserta un nuevo docente y retorna el id generado."""
    filas = cliente.table('docentes').insert({
        'nombre':   nombre,
        'apellido': apellido,
        'email':    email,
        'rol':      rol,
        'foto':     foto,
    }).execute().data

    return filas[0]['id']


def actualizar_docente(docente_id: int, nombre: str, apellido: str,
                       email: str, rol: str, foto: str) -> int:
    """Actualiza un docente por id. Retorna la cantidad de filas afectadas."""
    filas = cliente.table('docentes').update({
        'nombre':   nombre,
        'apellido': apellido,
        'email':    email,
        'rol':      rol,
        'foto':     foto,
    }).eq('id', docente_id).execute().data

    return len(filas)


def eliminar_docente(docente_id: int) -> int:
    """Elimina un docente por id."""
    filas = cliente.table('docentes').delete().eq('id', docente_id).execute().data

    return len(filas)


# ---------------------------------------------------------------
# Cronograma (clases + contenidos)
# ---------------------------------------------------------------

CAMPOS_CLASE = 'id, semana, fecha, tipo, titulo'


def obtener_todas_las_clases() -> list[dict]:
    """Retorna todas las clases ordenadas por fecha."""
    return cliente.table('clases').select(CAMPOS_CLASE).order('fecha').execute().data


def obtener_clase_por_id(clase_id: int) -> dict:
    """Retorna la clase con el id dado, o un dict vacío si no existe."""
    filas = cliente.table('clases').select(CAMPOS_CLASE).eq('id', clase_id).execute().data

    return filas[0] if filas else {}


def obtener_clase_por_fecha(fecha: str) -> dict:
    """Retorna la clase con la fecha dada, o un dict vacío si no existe."""
    filas = cliente.table('clases').select(CAMPOS_CLASE).eq('fecha', fecha).execute().data

    return filas[0] if filas else {}


def obtener_contenidos_por_clase(clase_id: int) -> list[dict]:
    """Retorna los contenidos de una clase ordenados por su posición."""
    return (cliente.table('contenidos')
            .select('id, texto, hito')
            .eq('clase_id', clase_id)
            .order('orden')
            .execute().data)


def obtener_todos_los_contenidos() -> list[dict]:
    """Retorna todos los contenidos (para agrupar por clase sin N+1 queries)."""
    return (cliente.table('contenidos')
            .select('clase_id, texto, hito, orden')
            .order('clase_id')
            .order('orden')
            .execute().data)


def actualizar_clase(clase_id: int, semana: int, fecha: str, tipo: str, titulo: str) -> int:
    """Actualiza una clase por id. Retorna la cantidad de filas afectadas."""
    filas = cliente.table('clases').update({
        'semana': semana,
        'fecha':  fecha,
        'tipo':   tipo,
        'titulo': titulo,
    }).eq('id', clase_id).execute().data

    return len(filas)


def insertar_contenido(clase_id: int, texto: str, hito: bool, orden: int) -> int:
    """Inserta un contenido para una clase y retorna el id generado."""
    filas = cliente.table('contenidos').insert({
        'clase_id': clase_id,
        'texto':    texto,
        'hito':     hito,
        'orden':    orden,
    }).execute().data

    return filas[0]['id']


def eliminar_contenidos_de_clase(clase_id: int) -> int:
    """Elimina todos los contenidos asociados a una clase."""
    filas = cliente.table('contenidos').delete().eq('clase_id', clase_id).execute().data

    return len(filas)


def hay_clases() -> bool:
    """Indica si existe al menos una clase cargada."""
    return bool(cliente.table('clases').select('id').limit(1).execute().data)


def eliminar_todo_el_cronograma() -> None:
    """Borra todos los contenidos y todas las clases (PostgREST exige un filtro)."""
    cliente.table('contenidos').delete().neq('id', 0).execute()
    cliente.table('clases').delete().neq('id', 0).execute()


def insertar_clases(clases: list[dict]) -> list[dict]:
    """Inserta una lista de clases (bulk) y retorna las filas insertadas (con id y fecha)."""
    return cliente.table('clases').insert(clases).execute().data


def insertar_contenidos(contenidos: list[dict]) -> None:
    """Inserta una lista de contenidos (bulk)."""
    if contenidos:
        cliente.table('contenidos').insert(contenidos).execute()
