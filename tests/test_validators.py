import pytest

from ids_api.validators.auth import validar_body_login
from ids_api.validators.docentes import validar_body_docente
from ids_api.validators.cronograma import validar_body_clase, _normalizar_contenidos


def _codigos(excepcion):
    return [error['code'] for error in excepcion.value.args[0]['errors']]


# --- login ---

def test_login_ok():
    assert validar_body_login({'usuario': 'admin', 'password': 'x'}) == {
        'usuario': 'admin', 'password': 'x',
    }


def test_login_acumula_errores():
    with pytest.raises(ValueError) as excepcion:
        validar_body_login({})

    assert set(_codigos(excepcion)) == {'required.usuario', 'required.password'}


# --- docente ---

def test_docente_ok():
    datos = validar_body_docente({'nombre': 'Ana', 'apellido': 'Pérez', 'rol': 'Profesor'})

    assert datos['nombre'] == 'Ana'
    assert datos['rol'] == 'Profesor'
    assert datos['email'] is None and datos['foto'] is None


def test_docente_rol_invalido():
    with pytest.raises(ValueError) as excepcion:
        validar_body_docente({'nombre': 'Ana', 'apellido': 'P', 'rol': 'Jefe'})

    assert 'invalid.rol.docente' in _codigos(excepcion)


def test_docente_email_invalido():
    with pytest.raises(ValueError) as excepcion:
        validar_body_docente({'nombre': 'Ana', 'apellido': 'P', 'rol': 'Profesor', 'email': 'mal'})

    assert 'invalid.email.format' in _codigos(excepcion)


# --- clase ---

def test_clase_ok():
    datos = validar_body_clase({
        'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Virtual',
        'titulo': 'Intro', 'contenidos': ['a', {'texto': 'b', 'hito': True}],
    })

    assert datos['semana'] == 1
    assert datos['contenidos'] == [
        {'texto': 'a', 'hito': False}, {'texto': 'b', 'hito': True},
    ]


def test_clase_tipo_invalido():
    with pytest.raises(ValueError) as excepcion:
        validar_body_clase({'semana': 1, 'fecha': '2026-08-17', 'tipo': 'Zoom'})

    assert 'invalid.tipo.clase' in _codigos(excepcion)


def test_normalizar_contenidos_descarta_vacios():
    assert _normalizar_contenidos(['  ', 'x', {'texto': '', 'hito': True}]) == [
        {'texto': 'x', 'hito': False},
    ]
