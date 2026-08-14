-- =============================================================
--  IDS Lanzillotta - API :: Script DDL + seed para PostgreSQL
-- =============================================================
--  docker-compose lo ejecuta automáticamente al levantar el
--  contenedor (montado en /docker-entrypoint-initdb.d).
--
--  La base la crea el propio contenedor vía POSTGRES_DB.
--  El seed replica los datos que hoy tiene el frontend ids-web
--  en web/constants.py (docentes, cronograma, material), con las
--  fechas del cuatrimestre expresadas en el año 2026.
-- =============================================================

-- -------------------------------------------------------------
--  Esquema
--
--  Los campos de valores fijos (tipo de clase, rol de docente) se
--  modelan como VARCHAR y su validación vive en la capa Python
--  (constants.py + validators), para mantener el esquema portable
--  entre motores (sin ENUM propios de Postgres).
--
--  No hay tabla de usuarios: el único usuario de administración se
--  configura por variables de entorno (ADMIN_USER / ADMIN_PASSWORD).
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS docentes (
    id       BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre   VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email    VARCHAR(150) UNIQUE,
    rol      VARCHAR(20)  NOT NULL,
    foto     VARCHAR(255)              -- path del archivo en el bucket de Supabase Storage
);

CREATE TABLE IF NOT EXISTS clases (
    id      BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    semana  SMALLINT     NOT NULL,
    fecha   DATE         NOT NULL UNIQUE,
    tipo    VARCHAR(20)  NOT NULL,
    titulo  VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS contenidos (
    id       BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clase_id BIGINT       NOT NULL REFERENCES clases(id) ON DELETE CASCADE,
    texto    VARCHAR(500) NOT NULL,
    hito     BOOLEAN      NOT NULL DEFAULT FALSE,
    orden    SMALLINT     NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_contenidos_clase ON contenidos (clase_id);

-- -------------------------------------------------------------
--  Storage: bucket (privado) para las fotos de los docentes.
--  El backend lo usa con la key service_role (saltea RLS), así que
--  no hacen falta políticas. Alternativamente, crearlo desde el
--  dashboard: Storage > New bucket > "docentes-fotos" (no público).
-- -------------------------------------------------------------

INSERT INTO storage.buckets (id, name, public)
VALUES ('docentes-fotos', 'docentes-fotos', false)
ON CONFLICT (id) DO NOTHING;

-- -------------------------------------------------------------
--  Seed: docentes
-- -------------------------------------------------------------

-- email y foto quedan en NULL: los emails reales se cargan luego y las
-- fotos se suben al bucket de Supabase (recién ahí se completa foto).
INSERT INTO docentes (nombre, apellido, rol) VALUES
    ('Néstor Fabián',   'Palavecino Arnold', 'Ayudante'),
    ('Leonel Abel',     'Chaves',            'Ayudante'),
    ('Bruno',           'Lanzillotta',       'Profesor'),
    ('Cristian Martín', 'Sosa',              'Ayudante'),
    ('Tomás Ariel',     'Villegas Cabral',   'Ayudante'),
    ('Flavio Tomás',    'Villanueva',        'Colaborador'),
    ('Franco Daniel',   'Capra',             'Ayudante'),
    ('Tomas Gustavo',   'Rodriguez',         'Ayudante'),
    ('Luis Dario',      'Tejerina',          'Ayudante'),
    ('Tomás',           'Galluccio Antnuez', 'Colaborador'),
    ('Valentina',       'Grobly',            'Colaborador'),
    ('Camila Belén',    'Lo Iacono',         'Colaborador'),
    ('Sofía',           'Toledo',            'Colaborador'),
    ('Nicolás Ángel',   'Garofalo',          'Colaborador'),
    ('Carolina',        'Di Matteo',         'Colaborador');

-- -------------------------------------------------------------
--  Seed: cronograma (clases)
-- -------------------------------------------------------------

INSERT INTO clases (semana, fecha, tipo, titulo) VALUES
    (1,  '2026-08-17', 'Presencial', 'Introducción a la materia'),
    (1,  '2026-08-19', 'Virtual',    'Instalación de Linux'),
    (2,  '2026-08-24', 'Virtual',    'Continuación Bash'),
    (2,  '2026-08-26', 'Virtual',    'Git'),
    (3,  '2026-08-31', 'Feriado',    NULL),
    (3,  '2026-09-02', 'Presencial', 'Ejercitación TP1 (obligatoria)'),
    (4,  '2026-09-07', 'Virtual',    'Python + Flask'),
    (4,  '2026-09-09', 'Virtual',    'API RESTful'),
    (5,  '2026-09-14', 'Virtual',    'SQL'),
    (5,  '2026-09-16', 'Virtual',    'SQL (parte 2)'),
    (6,  '2026-09-21', 'Virtual',    'Git avanzado'),
    (6,  '2026-09-23', 'Virtual',    'Metodologías ágiles'),
    (7,  '2026-09-28', 'Presencial', 'Ejercitación Backend'),
    (7,  '2026-09-30', 'Sin clases', 'Elecciones en FIUBA (no hay clases)'),
    (8,  '2026-10-05', 'Virtual',    'Consultas primer parcial'),
    (8,  '2026-10-07', 'Presencial', 'Parcial'),
    (9,  '2026-10-12', 'Virtual',    'Introducción a Front End'),
    (9,  '2026-10-14', 'Virtual',    'Front End con Flask'),
    (10, '2026-10-19', 'Virtual',    'HTML y CSS'),
    (10, '2026-10-21', 'Virtual',    'JavaScript + HTML'),
    (11, '2026-10-26', 'Presencial', 'Integración Front + Backend'),
    (11, '2026-10-28', 'Virtual',    'Debugging + Testing'),
    (12, '2026-11-02', 'Feriado',    NULL),
    (12, '2026-11-04', 'Virtual',    'TP Integrador'),
    (13, '2026-11-09', 'Virtual',    'Docker'),
    (13, '2026-11-11', 'Presencial', 'Consultas del TP'),
    (14, '2026-11-16', 'Virtual',    'Docker (parte 2) + Compose'),
    (14, '2026-11-18', 'Presencial', '1er Recuperatorio'),
    (15, '2026-11-23', 'Feriado',    NULL),
    (15, '2026-11-25', 'Presencial', 'Entrega TP Integrador'),
    (16, '2026-11-30', 'Presencial', 'Defensas y consultas TP'),
    (16, '2026-12-02', 'Presencial', '2da Entrega TP Integrador');

-- -------------------------------------------------------------
--  Seed: contenidos de cada clase
--
--  hito = TRUE marca ese contenido como un hito relevante del día
--  (se muestra resaltado en el frontend). Cada clase referencia
--  su id vía la fecha, que es única.
-- -------------------------------------------------------------

INSERT INTO contenidos (clase_id, texto, hito, orden) VALUES
    ((SELECT id FROM clases WHERE fecha = '2026-08-17'), 'Presentación de la materia', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-08-17'), 'Introducción a Linux (FileSystem, carpetas)', TRUE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-08-17'), 'Terminal y comandos básicos (cd, ls, cat, cp, mv, sudo...)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), 'Opciones de instalación (WSL, VM, Dual boot)', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), 'Repaso general de comandos', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), '¿Qué es bash?', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), 'Variables de entorno', FALSE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), 'Estructuras condicionales e iterativas', FALSE, 4),
    ((SELECT id FROM clases WHERE fecha = '2026-08-19'), 'Mi primer script', FALSE, 5),
    ((SELECT id FROM clases WHERE fecha = '2026-08-24'), 'Estructuras condicionales e iterativas', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-08-24'), 'Pipelines, redirecciones, listas (&&, ||, ;)', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-08-24'), 'Scripts (búsqueda, reemplazo, manejo de archivos)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-08-26'), 'Repositorios y estados', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-08-26'), 'Comandos básicos (status, add, commit, push, pull, clone)', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-08-26'), 'Github: asociar SSH, subir repositorio', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-02'), 'Ejercitación integral de comandos', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-02'), 'Consultas Linux', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-02'), 'Ejercicios de scripting', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-07'), 'Repaso Python', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-07'), 'Instalación de Flask', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-07'), 'Introducción a Flask', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-09'), '¿Qué es una API?', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-09'), '¿Qué es REST?', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-09'), 'Ejemplo', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-14'), '¿Qué es una BDD? ¿Qué es SQL?', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-14'), 'BDD relacionales', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-14'), 'CREATE / DROP TABLE', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-14'), 'SELECT-FROM-WHERE', FALSE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-09-16'), 'Tipos de datos', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-16'), 'INSERT, UPDATE, DELETE', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-16'), 'AUTO_INCREMENT, PK', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-21'), 'Ramas (checkout, branch)', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-21'), 'git restore, staging', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-21'), 'git log y git diff', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-21'), 'Github Project', FALSE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-09-23'), 'Introducción a la agilidad', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-09-23'), 'Kanban', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-09-23'), 'Herramientas (Jira, Trello, Asana, Basecamp...)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-09-28'), 'Ejercitación integral de Backend', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-05'), 'Repaso y consultas previas al parcial', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-07'), 'Primer parcial', TRUE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-12'), 'Intro a HTML', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-12'), 'Intro a CSS', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-10-12'), 'Intro a JavaScript', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-10-12'), 'Mi primer código en Flask', FALSE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-10-14'), 'Flask con HTML + CSS (ejemplo asistido)', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-19'), 'HTML: estructura y etiquetas básicas', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-19'), 'CSS: clases e IDs, atributos básicos', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-10-19'), 'Flexbox (direction, justify, align)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-10-21'), 'JavaScript + HTML continuación', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-21'), 'Ejercitación', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-10-26'), 'Ejercitación integral Front + Backend', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-26'), 'Crear API consumiendo datos de una base', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-10-26'), 'SQL Joins', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-10-28'), 'Debugging', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-10-28'), 'Testing', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-11-04'), 'Trabajo sobre el TP Integrador', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-11-09'), '¿Qué es Docker? Diferencia con VM', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-11-09'), 'Container vs imagen', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-11-09'), 'Comandos básicos (run, ps, exec, images, pull...)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-11-11'), 'Consultas del TP', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-11-16'), 'Dockerfile, volúmenes y puertos', FALSE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-11-16'), 'docker build', FALSE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-11-16'), 'Docker Compose (compose.yaml)', FALSE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-11-16'), 'Comandos (build, up, stop, down)', FALSE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-11-18'), 'Primer recuperatorio', TRUE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-11-25'), '1er Entrega TP Integrador y Defensa', TRUE, 0),
    ((SELECT id FROM clases WHERE fecha = '2026-12-02'), '2da entrega TP Integrador y Defensa', TRUE, 0);

-- Entregas: cada entrega es un contenido más, marcado como hito.
INSERT INTO contenidos (clase_id, texto, hito, orden) VALUES
    ((SELECT id FROM clases WHERE fecha = '2026-08-17'), 'Entrega del enunciado TP1', TRUE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-09-02'), 'Clase obligatoria: resolución del ejercicio TP1 de bash', TRUE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-09-09'), 'Entrega enunciado TP2 BackEnd', TRUE, 3),
    ((SELECT id FROM clases WHERE fecha = '2026-09-28'), 'Clase obligatoria TP N°2', TRUE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-10-12'), 'Entrega enunciado TP Integrador', TRUE, 4),
    ((SELECT id FROM clases WHERE fecha = '2026-10-21'), 'Entrega parcial TP Integrador: alcance, backlog y mockup', TRUE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-10-28'), 'Entrega parcial TP Integrador: listado de endpoints y backend', TRUE, 2),
    ((SELECT id FROM clases WHERE fecha = '2026-11-04'), 'Entrega parcial: endpoints y backend', TRUE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-11-11'), 'Entrega parcial: templates e integración front con backend', TRUE, 1),
    ((SELECT id FROM clases WHERE fecha = '2026-11-30'), 'Defensas presenciales y consultas TP', TRUE, 0);
