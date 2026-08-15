"""Tests de servicios con la capa de datos (db) mockeada; no tocan Supabase."""
import pytest

from ids_api import db
from ids_api.services import cronograma, docentes


def _codigos(exc_info):
    return [e['code'] for e in exc_info.value.args[0]['errors']]


# ---------------------------------------------------------------
# cronograma.actualizar_clase
# ---------------------------------------------------------------

def _mock_clase(monkeypatch, ocupa=None):
    """Mockea el db para una clase id=1 en 2026-08-17. Retorna el dict con los kwargs del update."""
    clase = {'id': 1, 'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Presencial', 'titulo': 'x'}
    ocupa = ocupa or {}
    reg = {}

    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda cid: dict(clase, id=cid))
    monkeypatch.setattr(db, 'obtener_contenidos_por_clase', lambda cid: [])
    monkeypatch.setattr(db, 'obtener_clase_por_fecha', lambda f: ocupa.get(f, {}))
    monkeypatch.setattr(db, 'actualizar_clase', lambda **kw: reg.update(kw) or 1)
    monkeypatch.setattr(db, 'eliminar_contenidos_de_clase', lambda cid: 0)
    monkeypatch.setattr(db, 'insertar_contenido', lambda *a: 1)

    return reg


def test_actualizar_clase_ok_deriva_semana(monkeypatch):
    reg = _mock_clase(monkeypatch)
    res = cronograma.actualizar_clase(
        1, {'semana': 9, 'fecha': '2026-08-17', 'tipo': 'Virtual', 'titulo': 'y', 'contenidos': []},
    )
    assert res['fecha'] == '2026-08-17'
    assert reg['semana'] == 1   # se deriva de la fecha, no se usa la del body (9)


def test_actualizar_clase_404(monkeypatch):
    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda cid: {})
    with pytest.raises(ValueError) as exc:
        cronograma.actualizar_clase(999, {'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'})
    assert exc.value.args[1] == 404


@pytest.mark.parametrize('fecha,code', [
    ('2026-08-18', 'fecha.invalid.weekday'),
    ('2026-07-06', 'fecha.out.of.period'),
])
def test_actualizar_clase_fecha_invalida(monkeypatch, fecha, code):
    _mock_clase(monkeypatch)
    with pytest.raises(ValueError) as exc:
        cronograma.actualizar_clase(1, {'semana': 1, 'fecha': fecha, 'tipo': 'Virtual'})
    assert code in _codigos(exc)


def test_actualizar_clase_fecha_ocupada(monkeypatch):
    _mock_clase(monkeypatch, ocupa={'2026-08-19': {'id': 2, 'fecha': '2026-08-19'}})
    with pytest.raises(ValueError) as exc:
        cronograma.actualizar_clase(1, {'semana': 1, 'fecha': '2026-08-19', 'tipo': 'Virtual'})
    assert _codigos(exc) == ['fecha.duplicated']
    assert exc.value.args[1] == 409


# ---------------------------------------------------------------
# cronograma.importar_cronograma_csv (completa y persiste)
# ---------------------------------------------------------------

def test_importar_completa_a_32_y_persiste(monkeypatch):
    capturado = {}
    monkeypatch.setattr(db, 'hay_clases', lambda: False)
    monkeypatch.setattr(db, 'eliminar_todo_el_cronograma', lambda: None)
    monkeypatch.setattr(db, 'insertar_clases',
                        lambda clases: capturado.update(n=len(clases)) or
                        [{'id': i + 1, 'fecha': c['fecha']} for i, c in enumerate(clases)])
    monkeypatch.setattr(db, 'insertar_contenidos', lambda cs: None)
    monkeypatch.setattr(db, 'obtener_todas_las_clases', lambda: [])
    monkeypatch.setattr(db, 'obtener_todos_los_contenidos', lambda: [])

    res = cronograma.importar_cronograma_csv('1,17/08/2026,Virtual,X\n', reemplazar=True)

    assert capturado['n'] == 32   # completa las faltantes antes de persistir
    assert len(res) == 32


# ---------------------------------------------------------------
# docentes: unicidad de email
# ---------------------------------------------------------------

def test_crear_docente_email_duplicado(monkeypatch):
    monkeypatch.setattr(db, 'obtener_docente_por_email', lambda e: {'id': 2, 'email': e})
    with pytest.raises(ValueError) as exc:
        docentes.crear_docente({'nombre': 'A', 'apellido': 'B', 'rol': 'Ayudante', 'email': 'a@fi.uba.ar'})
    assert _codigos(exc) == ['email.duplicated']
    assert exc.value.args[1] == 409


def test_crear_docente_ok(monkeypatch):
    monkeypatch.setattr(db, 'obtener_docente_por_email', lambda e: {})
    monkeypatch.setattr(db, 'insertar_docente', lambda *a: 99)
    monkeypatch.setattr(db, 'obtener_docente_por_id',
                        lambda i: {'id': i, 'nombre': 'A', 'apellido': 'B',
                                   'email': 'a@fi.uba.ar', 'rol': 'Ayudante', 'foto': None})
    monkeypatch.setattr(docentes, 'obtener_imagen_base64', lambda p: None)

    res = docentes.crear_docente({'nombre': 'A', 'apellido': 'B', 'rol': 'Ayudante', 'email': 'a@fi.uba.ar'})
    assert res['id'] == 99 and res['foto'] is None
