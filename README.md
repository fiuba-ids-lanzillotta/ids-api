# IDS-Lanzillotta-api

Backend de la página informativa de la cátedra de Lanzillotta de **Introducción al Desarrollo de Software** (FIUBA).

API REST en **Flask** que expone los datos de la cátedra (docentes y cronograma) y un login con roles para el panel de administración. Es el backend que consume el frontend [`ids-web`](../ids-web).

## Tecnologías

- **Python 3.10+**
- **Flask 3.0.3** + **flask-cors** (API y CORS para el frontend)
- **Supabase** (`supabase-py`) como backend de datos (PostgREST sobre PostgreSQL)
- **PyJWT** (autenticación stateless) + **bcrypt** (hashing de passwords)
- **python-dotenv** (variables de entorno)
- **Supabase CLI** para el entorno local (`supabase start`)

Sigue el mismo estilo **funcional** (sin clases, DTOs como `dict`) y la misma separación en capas **routes / services / validators / db** que el resto de los ejemplos del workspace. La capa `db` usa el **cliente de Supabase** (query builder), no ejecuta SQL crudo desde la app.

## Arquitectura

```
Flujo de una request:

  Frontend (ids-web)
       |
       |  HTTP (JSON) [+ header Authorization: Bearer <jwt> en endpoints admin]
       v
  Flask API (este proyecto, puerto 5000)
       |   - valida el body / parámetros
       |   - en endpoints protegidos: decodifica el JWT y valida el rol
       |   - usa el cliente de Supabase (service_role)
       v
  Supabase (PostgREST + PostgreSQL)
```

## Estructura del proyecto

```
ids-api/
├── app.py                       # Entry point Flask (puerto 5000, CORS, registro de blueprints)
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias de desarrollo (pytest)
├── vercel.json                  # Configuración de deploy en Vercel
├── pytest.ini / conftest.py     # Configuración de los tests
├── .env.example                 # Template de variables de entorno (Supabase + JWT + admin + CORS)
├── setup_virtualenv.bat/.sh     # Scripts de setup con virtualenv
├── setup_pipenv.bat/.sh         # Scripts de setup con pipenv
├── README.md
├── LICENSE
├── .gitignore
├── .gitattributes
│
├── ids_api/
│   ├── constants.py             # Constantes de dominio (roles, tipos, período, códigos de error)
│   ├── config.py                # Configuración de entorno (Supabase, JWT, admin, CORS)
│   ├── db.py                    # Capa de acceso a datos (cliente de Supabase)
│   ├── utils.py                 # Validaciones, bcrypt, JWT, @requiere_auth
│   ├── routes/                  # Un blueprint por recurso
│   │   ├── auth.py              #   POST /login, GET /me
│   │   ├── docentes.py          #   CRUD de docentes
│   │   └── cronograma.py        #   Cronograma (GET/PUT clases, import/export CSV)
│   ├── services/                # Lógica de negocio (una por recurso)
│   │   ├── auth.py
│   │   ├── docentes.py
│   │   └── cronograma.py
│   └── validators/              # Validación de bodies (una por recurso)
│       ├── auth.py
│       ├── docentes.py
│       └── cronograma.py
│
├── db/
│   ├── init_db.sql              # Esquema + seed (para correr en Supabase)
│   └── schema.md                # Diagrama entidad-relación (Mermaid)
├── docs/
│   └── swagger.yaml             # Documentación OpenAPI 3.0 de la API
└── tests/                       # Tests (pytest): utils, validators, servicios y rutas
```

## Configuración

### 1. Variables de entorno

Copiá `.env.example` a `.env` y completá los valores:

```bash
cp .env.example .env        # Linux / macOS
copy .env.example .env      # Windows
```

```
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=tu-service-role-key

JWT_SECRET=change-me-please
JWT_EXPIRACION_HORAS=8

ADMIN_USER=admin
ADMIN_PASSWORD=$2b$12$...   # hash bcrypt del password (no el texto plano)

CORS_ORIGINS=*             # orígenes permitidos (coma-separados); en prod, el dominio del front
```

| Variable         | Descripción                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `SUPABASE_URL`   | URL de la API del proyecto Supabase (en local la imprime `supabase start`). |
| `SUPABASE_KEY`   | **service_role** key (secreta, no se expone al frontend).                   |
| `SUPABASE_BUCKET_DOCENTES` | Bucket privado para las fotos de docentes (default `docentes-fotos`). |
| `JWT_SECRET`     | Clave con la que se firman los tokens. Usá una propia y larga fuera de local. |
| `JWT_EXPIRACION_HORAS` | Horas de validez del token (default `8`).                             |
| `ADMIN_USER`     | Usuario del panel de administración (único usuario).                        |
| `ADMIN_PASSWORD` | **Hash bcrypt** del password del admin (no el password en texto plano).     |
| `CORS_ORIGINS`   | Orígenes permitidos para CORS, separados por coma (default `*` = todos).     |

> El `.env` está en `.gitignore` y **no debe subirse al repositorio**.

Para generar una `JWT_SECRET` aleatoria:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Para generar el hash bcrypt de `ADMIN_PASSWORD`:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'tu-password', bcrypt.gensalt()).decode())"
```

### 2. Base de datos (Supabase)

El backend habla con Supabase a través de su cliente (PostgREST), no ejecuta SQL desde la app.
El esquema y el diagrama entidad-relación están en [`db/schema.md`](db/schema.md).

#### Desarrollo local con la CLI de Supabase

```bash
# 1. Instalar la CLI: https://supabase.com/docs/guides/cli
# 2. Inicializar (una vez) y levantar el stack local
supabase init
supabase start
```

`supabase start` imprime la **API URL** y las keys (`anon` y `service_role`). Copiá la API URL a `SUPABASE_URL` y la `service_role` key a `SUPABASE_KEY` en tu `.env`.

Luego aplicá el esquema y el seed corriendo `db/init_db.sql` en la base local (por ejemplo desde el editor SQL de Supabase Studio, en `http://127.0.0.1:54323`, o con `psql` contra la base local). Ese script también crea el bucket privado `docentes-fotos` (usado para las fotos de los docentes, que la API sube/devuelve como base64).

> Para un proyecto Supabase remoto, el flujo es el mismo: tomás `SUPABASE_URL` y la `service_role` key del dashboard, y corrés `db/init_db.sql` en su editor SQL.

### 3. Entorno virtual, instalación y ejecución

Los scripts crean el entorno virtual, instalan las dependencias y levantan la API.

**Con virtualenv:**

```bash
# Windows
setup_virtualenv.bat

# Linux / macOS
chmod +x setup_virtualenv.sh
./setup_virtualenv.sh
```

**Con pipenv:**

```bash
# Windows
setup_pipenv.bat

# Linux / macOS
chmod +x setup_pipenv.sh
./setup_pipenv.sh
```

También podés hacerlo manualmente:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux / macOS
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Una vez iniciada, la API estará disponible en `http://localhost:5000/ids_api`.

### 4. Acceso de administración

No hay tabla de usuarios: el panel usa un **único usuario** configurado por variables de entorno (`ADMIN_USER` / `ADMIN_PASSWORD`). Para obtener un token, hacé login con esas credenciales:

```bash
curl -X POST http://localhost:5000/ids_api/login \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","password":"tu-password"}'
```

La respuesta trae `{token, usuario}`. Ese `token` se envía en el header `Authorization: Bearer <token>` para los endpoints de escritura.

## Endpoints

Todos cuelgan del prefijo `/ids_api`. Las lecturas son públicas; las escrituras requieren el `admin` autenticado (`Authorization: Bearer <token>`). Los errores siguen el formato:

```json
{
  "errors": [
    { "code": "<codigo>", "message": "<mensaje breve>", "level": "error", "description": "<descripción detallada>" }
  ]
}
```

| Método | Endpoint                          | Auth        | Descripción                              |
|--------|-----------------------------------|-------------|------------------------------------------|
| POST   | `/login`                          | Público     | Devuelve `{token, usuario}`              |
| GET    | `/me`                             | Autenticado | Identidad del admin logueado             |
| GET    | `/docentes`                       | Público     | Lista el equipo docente                  |
| GET    | `/docentes/<id>`                  | Público     | Detalle de un docente                    |
| POST   | `/docentes`                       | Admin       | Crea un docente                          |
| PUT    | `/docentes/<id>`                  | Admin       | Actualiza un docente                     |
| DELETE | `/docentes/<id>`                  | Admin       | Elimina un docente                       |
| GET    | `/cronograma/clases`              | Público     | Lista todas las clases                   |
| PUT    | `/cronograma/clases/<id>`         | Admin       | Actualiza una clase                      |
| POST   | `/cronograma/csv`                 | Admin       | Alta bulk del cronograma desde CSV       |
| PUT    | `/cronograma/csv`                 | Admin       | Reemplaza todo el cronograma desde CSV   |
| GET    | `/cronograma/csv`                 | Público     | Exporta el cronograma actual como CSV    |

### Período de clases y autocompletado

El cuatrimestre se define por constantes (`INICIO_CLASES`, `FIN_CLASES` en `constants.py`): del **lunes 17/08/2026** al **lunes 30/11/2026**. Hay **2 clases por semana** (lunes y miércoles), lo que da **16 semanas → 32 clases**.

- Al **importar** (POST/PUT) o al **exportar/listar** (GET), las fechas lunes/miércoles del período que no estén cargadas se **completan automáticamente** con una clase default: `tipo = Virtual`, `titulo = "A definir"`, sin contenidos. En el import se persisten; en el GET solo se devuelven.
- Validaciones sobre cada fila: la `fecha` debe ser **lunes o miércoles**, estar **dentro del período**, y la `semana` informada debe **coincidir** con la que corresponde a esa fecha.

### Formato del CSV del cronograma

El CSV se envía como archivo (`multipart/form-data`, campo `archivo`). Cada fila:

```
semana, fecha, tipo, titulo, <descripción1>, <hito1>, <descripción2>, <hito2>, ...
```

- **Obligatorios**: `semana`, `fecha` (formato `DD/MM/AAAA`) y `tipo` (`Presencial` / `Virtual` / `Feriado` / `Sin clases`).
- `titulo` puede quedar vacío; `contenidos` puede estar vacío (p. ej. en feriados).
- Después de `titulo`, los contenidos van en **pares** `descripción, hito` (hito = `True`/`False`). Los campos de texto (tipo, titulo, descripciones) se exportan siempre entre comillas dobles.
- El `POST` solo carga si el cronograma está vacío (si no, `409`); el `PUT` reemplaza todo.

Ejemplo de fila:

```
1,17/08/2026,"Presencial","Introducción a la materia","Presentación de la materia",False,"Introducción a Linux (FileSystem, carpetas)",True
```

## Documentación (Swagger / OpenAPI)

La especificación completa en formato OpenAPI 3.0 vive en [`docs/swagger.yaml`](docs/swagger.yaml). Se puede visualizar pegándola en [editor.swagger.io](https://editor.swagger.io) o con la extensión "Swagger Viewer" en VSCode.

## Tests

Los tests (pytest) cubren funciones puras: validaciones, parser del CSV y la lógica de calendario (semanas del período, autocompletado). No requieren base ni red.

```bash
pip install -r requirements-dev.txt
pytest
```
