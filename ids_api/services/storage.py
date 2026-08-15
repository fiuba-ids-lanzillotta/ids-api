import base64
import binascii
import logging
import re
import uuid

from ..config import SUPABASE_BUCKET_DOCENTES
from ..constants import (
    EXTENSIONES_IMAGEN,
    MAX_IMAGEN_MB,
    ERROR_CODE_INVALID_IMAGEN,
    ERROR_CODE_IMAGEN_UPLOAD,
)
from ..utils import construir_error_api
from .. import db

logger = logging.getLogger(__name__)

# data:image/<ext>;base64,<datos>
REGEX_DATA_URI = re.compile(r'^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$', re.DOTALL)


def subir_imagen_base64(data_uri: str) -> str:
    """
    Decodifica un data URI base64 y sube la imagen al bucket privado.
    Retorna el path (nombre) del archivo generado en el bucket.
    Lanza ValueError con error API si el data URI es inválido o falla la subida.
    """
    match = REGEX_DATA_URI.match((data_uri or '').strip())

    if not match:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_IMAGEN,
            message='Imagen inválida',
            description='La foto debe ser un data URI base64 (data:image/<ext>;base64,...)'
        ))

    extension = match.group(1).lower()

    if extension not in EXTENSIONES_IMAGEN:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_IMAGEN,
            message='Formato de imagen no permitido',
            description=f"Extensiones permitidas: {', '.join(EXTENSIONES_IMAGEN)}"
        ))

    try:
        contenido = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_IMAGEN,
            message='Imagen inválida',
            description='El contenido base64 de la foto no es válido'
        ))

    if len(contenido) > MAX_IMAGEN_MB * 1024 * 1024:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_IMAGEN,
            message='Imagen demasiado grande',
            description=f'La foto no puede superar los {MAX_IMAGEN_MB} MB'
        ))

    nombre = f'{uuid.uuid4().hex}.{extension}'

    try:
        db.cliente.storage.from_(SUPABASE_BUCKET_DOCENTES).upload(
            path=nombre,
            file=contenido,
            file_options={'content-type': f'image/{extension}'},
        )
    except Exception as e:
        logger.error(f'Error al subir imagen al bucket: {e}')

        raise ValueError(construir_error_api(
            code=ERROR_CODE_IMAGEN_UPLOAD,
            message='No se pudo subir la imagen',
            description='Error al guardar la foto en el bucket de Supabase'
        ), 500)

    return nombre


def obtener_imagen_base64(path: str) -> str | None:
    """Descarga la imagen del bucket y la retorna como data URI base64, o None si no hay/falla."""
    if not path:
        return None

    try:
        contenido = db.cliente.storage.from_(SUPABASE_BUCKET_DOCENTES).download(path)
    except Exception as e:
        logger.error(f"Error al descargar imagen '{path}': {e}")

        return None

    extension = path.rsplit('.', 1)[1].lower() if '.' in path else 'jpeg'
    b64 = base64.b64encode(contenido).decode('utf-8')

    return f'data:image/{extension};base64,{b64}'


def borrar_imagen(path: str) -> None:
    """Borra una imagen del bucket (best-effort; no falla si no existe)."""
    if not path:
        return

    try:
        db.cliente.storage.from_(SUPABASE_BUCKET_DOCENTES).remove([path])
    except Exception as e:
        logger.error(f"Error al borrar imagen '{path}': {e}")
