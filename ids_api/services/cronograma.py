import csv
import io
from datetime import date, datetime, timedelta

from ..constants import (
    FECHA_ISO_FORMATO,
    INICIO_CLASES,
    FIN_CLASES,
    DIAS_CLASE,
    TIPO_CLASE_DEFAULT,
    TITULO_CLASE_DEFAULT,
    ERROR_CODE_CLASE_NOT_FOUND,
    ERROR_CODE_CSV_INVALIDO,
    ERROR_CODE_FECHA_DUPLICADA,
    ERROR_CODE_CRONOGRAMA_NO_VACIO,
    ERROR_CODE_FECHA_DIA_INVALIDO,
    ERROR_CODE_FECHA_FUERA_PERIODO,
    ERROR_CODE_SEMANA_INCORRECTA,
)
from ..config import CACHE_TTL_CRONOGRAMA_SEGUNDOS
from ..utils import construir_error_api
from ..validators.cronograma import validar_body_clase
from .. import db, cache

# Clave de cache del cronograma completo (se invalida en cada escritura).
_CACHE_CLASES = 'cronograma:clases'

# Formato de fecha usado en el CSV (DD/MM/AAAA).
FECHA_CSV_FORMATO = '%d/%m/%Y'

# Encabezado del CSV. El import lo detecta y lo saltea si viene.
CSV_HEADER = ['semana', 'fecha', 'tipo', 'titulo', 'contenidos']


# ---------------------------------------------------------------
# Calendario del cuatrimestre (semanas y días de clase)
# ---------------------------------------------------------------

def _lunes_de(d: date) -> date:
    """Retorna el lunes de la semana de la fecha dada."""
    return d - timedelta(days=d.weekday())


def semanas_esperadas() -> list[tuple[int, str]]:
    """
    Retorna la lista de (semana, fecha_iso) esperada para todo el período:
    el lunes y el miércoles de cada semana entre INICIO_CLASES y FIN_CLASES.
    """
    inicio = _lunes_de(INICIO_CLASES)
    fin    = _lunes_de(FIN_CLASES)
    total  = (fin - inicio).days // 7 + 1

    esperadas = []
    for indice_semana in range(total):
        lunes = inicio + timedelta(weeks=indice_semana)
        for dia in DIAS_CLASE:
            esperadas.append((indice_semana + 1, (lunes + timedelta(days=dia)).isoformat()))

    return esperadas


def _semana_de_fecha(fecha_iso: str) -> int | None:
    """
    Retorna el número de semana (1..N) al que pertenece una fecha dentro del
    período, o None si la fecha está fuera del período o no es un día de clase.
    """
    fecha = date.fromisoformat(fecha_iso)

    if fecha.weekday() not in DIAS_CLASE:
        return None

    inicio      = _lunes_de(INICIO_CLASES)
    fin         = _lunes_de(FIN_CLASES)
    lunes_fecha = _lunes_de(fecha)

    if lunes_fecha < inicio or lunes_fecha > fin:
        return None

    return (lunes_fecha - inicio).days // 7 + 1


def _clase_default(semana: int, fecha_iso: str) -> dict:
    """Clase autogenerada para una fecha del período que no fue cargada."""
    return {
        'id':         None,
        'semana':     semana,
        'fecha':      fecha_iso,
        'tipo':       TIPO_CLASE_DEFAULT,
        'titulo':     TITULO_CLASE_DEFAULT,
        'contenidos': [],
    }


def _completar_clases(clases: list[dict]) -> list[dict]:
    """
    Completa el cronograma con las clases faltantes del período: por cada fecha
    esperada (lunes/miércoles) que no esté en `clases`, agrega una clase default.
    Retorna la lista completa ordenada cronológicamente.
    """
    por_fecha = {clase['fecha']: clase for clase in clases}

    return [
        por_fecha.get(fecha) or _clase_default(semana, fecha)
        for semana, fecha in semanas_esperadas()
    ]


def construir_clase_dto(clase: dict, contenidos: list[dict]) -> dict:
    """DTO de una clase, con sus contenidos. La fecha se expone en formato ISO (YYYY-MM-DD)."""
    fecha = clase['fecha']

    return {
        'id':         clase['id'],
        'semana':     clase['semana'],
        'fecha':      fecha.isoformat() if hasattr(fecha, 'isoformat') else fecha,
        'tipo':       clase['tipo'],
        'titulo':     clase['titulo'],
        'contenidos': [{'texto': contenido['texto'], 'hito': contenido['hito']} for contenido in contenidos],
    }


def _agrupar_contenidos(contenidos: list[dict]) -> dict[int, list[dict]]:
    """Agrupa una lista de contenidos por clase_id (preservando el orden recibido)."""
    por_clase: dict[int, list[dict]] = {}

    for contenido in contenidos:
        por_clase.setdefault(contenido['clase_id'], []).append(contenido)

    return por_clase


def listar_clases() -> list[dict]:
    """
    Retorna el cronograma completo del período (lista plana).

    Las fechas lunes/miércoles que no estén cargadas se completan con clases
    default (no se persisten; solo se devuelven). El resultado se cachea en Redis
    y se invalida en cada escritura del cronograma.
    """
    cacheada = cache.obtener(_CACHE_CLASES)
    if cacheada is not None:
        return cacheada

    por_clase = _agrupar_contenidos(db.obtener_todos_los_contenidos())
    dtos = [construir_clase_dto(clase, por_clase.get(clase['id'], [])) for clase in db.obtener_todas_las_clases()]
    resultado = _completar_clases(dtos)

    cache.guardar(_CACHE_CLASES, resultado, CACHE_TTL_CRONOGRAMA_SEGUNDOS)

    return resultado


def buscar_clase_por_id(clase_id: int) -> dict:
    """Busca una clase por id. Lanza ValueError 404 si no existe."""
    clase = db.obtener_clase_por_id(clase_id)

    if not clase:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_CLASE_NOT_FOUND,
            message='Clase no encontrada',
            description=f"No existe una clase con id '{clase_id}'"
        ), 404)

    return construir_clase_dto(clase, db.obtener_contenidos_por_clase(clase_id))


def actualizar_clase(clase_id: int, body: dict) -> dict:
    """Valida el body y actualiza la clase junto a sus contenidos. Lanza ValueError 404 si no existe."""
    buscar_clase_por_id(clase_id)

    datos  = validar_body_clase(body)
    semana = _validar_fecha_de_clase(datos['fecha'], clase_id)

    db.actualizar_clase(
        clase_id=clase_id,
        semana=semana,
        fecha=datos['fecha'],
        tipo=datos['tipo'],
        titulo=datos['titulo'],
    )

    _reemplazar_contenidos(clase_id, datos['contenidos'])
    cache.invalidar(_CACHE_CLASES)

    return buscar_clase_por_id(clase_id)


def _validar_fecha_de_clase(fecha_iso: str, clase_id: int) -> int:
    """
    Valida la fecha para el alta/edición de una clase individual y devuelve el
    número de semana que le corresponde.

    - Debe ser lunes o miércoles.
    - Debe caer dentro del período de clases.
    - No puede coincidir con la fecha de otra clase (la fecha es única).

    La semana se deriva de la fecha (no se confía en la que venga en el body).
    """
    if date.fromisoformat(fecha_iso).weekday() not in DIAS_CLASE:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_FECHA_DIA_INVALIDO,
            message='Día de clase inválido',
            description=f"La fecha {fecha_iso} no es lunes ni miércoles"
        ))

    semana = _semana_de_fecha(fecha_iso)

    if semana is None:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_FECHA_FUERA_PERIODO,
            message='Fecha fuera del período',
            description=f"La fecha {fecha_iso} está fuera del período de clases"
        ))

    otra = db.obtener_clase_por_fecha(fecha_iso)

    if otra and otra['id'] != clase_id:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_FECHA_DUPLICADA,
            message='Fecha duplicada',
            description=f"Ya existe otra clase con la fecha {fecha_iso}"
        ), 409)

    return semana


def _reemplazar_contenidos(clase_id: int, contenidos: list[dict]) -> None:
    """Borra los contenidos existentes de una clase y los reemplaza por los nuevos."""
    db.eliminar_contenidos_de_clase(clase_id)

    for orden, contenido in enumerate(contenidos):
        db.insertar_contenido(clase_id, contenido['texto'], contenido['hito'], orden)


# ---------------------------------------------------------------
# Import / export CSV del cronograma completo
# ---------------------------------------------------------------

def importar_cronograma_csv(contenido: str, reemplazar: bool) -> list[dict]:
    """
    Parsea y valida un CSV con el cronograma completo y lo persiste.

    - reemplazar=False (alta bulk): solo carga si el cronograma está vacío,
      de lo contrario lanza ValueError 409.
    - reemplazar=True (PUT completo): borra el cronograma existente y carga el nuevo.

    Las fechas lunes/miércoles del período que no vengan en el CSV se completan
    con clases default y se persisten. Retorna el cronograma completo resultante.
    """
    clases = _parsear_csv(contenido)

    if not reemplazar and db.hay_clases():
        raise ValueError(construir_error_api(
            code=ERROR_CODE_CRONOGRAMA_NO_VACIO,
            message='El cronograma ya tiene clases',
            description='Ya existe un cronograma cargado. Usá PUT /cronograma/csv para reemplazarlo.'
        ), 409)

    _reemplazar_cronograma(_completar_clases(clases))

    return listar_clases()


def _reemplazar_cronograma(clases: list[dict]) -> None:
    """
    Borra el cronograma existente e inserta el nuevo mediante llamadas separadas
    al cliente de Supabase.

    Nota: no es atómico (PostgREST no expone transacciones multi-statement). Si
    el insert falla luego del borrado, el cronograma puede quedar vacío/parcial.
    Se usa la fecha (única) para asociar cada clase con sus contenidos, sin
    depender del orden de retorno del bulk insert.
    """
    db.eliminar_todo_el_cronograma()

    filas = db.insertar_clases([
        {'semana': clase['semana'], 'fecha': clase['fecha'], 'tipo': clase['tipo'], 'titulo': clase['titulo']}
        for clase in clases
    ])
    id_por_fecha = {fila['fecha']: fila['id'] for fila in filas}

    contenidos = []
    for clase in clases:
        clase_id = id_por_fecha[clase['fecha']]
        for orden, contenido in enumerate(clase['contenidos']):
            contenidos.append({
                'clase_id': clase_id,
                'texto':    contenido['texto'],
                'hito':     contenido['hito'],
                'orden':    orden,
            })

    db.insertar_contenidos(contenidos)
    cache.invalidar(_CACHE_CLASES)


def exportar_cronograma_csv() -> str:
    """
    Serializa el cronograma actual a CSV (mismo formato que acepta el import).

    Los campos de texto (tipo, titulo y cada descripción de contenido) se
    exportan SIEMPRE entre comillas dobles, para representarlos como strings de
    forma consistente. Los demás campos (semana, fecha y el hito booleano) van
    sin comillas.

    Las clases faltantes del período se completan con los valores default.
    """
    lineas = [','.join(CSV_HEADER)]

    for clase in listar_clases():
        campos = [
            str(clase['semana']),
            _fecha_iso_a_csv(clase['fecha']),
            _entrecomillar(clase['tipo']),
            _entrecomillar(clase['titulo']) if clase['titulo'] else '',
        ]

        for contenido in clase['contenidos']:
            campos.append(_entrecomillar(contenido['texto']))
            campos.append('True' if contenido['hito'] else 'False')

        lineas.append(','.join(campos))

    return '\r\n'.join(lineas) + '\r\n'


def _entrecomillar(valor: str) -> str:
    """Devuelve el valor como campo CSV entre comillas dobles, escapando las internas."""
    return '"' + str(valor).replace('"', '""') + '"'


def _fecha_iso_a_csv(fecha) -> str:
    """Convierte la fecha (date o string ISO) al formato del CSV (DD/MM/AAAA)."""
    if hasattr(fecha, 'strftime'):
        return fecha.strftime(FECHA_CSV_FORMATO)

    return datetime.strptime(fecha, FECHA_ISO_FORMATO).strftime(FECHA_CSV_FORMATO)


def _parsear_csv(contenido: str) -> list[dict]:
    """Parsea el CSV a una lista de clases validadas. Acumula errores por fila."""
    filas = [fila for fila in csv.reader(io.StringIO(contenido)) if any(celda.strip() for celda in fila)]

    if not filas:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_CSV_INVALIDO,
            message='CSV vacío',
            description='El archivo no contiene filas de datos'
        ))

    # Saltear el encabezado si viene.
    if filas[0] and filas[0][0].strip().lower() == 'semana':
        filas = filas[1:]

    clases        = []
    errores       = []
    fechas_vistas = {}

    for nro_fila, campos in enumerate(filas, start=1):
        try:
            datos = _parsear_fila(campos)
        except ValueError as error:
            for detalle in error.args[0]['errors']:
                detalle = dict(detalle)
                detalle['description'] = f"Fila {nro_fila}: {detalle['description']}"
                errores.append(detalle)
            continue

        if datos['fecha'] in fechas_vistas:
            errores.append(construir_error_api(
                code=ERROR_CODE_FECHA_DUPLICADA,
                message='Fecha duplicada',
                description=f"Fila {nro_fila}: la fecha ya aparece en la fila {fechas_vistas[datos['fecha']]}"
            )['errors'][0])
        else:
            fechas_vistas[datos['fecha']] = nro_fila

        clases.append(datos)

    if errores:
        raise ValueError({'errors': errores})

    return clases


def _parsear_fila(campos: list[str]) -> dict:
    """Parsea una fila del CSV a un dict de clase validado."""
    errores = []

    semana = campos[0].strip() if len(campos) > 0 else None
    tipo   = campos[2].strip() if len(campos) > 2 else None
    titulo = campos[3].strip() if len(campos) > 3 else ''
    titulo = titulo or None

    fecha_iso = None

    try:
        fecha_iso = _parsear_fecha_csv(campos[1] if len(campos) > 1 else None)
    except ValueError as error:
        errores.extend(error.args[0]['errors'])

    contenidos = []

    try:
        contenidos = _parsear_contenidos(campos[4:])
    except ValueError as error:
        errores.extend(error.args[0]['errors'])

    body = {
        'semana':     semana,
        'fecha':      fecha_iso or '2000-01-01',  # placeholder si la fecha ya falló
        'tipo':       tipo,
        'titulo':     titulo,
        'contenidos': contenidos,
    }

    datos = None

    try:
        datos = validar_body_clase(body)
    except ValueError as error:
        for detalle in error.args[0]['errors']:
            # No duplicar el error de fecha si ya lo reportamos arriba.
            if fecha_iso is None and str(detalle.get('code', '')).startswith('invalid.fecha'):
                continue
            errores.append(detalle)

    # Validaciones de dominio: la fecha debe ser un día de clase válido del
    # período y la semana informada debe coincidir con la calculada.
    if fecha_iso is not None:
        errores.extend(_validar_fecha_periodo(fecha_iso, semana))

    if errores:
        raise ValueError({'errors': errores})

    return datos


def _validar_fecha_periodo(fecha_iso: str, semana_informada) -> list[dict]:
    """Valida que la fecha sea lunes/miércoles, esté en el período y que la semana coincida."""
    fecha = date.fromisoformat(fecha_iso)

    if fecha.weekday() not in DIAS_CLASE:
        return [construir_error_api(
            code=ERROR_CODE_FECHA_DIA_INVALIDO,
            message='Día de clase inválido',
            description=f"La fecha {fecha_iso} no es lunes ni miércoles"
        )['errors'][0]]

    semana_calculada = _semana_de_fecha(fecha_iso)

    if semana_calculada is None:
        return [construir_error_api(
            code=ERROR_CODE_FECHA_FUERA_PERIODO,
            message='Fecha fuera del período',
            description=f"La fecha {fecha_iso} está fuera del período de clases"
        )['errors'][0]]

    try:
        semana_informada_numero = int(str(semana_informada))
    except (ValueError, TypeError):
        return []  # el error de 'semana' ya lo reporta validar_body_clase

    if semana_informada_numero != semana_calculada:
        return [construir_error_api(
            code=ERROR_CODE_SEMANA_INCORRECTA,
            message='Semana incorrecta',
            description=f"La semana {semana_informada_numero} no corresponde a la fecha {fecha_iso} (semana esperada: {semana_calculada})"
        )['errors'][0]]

    return []


def _parsear_fecha_csv(valor) -> str:
    """Convierte una fecha DD/MM/AAAA a ISO (YYYY-MM-DD)."""
    valor = (valor or '').strip()

    try:
        return datetime.strptime(valor, FECHA_CSV_FORMATO).date().isoformat()
    except ValueError:
        raise ValueError(construir_error_api(
            code='invalid.fecha.format',
            message="Formato de 'fecha' inválido",
            description=f"El valor '{valor}' no es una fecha válida. Formato esperado: DD/MM/AAAA"
        ))


def _parsear_contenidos(campos: list[str]) -> list[dict]:
    """Convierte los campos posteriores a titulo en pares (descripción, hito)."""
    campos = list(campos)

    # Descartar celdas vacías al final (columnas sobrantes del CSV).
    while campos and campos[-1].strip() == '':
        campos.pop()

    if len(campos) % 2 != 0:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_CSV_INVALIDO,
            message='Contenidos mal formados',
            description='Los contenidos deben venir en pares (descripción, hito)'
        ))

    contenidos = []

    for indice in range(0, len(campos), 2):
        texto = campos[indice].strip()
        hito  = _parsear_hito(campos[indice + 1])

        if texto:
            contenidos.append({'texto': texto, 'hito': hito})

    return contenidos


def _parsear_hito(valor) -> bool:
    """Interpreta el flag de hito del CSV (True/False, 1/0)."""
    valor_normalizado = (valor or '').strip().lower()

    if valor_normalizado in ('true', '1', 'si', 'sí'):
        return True
    if valor_normalizado in ('false', '0', 'no', ''):
        return False

    raise ValueError(construir_error_api(
        code=ERROR_CODE_CSV_INVALIDO,
        message='Valor de hito inválido',
        description=f"El valor de hito '{valor}' no es válido. Se espera True o False"
    ))
