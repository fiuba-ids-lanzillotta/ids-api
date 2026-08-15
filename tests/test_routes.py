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

    r = client.get('/ids_api/cronograma/clases')
    data = r.get_json()

    assert r.status_code == 200
    assert len(data) == 32
    assert data[0]['tipo'] == 'Virtual'


# --- PUT /cronograma/clases/<id> (auth admin) ---

def test_put_clase_sin_token(client):
    r = client.put('/ids_api/cronograma/clases/1',
                   json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'})

    assert r.status_code == 401


def test_put_clase_rol_insuficiente(client):
    r = client.put('/ids_api/cronograma/clases/1',
                   json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'},
                   headers=_auth(rol='otro'))

    assert r.status_code == 403


def test_put_clase_ok(client, monkeypatch):
    clase = {'id': 1, 'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Presencial', 'titulo': 'x'}
    reg = {}
    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda cid: dict(clase, id=cid))
    monkeypatch.setattr(db, 'obtener_contenidos_por_clase', lambda cid: [])
    monkeypatch.setattr(db, 'obtener_clase_por_fecha', lambda f: {})
    monkeypatch.setattr(db, 'actualizar_clase', lambda **kw: reg.update(kw) or 1)
    monkeypatch.setattr(db, 'eliminar_contenidos_de_clase', lambda cid: 0)
    monkeypatch.setattr(db, 'insertar_contenido', lambda *a: 1)

    r = client.put('/ids_api/cronograma/clases/1',
                   json={'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual', 'titulo': 'y', 'contenidos': []},
                   headers=_auth())

    assert r.status_code == 200
    assert reg['tipo'] == 'Virtual' and reg['semana'] == 1


# --- POST /cronograma/csv sin archivo ---

def test_post_csv_sin_archivo(client):
    r = client.post('/ids_api/cronograma/csv', headers=_auth())
    
    assert r.status_code == 400
    assert r.get_json()['errors'][0]['code'] == 'file.missing'


# --- GET /docentes (ordenados por rol) ---

def test_get_docentes_ordenados_por_rol(client, monkeypatch):
    docs = [
        {'id': 1, 'nombre': 'Aye', 'apellido': 'x', 'email': None, 'rol': 'Ayudante', 'foto': None},
        {'id': 2, 'nombre': 'Cola', 'apellido': 'y', 'email': None, 'rol': 'Colaborador', 'foto': None},
        {'id': 3, 'nombre': 'Prof', 'apellido': 'z', 'email': None, 'rol': 'Profesor', 'foto': None},
    ]
    monkeypatch.setattr(db, 'obtener_todos_los_docentes', lambda: list(docs))
    monkeypatch.setattr(docentes, 'obtener_imagen_base64', lambda p: None)

    r = client.get('/ids_api/docentes')

    assert r.status_code == 200
    assert [d['rol'] for d in r.get_json()] == ['Profesor', 'Ayudante', 'Colaborador']


def test_get_docentes_vacio_404(client, monkeypatch):
    monkeypatch.setattr(db, 'obtener_todos_los_docentes', lambda: [])

    r = client.get('/ids_api/docentes')

    assert r.status_code == 404
    assert r.get_json()['errors'][0]['code'] == 'docente.not.found'
