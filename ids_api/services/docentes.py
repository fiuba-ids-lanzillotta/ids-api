from ..config import CACHE_TTL_DOCENTES_SEGUNDOS
from ..constants import ERROR_CODE_DOCENTE_NOT_FOUND, ERROR_CODE_EMAIL_DUPLICADO, ROLES_DOCENTE
from ..utils import construir_error_api
from ..validators.docentes import validar_body_docente
from .storage import subir_imagen_base64, obtener_imagen_base64, borrar_imagen
from .. import db, cache

# Prioridad de orden por rol: Profesor, luego Ayudantes, luego Colaboradores.
_ORDEN_ROL = {rol: indice for indice, rol in enumerate(ROLES_DOCENTE)}

# Clave de cache de las filas de docentes (metadata, sin las fotos base64).
_CACHE_DOCENTES = 'docentes:filas'


def construir_docente_dto(docente: dict) -> dict:
    """DTO público de un docente. La foto se expone como data URI base64 (o null)."""
    return {
        'id':       docente['id'],
        'nombre':   docente['nombre'],
        'apellido': docente['apellido'],
        'email':    docente['email'],
        'rol':      docente['rol'],
        'foto':     obtener_imagen_base64(docente['foto']),
    }


def listar_docentes() -> list[dict]:
    """
    Retorna los docentes ordenados por rol (Profesor, Ayudante, Colaborador) y luego por id.

    Las filas (metadata, incluido el path de la foto) se cachean en Redis y se
    invalidan en cada escritura. Las fotos NO van a Redis: se resuelven del bucket
    en `construir_docente_dto` (con su propio cache en proceso).
    """
    filas = cache.obtener(_CACHE_DOCENTES)
    if filas is None:
        filas = db.obtener_todos_los_docentes()
        cache.guardar(_CACHE_DOCENTES, filas, CACHE_TTL_DOCENTES_SEGUNDOS)

    filas = sorted(filas, key=lambda docente: (_ORDEN_ROL.get(docente['rol'], len(ROLES_DOCENTE)), docente['id']))

    return [construir_docente_dto(docente) for docente in filas]


def buscar_docente_por_id(docente_id: int) -> dict:
    """Busca un docente por id. Lanza ValueError 404 si no existe."""
    docente = _obtener_docente_o_404(docente_id)

    return construir_docente_dto(docente)


def crear_docente(body: dict) -> dict:
    """Valida el body, sube la foto (si viene) e inserta un docente."""
    datos = validar_body_docente(body)
    _validar_email_unico(datos['email'])

    foto_path = subir_imagen_base64(datos['foto']) if datos['foto'] else None

    nuevo_id = db.insertar_docente(
        datos['nombre'], datos['apellido'], datos['email'], datos['rol'], foto_path
    )
    cache.invalidar(_CACHE_DOCENTES)

    return buscar_docente_por_id(nuevo_id)


def actualizar_docente(docente_id: int, body: dict) -> dict:
    """
    Valida el body y actualiza un docente. Lanza ValueError 404 si no existe.

    Si el body trae una foto nueva, se sube y se borra la anterior; si no trae
    foto, se conserva la que ya tenía.
    """
    actual = _obtener_docente_o_404(docente_id)
    datos  = validar_body_docente(body)
    _validar_email_unico(datos['email'], excluir_id=docente_id)

    foto_path = actual['foto']

    if datos['foto']:
        foto_path = subir_imagen_base64(datos['foto'])

        if actual['foto']:
            borrar_imagen(actual['foto'])

    db.actualizar_docente(
        docente_id, datos['nombre'], datos['apellido'], datos['email'], datos['rol'], foto_path
    )
    cache.invalidar(_CACHE_DOCENTES)

    return buscar_docente_por_id(docente_id)


def eliminar_docente_por_id(docente_id: int) -> None:
    """Elimina un docente por id (y su foto del bucket), o lanza ValueError 404 si no existe."""
    docente = _obtener_docente_o_404(docente_id)

    db.eliminar_docente(docente_id)
    cache.invalidar(_CACHE_DOCENTES)
    borrar_imagen(docente['foto'])


def _validar_email_unico(email: str | None, excluir_id: int | None = None) -> None:
    """
    Verifica que el email no esté usado por otro docente (la columna es única).

    No hace nada si el email es None. `excluir_id` permite ignorar al propio
    docente en una actualización. Lanza ValueError 409 si ya está en uso.
    """
    if not email:
        return

    otro = db.obtener_docente_por_email(email)

    if otro and otro['id'] != excluir_id:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_EMAIL_DUPLICADO,
            message='Email en uso',
            description=f"Ya existe un docente con el email '{email}'"
        ), 409)


def _obtener_docente_o_404(docente_id: int) -> dict:
    """Retorna la fila cruda del docente (incluye el path de la foto) o lanza 404."""
    docente = db.obtener_docente_por_id(docente_id)

    if not docente:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_DOCENTE_NOT_FOUND,
            message='Docente no encontrado',
            description=f"No existe un docente con id '{docente_id}'"
        ), 404)

    return docente
