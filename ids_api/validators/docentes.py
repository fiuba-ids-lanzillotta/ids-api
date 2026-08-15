from ..constants import (
    ROLES_DOCENTE,
    ERROR_CODE_INVALID_ROL_DOCENTE,
)
from ..utils import (
    construir_error_api,
    validar_string_no_vacio,
    validar_largo_string,
    validar_formato_email,
)
from .auth import validar_body_presente


def validar_body_docente(body: dict) -> dict:
    """
    Valida el body para crear/actualizar un docente.

    Campos obligatorios: nombre, apellido, rol.
    Campos opcionales: email (único) y foto (data URI base64 de la imagen).
    La validación del contenido de la foto la hace la capa de storage.
    """
    validar_body_presente(body)

    errores  = []
    nombre   = None
    apellido = None
    rol      = None
    email    = None

    try:
        nombre = validar_string_no_vacio(body.get('nombre'), 'nombre')
        nombre = validar_largo_string(nombre, 1, 100, 'nombre')
    except ValueError as error:
        errores.extend(error.args[0]['errors'])

    try:
        apellido = validar_string_no_vacio(body.get('apellido'), 'apellido')
        apellido = validar_largo_string(apellido, 1, 100, 'apellido')
    except ValueError as error:
        errores.extend(error.args[0]['errors'])

    try:
        rol = validar_string_no_vacio(body.get('rol'), 'rol')

        if rol not in ROLES_DOCENTE:
            raise ValueError(construir_error_api(
                code=ERROR_CODE_INVALID_ROL_DOCENTE,
                message='Rol de docente inválido',
                description=f"El rol '{rol}' no es válido. Valores permitidos: {', '.join(ROLES_DOCENTE)}"
            ))
    except ValueError as error:
        errores.extend(error.args[0]['errors'])

    # email opcional
    if body.get('email') is not None and str(body.get('email')).strip():
        try:
            email = validar_formato_email(validar_string_no_vacio(body.get('email'), 'email'))
        except ValueError as error:
            errores.extend(error.args[0]['errors'])

    # foto opcional: data URI base64. La validación del contenido (formato,
    # extensión, tamaño) y la subida al bucket las hace services/storage.
    foto = body.get('foto')
    foto = foto if isinstance(foto, str) and foto.strip() else None

    if errores:
        raise ValueError({'errors': errores})

    return {
        'nombre':   nombre,
        'apellido': apellido,
        'email':    email,
        'rol':      rol,
        'foto':     foto,
    }
