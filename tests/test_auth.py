import bcrypt
import pytest

from ids_api import utils
from ids_api.services import auth


def _codigos(excepcion):
    return [error['code'] for error in excepcion.value.args[0]['errors']]


# --- password ---

def test_verificar_password():
    hash_password = bcrypt.hashpw(b'secreto', bcrypt.gensalt()).decode('utf-8')

    assert utils.verificar_password('secreto', hash_password) is True
    assert utils.verificar_password('otro', hash_password) is False


def test_verificar_password_hash_invalido():
    assert utils.verificar_password('x', 'no-es-un-hash') is False


# --- JWT ---

def test_jwt_roundtrip():
    token = utils.generar_token(subject='admin', rol='admin')
    payload = utils.decodificar_token(token)

    assert payload['sub'] == 'admin'
    assert payload['rol'] == 'admin'


def test_jwt_invalido():
    with pytest.raises(ValueError) as excepcion:
        utils.decodificar_token('esto.no.es.un.jwt')

    assert _codigos(excepcion) == ['auth.token.invalid']


def test_jwt_expirado(monkeypatch):
    monkeypatch.setattr(utils, 'JWT_EXPIRACION_HORAS', -1)  # emite un token ya vencido
    token = utils.generar_token(subject='admin', rol='admin')

    with pytest.raises(ValueError) as excepcion:
        utils.decodificar_token(token)

    assert _codigos(excepcion) == ['auth.token.expired']


# --- autenticar_admin ---

def _config_admin(monkeypatch, password='secreto'):
    hash_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
    monkeypatch.setattr(auth, 'ADMIN_USER', 'admin')
    monkeypatch.setattr(auth, 'ADMIN_PASSWORD', hash_password)


def test_autenticar_admin_ok(monkeypatch):
    _config_admin(monkeypatch)
    resultado = auth.autenticar_admin({'usuario': 'admin', 'password': 'secreto'})

    assert resultado['usuario'] == {'usuario': 'admin', 'rol': 'admin'}
    assert utils.decodificar_token(resultado['token'])['rol'] == 'admin'


@pytest.mark.parametrize('body', [
    {'usuario': 'admin', 'password': 'mala'},
    {'usuario': 'otro', 'password': 'secreto'},
])
def test_autenticar_admin_invalido(monkeypatch, body):
    _config_admin(monkeypatch)
    with pytest.raises(ValueError) as excepcion:
        auth.autenticar_admin(body)

    assert _codigos(excepcion) == ['invalid.credentials']
    assert excepcion.value.args[1] == 401
