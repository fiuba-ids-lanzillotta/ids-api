import pytest

from ids_api.utils import (
    validar_entero,
    validar_minimo,
    validar_maximo,
    validar_string_no_vacio,
    validar_largo_string,
    validar_formato_email,
    validar_fecha,
)


def _codigos(exc_info):
    """Extrae los codes del payload de error de un ValueError de la API."""
    return [e['code'] for e in exc_info.value.args[0]['errors']]


# --- validar_entero ---

def test_validar_entero_ok():
    assert validar_entero('42', 'id') == 42
    assert validar_entero(7, 'id') == 7


@pytest.mark.parametrize('valor', ['abc', '3.5', None, ''])
def test_validar_entero_invalido(valor):
    with pytest.raises(ValueError) as exc:
        validar_entero(valor, 'id')

    assert _codigos(exc) == ['invalid.id.format']


# --- min / max ---

def test_validar_minimo():
    assert validar_minimo(5, 1, 'n') == 5
    with pytest.raises(ValueError) as exc:
        validar_minimo(0, 1, 'n')
        
    assert _codigos(exc) == ['invalid.min.value']


def test_validar_maximo():
    assert validar_maximo(5, 10, 'n') == 5
    with pytest.raises(ValueError) as exc:
        validar_maximo(11, 10, 'n')
    assert _codigos(exc) == ['invalid.max.value']


# --- strings ---

def test_validar_string_no_vacio():
    assert validar_string_no_vacio('  hola  ', 'x') == 'hola'
    with pytest.raises(ValueError) as exc:
        validar_string_no_vacio('   ', 'x')
    assert _codigos(exc) == ['required.x']


def test_validar_largo_string():
    assert validar_largo_string('abc', 1, 5, 'x') == 'abc'
    with pytest.raises(ValueError):
        validar_largo_string('', 1, 5, 'x')
    with pytest.raises(ValueError):
        validar_largo_string('abcdef', 1, 5, 'x')


# --- email ---

def test_validar_formato_email_ok():
    assert validar_formato_email('Test@FI.uba.ar') == 'test@fi.uba.ar'


@pytest.mark.parametrize('email', ['sin-arroba', 'a@b', 'a b@c.com'])
def test_validar_formato_email_invalido(email):
    with pytest.raises(ValueError) as exc:
        validar_formato_email(email)
        
    assert _codigos(exc) == ['invalid.email.format']


# --- fecha ---

def test_validar_fecha_ok():
    assert validar_fecha('2026-08-17', 'fecha') == '2026-08-17'


@pytest.mark.parametrize('valor', ['17/08/2026', '2026-13-01', 'no-fecha', ''])
def test_validar_fecha_invalida(valor):
    with pytest.raises(ValueError):
        validar_fecha(valor, 'fecha')
