import csv
import io
from datetime import datetime

from ..constants import (
    ERROR_CODE_CLASE_NOT_FOUND,
    ERROR_CODE_CSV_INVALIDO,
    ERROR_CODE_FECHA_DUPLICADA,
    ERROR_CODE_CRONOGRAMA_NO_VACIO,
)
from ..utils import construir_error_api
from ..validators.cronograma import validar_body_clase
from .. import db

# Formato de fecha usado en el CSV (DD/MM/AAAA).
FECHA_CSV_FORMATO = '%d/%m/%Y'

# Encabezado del CSV. El import lo detecta y lo saltea si viene.
CSV_HEADER = ['semana', 'fecha', 'tipo', 'titulo', 'contenidos']


def construir_clase_dto(clase: dict, contenidos: list[dict]) -> dict:
    """DTO de una clase, con sus contenidos. La fecha se expone en formato ISO (YYYY-MM-DD)."""
    fecha = clase['fecha']

    return {
        'id':         clase['id'],
        'semana':     clase['semana'],
        'fecha':      fecha.isoformat() if hasattr(fecha, 'isoformat') else fecha,
        'tipo':       clase['tipo'],
        'titulo':     clase['titulo'],
        'contenidos': [{'texto': c['texto'], 'hito': c['hito']} for c in contenidos],
    }


def _agrupar_contenidos(contenidos: list[dict]) -> dict[int, list[dict]]:
    """Agrupa una lista de contenidos por clase_id (preservando el orden recibido)."""
    por_clase: dict[int, list[dict]] = {}

    for contenido in contenidos:
        por_clase.setdefault(contenido['clase_id'], []).append(contenido)

    return por_clase


def listar_clases() -> list[dict]:
    """Retorna todas las clases (lista plana) con sus contenidos."""
    clases     = db.obtener_todas_las_clases()
    por_clase  = _agrupar_contenidos(db.obtener_todos_los_contenidos())

    return [construir_clase_dto(c, por_clase.get(c['id'], [])) for c in clases]


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

    datos = validar_body_clase(body)

    db.actualizar_clase(
        clase_id=clase_id,
        semana=datos['semana'],
        fecha=datos['fecha'],
        tipo=datos['tipo'],
        titulo=datos['titulo'],
    )

    _reemplazar_contenidos(clase_id, datos['contenidos'])

    return buscar_clase_por_id(clase_id)


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

    Retorna la lista de clases resultante.
    """
    clases = _parsear_csv(contenido)

    if not reemplazar and db.hay_clases():
        raise ValueError(construir_error_api(
            code=ERROR_CODE_CRONOGRAMA_NO_VACIO,
            message='El cronograma ya tiene clases',
            description='Ya existe un cronograma cargado. Usá PUT /cronograma/csv para reemplazarlo.'
        ), 409)

    _reemplazar_cronograma(clases)

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
        {'semana': c['semana'], 'fecha': c['fecha'], 'tipo': c['tipo'], 'titulo': c['titulo']}
        for c in clases
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


def exportar_cronograma_csv() -> str:
    """Serializa el cronograma actual a CSV (mismo formato que acepta el import)."""
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(CSV_HEADER)

    por_clase = _agrupar_contenidos(db.obtener_todos_los_contenidos())

    for clase in db.obtener_todas_las_clases():
        fecha = clase['fecha']
        fecha_csv = _fecha_iso_a_csv(fecha)

        fila = [clase['semana'], fecha_csv, clase['tipo'], clase['titulo'] or '']

        for contenido in por_clase.get(clase['id'], []):
            fila.append(contenido['texto'])
            fila.append('True' if contenido['hito'] else 'False')

        escritor.writerow(fila)

    return salida.getvalue()


def _fecha_iso_a_csv(fecha) -> str:
    """Convierte la fecha (date o string ISO) al formato del CSV (DD/MM/AAAA)."""
    if hasattr(fecha, 'strftime'):
        return fecha.strftime(FECHA_CSV_FORMATO)

    return datetime.strptime(fecha, '%Y-%m-%d').strftime(FECHA_CSV_FORMATO)


def _parsear_csv(contenido: str) -> list[dict]:
    """Parsea el CSV a una lista de clases validadas. Acumula errores por fila."""
    filas = [f for f in csv.reader(io.StringIO(contenido)) if any(c.strip() for c in f)]

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
        except ValueError as e:
            for err in e.args[0]['errors']:
                err = dict(err)
                err['description'] = f"Fila {nro_fila}: {err['description']}"
                errores.append(err)
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
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

    contenidos = []
    try:
        contenidos = _parsear_contenidos(campos[4:])
    except ValueError as e:
        errores.extend(e.args[0]['errors'])

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
    except ValueError as e:
        for err in e.args[0]['errors']:
            # No duplicar el error de fecha si ya lo reportamos arriba.
            if fecha_iso is None and str(err.get('code', '')).startswith('invalid.fecha'):
                continue
            errores.append(err)

    if errores:
        raise ValueError({'errors': errores})

    return datos


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
    for i in range(0, len(campos), 2):
        texto = campos[i].strip()
        hito  = _parsear_hito(campos[i + 1])

        if texto:
            contenidos.append({'texto': texto, 'hito': hito})

    return contenidos


def _parsear_hito(valor) -> bool:
    """Interpreta el flag de hito del CSV (True/False, 1/0)."""
    v = (valor or '').strip().lower()

    if v in ('true', '1', 'si', 'sí'):
        return True
    if v in ('false', '0', ''):
        return False

    raise ValueError(construir_error_api(
        code=ERROR_CODE_CSV_INVALIDO,
        message='Valor de hito inválido',
        description=f"El valor de hito '{valor}' no es válido. Se espera True o False"
    ))
