from flask import Blueprint, jsonify, request

from ..constants import ROL_ADMIN
from ..utils import requiere_auth, validar_entero, validar_minimo
from ..services.docentes import (
    listar_docentes,
    buscar_docente_por_id,
    crear_docente,
    actualizar_docente,
    eliminar_docente_por_id,
)

docentes_bp = Blueprint('docentes', __name__)


@docentes_bp.route('/docentes', methods=['GET'])
def get_docentes():
    """Lista todos los docentes (público)."""
    docentes = listar_docentes()

    if not docentes:
        return '', 204

    return jsonify(docentes)


@docentes_bp.route('/docentes/<docente_id>', methods=['GET'])
def get_docente(docente_id):
    try:
        id_validado = validar_minimo(validar_entero(docente_id, 'id'), 1, 'id')
        docente = buscar_docente_por_id(id_validado)
    except ValueError as e:
        status = e.args[1] if len(e.args) > 1 else 400

        return jsonify(e.args[0]), status

    return jsonify(docente)


@docentes_bp.route('/docentes', methods=['POST'])
@requiere_auth(rol=ROL_ADMIN)
def post_docente():
    body = request.get_json(silent=True)

    try:
        docente = crear_docente(body)
    except ValueError as e:
        status = e.args[1] if len(e.args) > 1 else 400

        return jsonify(e.args[0]), status

    return jsonify(docente), 201


@docentes_bp.route('/docentes/<docente_id>', methods=['PUT'])
@requiere_auth(rol=ROL_ADMIN)
def put_docente(docente_id):
    body = request.get_json(silent=True)

    try:
        id_validado = validar_minimo(validar_entero(docente_id, 'id'), 1, 'id')
        docente = actualizar_docente(id_validado, body)
    except ValueError as e:
        status = e.args[1] if len(e.args) > 1 else 400

        return jsonify(e.args[0]), status

    return jsonify(docente)


@docentes_bp.route('/docentes/<docente_id>', methods=['DELETE'])
@requiere_auth(rol=ROL_ADMIN)
def delete_docente(docente_id):
    try:
        id_validado = validar_minimo(validar_entero(docente_id, 'id'), 1, 'id')
        eliminar_docente_por_id(id_validado)
    except ValueError as e:
        status = e.args[1] if len(e.args) > 1 else 400

        return jsonify(e.args[0]), status

    return '', 204
