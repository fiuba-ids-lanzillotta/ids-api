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


def _codigos(exc_info):
    return [e['code'] for e in exc_info.value.args[0]['errors']]


# --- calendario del período ---

def test_semanas_esperadas():
    esp = semanas_esperadas()

    assert len(esp) == 32                 # 16 semanas x 2 (lunes y miércoles)
    assert esp[0] == (1, '2026-08-17')
    assert esp[1] == (1, '2026-08-19')
    assert esp[-1] == (16, '2026-12-02')


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
    assert all(c['tipo'] == 'Virtual' and c['titulo'] == 'A definir' for c in clases)
    assert all(c['id'] is None for c in clases)


def test_completar_preserva_cargadas():
    cargada = {'id': 7, 'semana': 1, 'fecha': '2026-08-17',
               'tipo': 'Presencial', 'titulo': 'Intro', 'contenidos': []}
    clases = _completar_clases([cargada])

    assert len(clases) == 32
    assert clases[0] == cargada                      # la cargada se mantiene
    assert clases[1]['titulo'] == 'A definir'        # el resto, default


# --- parser de CSV ---

def test_parsear_csv_ok():
    csv = '1,17/08/2026,Presencial,Intro,"Tema",False\n'
    clases = _parsear_csv(csv)

    assert len(clases) == 1
    assert clases[0]['fecha'] == '2026-08-17'
    assert clases[0]['contenidos'] == [{'texto': 'Tema', 'hito': False}]


@pytest.mark.parametrize('csv,code', [
    ('1,18/08/2026,Virtual,X\n', 'fecha.invalid.weekday'),   # martes
    ('1,06/07/2026,Virtual,X\n', 'fecha.out.of.period'),     # fuera de período
    ('5,17/08/2026,Virtual,X\n', 'semana.mismatch'),         # semana no coincide
])
def test_parsear_csv_valida_fecha(csv, code):
    with pytest.raises(ValueError) as exc:
        _parsear_csv(csv)

    assert code in _codigos(exc)


def test_parsear_csv_fecha_duplicada():
    csv = '1,17/08/2026,Virtual,A\n1,17/08/2026,Virtual,B\n'
    with pytest.raises(ValueError) as exc:
        _parsear_csv(csv)

    assert 'fecha.duplicated' in _codigos(exc)


def test_parsear_csv_saltea_header():
    csv = 'semana,fecha,tipo,titulo,contenidos\n1,17/08/2026,Virtual,X\n'
    clases = _parsear_csv(csv)

    assert len(clases) == 1 and clases[0]['fecha'] == '2026-08-17'


def test_parsear_csv_vacio():
    with pytest.raises(ValueError) as exc:
        _parsear_csv('')

    assert 'invalid.csv' in _codigos(exc)


# --- contenidos ---

def test_parsear_contenidos_pares():
    assert _parsear_contenidos(['Tema A', 'False', 'Tema B', 'True']) == [
        {'texto': 'Tema A', 'hito': False},
        {'texto': 'Tema B', 'hito': True},
    ]


def test_parsear_contenidos_impares_falla():
    with pytest.raises(ValueError) as exc:
        _parsear_contenidos(['Tema A', 'False', 'Tema B'])
        
    assert 'invalid.csv' in _codigos(exc)


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
