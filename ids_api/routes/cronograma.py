from flask import Blueprint, jsonify, request, Response

from ..constants import ROL_ADMIN, ERROR_CODE_ARCHIVO_FALTANTE
from ..utils import requiere_auth, construir_error_api, validar_entero, validar_minimo
from ..services.cronograma import (
    listar_clases,
    actualizar_clase,
    importar_cronograma_csv,
    exportar_cronograma_csv,
)

cronograma_bp = Blueprint('cronograma', __name__)

# Nombre del campo del formulario multipart donde viaja el archivo CSV.
CAMPO_ARCHIVO_CSV = 'archivo'


@cronograma_bp.route('/cronograma/clases', methods=['GET'])
def get_clases():
    """
    Retorna el cronograma completo con sus contenidos (público).

    Siempre devuelve las clases del período (las fechas no cargadas vienen
    autocompletadas con valores default), así que nunca es una lista vacía.
    """
    return jsonify(listar_clases())


@cronograma_bp.route('/cronograma/clases/<clase_id>', methods=['PUT'])
@requiere_auth(rol=ROL_ADMIN)
def put_clase(clase_id):
    body = request.get_json(silent=True)

    try:
        id_validado = validar_minimo(validar_entero(clase_id, 'id'), 1, 'id')
        clase = actualizar_clase(id_validado, body)
    except ValueError as error:
        status = error.args[1] if len(error.args) > 1 else 400

        return jsonify(error.args[0]), status

    return jsonify(clase)


@cronograma_bp.route('/cronograma/csv', methods=['POST'])
@requiere_auth(rol=ROL_ADMIN)
def post_cronograma_csv():
    """Alta bulk del cronograma desde un CSV (solo si está vacío)."""
    return _importar_csv(reemplazar=False, status_ok=201)


@cronograma_bp.route('/cronograma/csv', methods=['PUT'])
@requiere_auth(rol=ROL_ADMIN)
def put_cronograma_csv():
    """Reemplazo total del cronograma desde un CSV."""
    return _importar_csv(reemplazar=True, status_ok=200)


@cronograma_bp.route('/cronograma/csv', methods=['GET'])
def get_cronograma_csv():
    """Exporta el cronograma actual como CSV (descarga)."""
    contenido = exportar_cronograma_csv()

    return Response(
        contenido,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename="cronograma.csv"'},
    )


def _importar_csv(reemplazar: bool, status_ok: int):
    archivo = request.files.get(CAMPO_ARCHIVO_CSV)

    if archivo is None:
        return jsonify(construir_error_api(
            code=ERROR_CODE_ARCHIVO_FALTANTE,
            message='Archivo CSV faltante',
            description=f"Debe enviarse el CSV como archivo en el campo '{CAMPO_ARCHIVO_CSV}' (multipart/form-data)"
        )), 400

    contenido = archivo.read().decode('utf-8-sig')

    try:
        clases = importar_cronograma_csv(contenido, reemplazar=reemplazar)
    except ValueError as error:
        status = error.args[1] if len(error.args) > 1 else 400

        return jsonify(error.args[0]), status

    return jsonify(clases), status_ok
