from ..constants import (
    TIPOS_CLASE,
    ERROR_CODE_INVALID_TIPO_CLASE,
)
from ..utils import (
    construir_error_api,
    validar_string_no_vacio,
    validar_entero,
    validar_minimo,
    validar_fecha,
)
from .auth import validar_body_presente


def _normalizar_contenidos(raw) -> list[dict]:
    """
    Normaliza la lista de contenidos a objetos { "texto": str, "hito": bool }.

    Acepta tanto strings sueltos (que pasan a { texto, hito: false }) como
    objetos { texto, hito }. Descarta los items sin texto.
    """
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(construir_error_api(
            code='invalid.contenidos',
            message="Formato de 'contenidos' inválido",
            description="El campo 'contenidos' debe ser una lista"
        ))

    contenidos = []

    for item in raw:
        if isinstance(item, str):
            texto, hito = item.strip(), False
        elif isinstance(item, dict):
            texto, hito = str(item.get('texto', '')).strip(), bool(item.get('hito', False))
        else:
            raise ValueError(construir_error_api(
                code='invalid.contenidos',
                message="Formato de 'contenidos' inválido",
                description="Cada contenido debe ser un texto o un objeto { texto, hito }"
            ))

        if texto:
            contenidos.append({'texto': texto, 'hito': hito})

    return contenidos


def validar_body_clase(body: dict) -> dict:
    """
    Valida el body para crear/actualizar una clase del cronograma.

    Campos obligatorios: semana, fecha (YYYY-MM-DD), tipo.
    Campos opcionales: titulo y contenidos (lista de objetos { texto, hito }).
    """
    validar_body_presente(body)

    errores    = []
    semana     = None
    fecha      = None
    tipo       = None
    contenidos = []

    try:
        semana = validar_minimo(validar_entero(body.get('semana'), 'semana'), 1, 'semana')
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

    try:
        fecha = validar_fecha(body.get('fecha'), 'fecha')
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

    try:
        tipo = validar_string_no_vacio(body.get('tipo'), 'tipo')

        if tipo not in TIPOS_CLASE:
            raise ValueError(construir_error_api(
                code=ERROR_CODE_INVALID_TIPO_CLASE,
                message='Tipo de clase inválido',
                description=f"El tipo '{tipo}' no es válido. Valores permitidos: {', '.join(TIPOS_CLASE)}"
            ))
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

    try:
        contenidos = _normalizar_contenidos(body.get('contenidos'))
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

    # Campo opcional de texto
    titulo = body.get('titulo')
    titulo = str(titulo).strip() if titulo is not None and str(titulo).strip() else None

    if errores:
        raise ValueError({'errors': errores})

    return {
        'semana':     semana,
        'fecha':      fecha,
        'tipo':       tipo,
        'titulo':     titulo,
        'contenidos': contenidos,
    }
