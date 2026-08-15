"""Tests de servicios con la capa de datos (db) mockeada; no tocan Supabase."""
import pytest

from ids_api import db
from ids_api.services import cronograma, docentes


def _codigos(excepcion):
    return [error['code'] for error in excepcion.value.args[0]['errors']]


# ---------------------------------------------------------------
# cronograma.actualizar_clase
# ---------------------------------------------------------------

def _mock_clase(monkeypatch, ocupa=None):
    """Mockea el db para una clase id=1 en 2026-08-17. Retorna el dict con los kwargs del update."""
    clase = {'id': 1, 'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Presencial', 'titulo': 'x'}
    ocupa = ocupa or {}
    registro = {}

    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda clase_id: dict(clase, id=clase_id))
    monkeypatch.setattr(db, 'obtener_contenidos_por_clase', lambda clase_id: [])
    monkeypatch.setattr(db, 'obtener_clase_por_fecha', lambda fecha: ocupa.get(fecha, {}))
    monkeypatch.setattr(db, 'actualizar_clase', lambda **kwargs: registro.update(kwargs) or 1)
    monkeypatch.setattr(db, 'eliminar_contenidos_de_clase', lambda clase_id: 0)
    monkeypatch.setattr(db, 'insertar_contenido', lambda *args: 1)

    return registro


def test_actualizar_clase_ok_deriva_semana(monkeypatch):
    registro = _mock_clase(monkeypatch)
    resultado = cronograma.actualizar_clase(
        1, {'semana': 9, 'fecha': '2026-08-17', 'tipo': 'Virtual', 'titulo': 'y', 'contenidos': []},
    )

    assert resultado['fecha'] == '2026-08-17'
    assert registro['semana'] == 1   # se deriva de la fecha, no se usa la del body (9)


def test_actualizar_clase_404(monkeypatch):
    monkeypatch.setattr(db, 'obtener_clase_por_id', lambda clase_id: {})

    with pytest.raises(ValueError) as excepcion:
        cronograma.actualizar_clase(999, {'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual'})

    assert excepcion.value.args[1] == 404


@pytest.mark.parametrize('fecha,codigo_esperado', [
    ('2026-08-18', 'fecha.invalid.weekday'),
    ('2026-07-06', 'fecha.out.of.period'),
])
def test_actualizar_clase_fecha_invalida(monkeypatch, fecha, codigo_esperado):
    _mock_clase(monkeypatch)

    with pytest.raises(ValueError) as excepcion:
        cronograma.actualizar_clase(1, {'semana': 1, 'fecha': fecha, 'tipo': 'Virtual'})

    assert codigo_esperado in _codigos(excepcion)


def test_actualizar_clase_fecha_ocupada(monkeypatch):
    _mock_clase(monkeypatch, ocupa={'2026-08-19': {'id': 2, 'fecha': '2026-08-19'}})

    with pytest.raises(ValueError) as excepcion:
        cronograma.actualizar_clase(1, {'semana': 1, 'fecha': '2026-08-19', 'tipo': 'Virtual'})

    assert _codigos(excepcion) == ['fecha.duplicated']
    assert excepcion.value.args[1] == 409


# ---------------------------------------------------------------
# cronograma.importar_cronograma_csv (completa y persiste)
# ---------------------------------------------------------------

def test_importar_completa_a_32_y_persiste(monkeypatch):
    capturado = {}
    monkeypatch.setattr(db, 'hay_clases', lambda: False)
    monkeypatch.setattr(db, 'eliminar_todo_el_cronograma', lambda: None)
    monkeypatch.setattr(db, 'insertar_clases',
                        lambda clases: capturado.update(cantidad=len(clases)) or
                        [{'id': indice + 1, 'fecha': clase['fecha']} for indice, clase in enumerate(clases)])
    monkeypatch.setattr(db, 'insertar_contenidos', lambda contenidos: None)
    monkeypatch.setattr(db, 'obtener_todas_las_clases', lambda: [])
    monkeypatch.setattr(db, 'obtener_todos_los_contenidos', lambda: [])

    resultado = cronograma.importar_cronograma_csv('1,17/08/2026,Virtual,X\n', reemplazar=True)

    assert capturado['cantidad'] == 32   # completa las faltantes antes de persistir
    assert len(resultado) == 32


# ---------------------------------------------------------------
# docentes: unicidad de email
# ---------------------------------------------------------------

def test_crear_docente_email_duplicado(monkeypatch):
    monkeypatch.setattr(db, 'obtener_docente_por_email', lambda email: {'id': 2, 'email': email})

    with pytest.raises(ValueError) as excepcion:
        docentes.crear_docente({'nombre': 'A', 'apellido': 'B', 'rol': 'Ayudante', 'email': 'a@fi.uba.ar'})

    assert _codigos(excepcion) == ['email.duplicated']
    assert excepcion.value.args[1] == 409


def test_crear_docente_ok(monkeypatch):
    monkeypatch.setattr(db, 'obtener_docente_por_email', lambda email: {})
    monkeypatch.setattr(db, 'insertar_docente', lambda *args: 99)
    monkeypatch.setattr(db, 'obtener_docente_por_id',
                        lambda docente_id: {'id': docente_id, 'nombre': 'A', 'apellido': 'B',
                                            'email': 'a@fi.uba.ar', 'rol': 'Ayudante', 'foto': None})
    monkeypatch.setattr(docentes, 'obtener_imagen_base64', lambda path: None)

    resultado = docentes.crear_docente({'nombre': 'A', 'apellido': 'B', 'rol': 'Ayudante', 'email': 'a@fi.uba.ar'})
    assert resultado['id'] == 99 and resultado['foto'] is None
