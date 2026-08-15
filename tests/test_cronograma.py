import pytest

from ids_api.services.cronograma import (
    semanas_esperadas,
    _semana_de_fecha,
    _completar_clases,
    _parsear_csv,
    _parsear_contenidos,
    _parsear_hito,
    _fecha_iso_a_csv,
)


def _codigos(excepcion):
    return [error['code'] for error in excepcion.value.args[0]['errors']]


# --- calendario del período ---

def test_semanas_esperadas():
    esperadas = semanas_esperadas()

    assert len(esperadas) == 32               # 16 semanas x 2 (lunes y miércoles)
    assert esperadas[0] == (1, '2026-08-17')
    assert esperadas[1] == (1, '2026-08-19')
    assert esperadas[-1] == (16, '2026-12-02')


@pytest.mark.parametrize('fecha,esperado', [
    ('2026-08-17', 1),   # lunes semana 1
    ('2026-08-19', 1),   # miércoles semana 1
    ('2026-08-24', 2),   # lunes semana 2
    ('2026-11-30', 16),  # lunes última semana
    ('2026-08-18', None),  # martes
    ('2026-07-06', None),  # lunes fuera del período (antes)
    ('2026-12-07', None),  # lunes fuera del período (después)
])
def test_semana_de_fecha(fecha, esperado):
    assert _semana_de_fecha(fecha) == esperado


# --- completar clases faltantes ---

def test_completar_desde_vacio():
    clases = _completar_clases([])

    assert len(clases) == 32
    assert all(clase['tipo'] == 'Virtual' and clase['titulo'] == 'A definir' for clase in clases)
    assert all(clase['id'] is None for clase in clases)


def test_completar_preserva_cargadas():
    cargada = {'id': 7, 'semana': 1, 'fecha': '2026-08-17',
               'tipo': 'Presencial', 'titulo': 'Intro', 'contenidos': []}
    clases = _completar_clases([cargada])

    assert len(clases) == 32
    assert clases[0] == cargada                      # la cargada se mantiene
    assert clases[1]['titulo'] == 'A definir'        # el resto, default


# --- parser de CSV ---

def test_parsear_csv_ok():
    contenido_csv = '1,17/08/2026,Presencial,Intro,"Tema",False\n'
    clases = _parsear_csv(contenido_csv)

    assert len(clases) == 1
    assert clases[0]['fecha'] == '2026-08-17'
    assert clases[0]['contenidos'] == [{'texto': 'Tema', 'hito': False}]


@pytest.mark.parametrize('contenido_csv,codigo_esperado', [
    ('1,18/08/2026,Virtual,X\n', 'fecha.invalid.weekday'),   # martes
    ('1,06/07/2026,Virtual,X\n', 'fecha.out.of.period'),     # fuera de período
    ('5,17/08/2026,Virtual,X\n', 'semana.mismatch'),         # semana no coincide
])
def test_parsear_csv_valida_fecha(contenido_csv, codigo_esperado):
    with pytest.raises(ValueError) as excepcion:
        _parsear_csv(contenido_csv)

    assert codigo_esperado in _codigos(excepcion)


def test_parsear_csv_fecha_duplicada():
    contenido_csv = '1,17/08/2026,Virtual,A\n1,17/08/2026,Virtual,B\n'
    with pytest.raises(ValueError) as excepcion:
        _parsear_csv(contenido_csv)

    assert 'fecha.duplicated' in _codigos(excepcion)


def test_parsear_csv_saltea_header():
    contenido_csv = 'semana,fecha,tipo,titulo,contenidos\n1,17/08/2026,Virtual,X\n'
    clases = _parsear_csv(contenido_csv)

    assert len(clases) == 1 and clases[0]['fecha'] == '2026-08-17'


def test_parsear_csv_vacio():
    with pytest.raises(ValueError) as excepcion:
        _parsear_csv('')

    assert 'invalid.csv' in _codigos(excepcion)


# --- contenidos ---

def test_parsear_contenidos_pares():
    assert _parsear_contenidos(['Tema A', 'False', 'Tema B', 'True']) == [
        {'texto': 'Tema A', 'hito': False},
        {'texto': 'Tema B', 'hito': True},
    ]


def test_parsear_contenidos_impares_falla():
    with pytest.raises(ValueError) as excepcion:
        _parsear_contenidos(['Tema A', 'False', 'Tema B'])

    assert 'invalid.csv' in _codigos(excepcion)


# --- helpers de CSV ---

@pytest.mark.parametrize('valor,esperado', [
    ('True', True), ('true', True), ('1', True), ('si', True), ('sí', True),
    ('False', False), ('0', False), ('no', False), ('', False),
])
def test_parsear_hito(valor, esperado):
    assert _parsear_hito(valor) is esperado


def test_parsear_hito_invalido():
    with pytest.raises(ValueError):
        _parsear_hito('quizas')


def test_fecha_iso_a_csv():
    assert _fecha_iso_a_csv('2026-08-17') == '17/08/2026'
