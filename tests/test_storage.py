import base64

import pytest

from ids_api.services import storage

# Data URI mínimo y válido (1 byte de contenido, extensión permitida).
PIXEL = 'data:image/png;base64,' + base64.b64encode(b'x').decode('ascii')


def _codigos(excepcion):
    return [error['code'] for error in excepcion.value.args[0]['errors']]


@pytest.mark.parametrize('data_uri', [
    'no-es-data-uri',
    'data:image/png;base64,@@@no-base64@@@',
    'data:image/tiff;base64,' + base64.b64encode(b'x').decode('ascii'),  # extensión no permitida
])
def test_subir_imagen_rechaza_invalidas(data_uri):
    with pytest.raises(ValueError) as excepcion:
        storage.subir_imagen_base64(data_uri)

    assert _codigos(excepcion) == ['invalid.imagen']


def test_subir_imagen_rechaza_grande(monkeypatch):
    monkeypatch.setattr(storage, 'MAX_IMAGEN_MB', 0)  # cualquier contenido supera el límite

    with pytest.raises(ValueError) as excepcion:
        storage.subir_imagen_base64(PIXEL)

    assert _codigos(excepcion) == ['invalid.imagen']


def test_obtener_imagen_sin_path():
    assert storage.obtener_imagen_base64(None) is None
    assert storage.obtener_imagen_base64('') is None


def test_borrar_imagen_sin_path_no_falla():
    storage.borrar_imagen(None)  # no debe lanzar
    storage.borrar_imagen('')
