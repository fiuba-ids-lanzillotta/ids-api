from ..constants import ERROR_CODE_DOCENTE_NOT_FOUND
from ..utils import construir_error_api
from ..validators.docentes import validar_body_docente
from .storage import subir_imagen_base64, obtener_imagen_base64, borrar_imagen
from .. import db


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
    """Retorna todos los docentes."""
    return [construir_docente_dto(d) for d in db.obtener_todos_los_docentes()]


def buscar_docente_por_id(docente_id: int) -> dict:
    """Busca un docente por id. Lanza ValueError 404 si no existe."""
    docente = _obtener_docente_o_404(docente_id)

    return construir_docente_dto(docente)


def crear_docente(body: dict) -> dict:
    """Valida el body, sube la foto (si viene) e inserta un docente."""
    datos = validar_body_docente(body)

    foto_path = subir_imagen_base64(datos['foto']) if datos['foto'] else None

    nuevo_id = db.insertar_docente(
        datos['nombre'], datos['apellido'], datos['email'], datos['rol'], foto_path
    )

    return buscar_docente_por_id(nuevo_id)


def actualizar_docente(docente_id: int, body: dict) -> dict:
    """
    Valida el body y actualiza un docente. Lanza ValueError 404 si no existe.

    Si el body trae una foto nueva, se sube y se borra la anterior; si no trae
    foto, se conserva la que ya tenía.
    """
    actual = _obtener_docente_o_404(docente_id)
    datos  = validar_body_docente(body)

    foto_path = actual['foto']

    if datos['foto']:
        foto_path = subir_imagen_base64(datos['foto'])

        if actual['foto']:
            borrar_imagen(actual['foto'])

    db.actualizar_docente(
        docente_id, datos['nombre'], datos['apellido'], datos['email'], datos['rol'], foto_path
    )

    return buscar_docente_por_id(docente_id)


def eliminar_docente_por_id(docente_id: int) -> None:
    """Elimina un docente por id (y su foto del bucket), o lanza ValueError 404 si no existe."""
    docente = _obtener_docente_o_404(docente_id)

    db.eliminar_docente(docente_id)
    borrar_imagen(docente['foto'])


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
