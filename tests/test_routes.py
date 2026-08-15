"""Tests end-to-end de las rutas con test_client; db mockeado y JWT real."""
import pytest

import app as app_module
from ids_api import db
from ids_api.services import docentes
from ids_api.utils import generar_token


@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    return app_module.app.test_client()


def _auth(rol='admin'):
    return {'Authorization': f'Bearer {generar_token("admin", rol)}'}


# --- GET /cronograma/clases (público, siempre 32) ---

def test_get_clases(client, monkeypatch):
    monkeypatch.setattr(db, 'obtener_todas_las_clases', lambda: [])
    monkeypatch.setattr(db, 'obtener_todos_los_contenidos', lambda: [])

    respuesta = client.get('/ids_api/cronograma/clases')
    datos = respuesta.get_json()

    assert respuesta.status_code == 200
    assert len(datos) == 32
    assert datos[0]['tipo'] == 'Virtual'
    assert 's-maxage' in respuesta.headers.get('Cache-Control', '')


# --- PUT /cronograma/clases/<id> (auth admin) ---

def test_put_clase_sin_token(client):
    respuesta = client.put('/ids_api/cronograma/clases/1',
                           json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'})

    assert respuesta.status_code == 401


def test_put_clase_rol_insuficiente(client):
    respuesta = client.put('/ids_api/cronograma/clases/1',
                           json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'},
                           headers=_auth(rol='otro'))

    assert respuesta.status_code == 403


def test_put_clase_ok(client, monkeypatch):
    clase = {'id': 1, 'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Presencial', 'titulo': 'x'}
    registro = {}
    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda clase_id: dict(clase, id=clase_id))
    monkeypatch.setattr(db, 'obtener_contenidos_por_clase', lambda clase_id: [])
    monkeypatch.setattr(db, 'obtener_clase_por_fecha', lambda fecha: {})
    monkeypatch.setattr(db, 'actualizar_clase', lambda **kwargs: registro.update(kwargs) or 1)
    monkeypatch.setattr(db, 'eliminar_contenidos_de_clase', lambda clase_id: 0)
    monkeypatch.setattr(db, 'insertar_contenido', lambda *args: 1)

    respuesta = client.put('/ids_api/cronograma/clases/1',
                           json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual', 'titulo': 'y', 'contenidos': []},
                           headers=_auth())

    assert respuesta.status_code == 200
    assert registro['tipo'] == 'Virtual' and registro['semana'] == 1


# --- POST /cronograma/csv sin archivo ---

def test_post_csv_sin_archivo(client):
    respuesta = client.post('/ids_api/cronograma/csv', headers=_auth())

    assert respuesta.status_code == 400
    assert respuesta.get_json()['errors'][0]['code'] == 'file.missing'


# --- GET /docentes (ordenados por rol) ---

def test_get_docentes_ordenados_por_rol(client, monkeypatch):
    lista_docentes = [
        {'id': 1, 'nombre': 'Aye', 'apellido': 'x', 'email': None, 'rol': 'Ayudante', 'foto': None},
        {'id': 2, 'nombre': 'Cola', 'apellido': 'y', 'email': None, 'rol': 'Colaborador', 'foto': None},
        {'id': 3, 'nombre': 'Prof', 'apellido': 'z', 'email': None, 'rol': 'Profesor', 'foto': None},
    ]
    monkeypatch.setattr(db, 'obtener_todos_los_docentes', lambda: list(lista_docentes))
    monkeypatch.setattr(docentes, 'obtener_imagen_base64', lambda path: None)

    respuesta = client.get('/ids_api/docentes')

    assert respuesta.status_code == 200
    assert [docente['rol'] for docente in respuesta.get_json()] == ['Profesor', 'Ayudante', 'Colaborador']


def test_get_docentes_vacio_404(client, monkeypatch):
    monkeypatch.setattr(db, 'obtener_todos_los_docentes', lambda: [])

    respuesta = client.get('/ids_api/docentes')

    assert respuesta.status_code == 404
    assert respuesta.get_json()['errors'][0]['code'] == 'docente.not.found'
