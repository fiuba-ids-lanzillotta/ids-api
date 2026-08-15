# Esquema de la base de datos

Diagrama entidad-relación de la base (PostgreSQL / Supabase). Fuente de verdad: [`init_db.sql`](init_db.sql).

```mermaid
erDiagram
    docentes {
        bigint   id       PK "identity"
        varchar  nombre      "NOT NULL (100)"
        varchar  apellido    "NOT NULL (100)"
        varchar  email    UK "nullable (150)"
        varchar  rol         "NOT NULL (20)"
        varchar  foto        "nullable (255) - path en el bucket"
    }

    clases {
        bigint   id       PK "identity"
        smallint semana      "NOT NULL"
        date     fecha    UK "NOT NULL"
        varchar  tipo        "NOT NULL (20)"
        varchar  titulo      "nullable (200)"
    }

    contenidos {
        bigint   id       PK "identity"
        bigint   clase_id FK "NOT NULL -> clases.id (ON DELETE CASCADE)"
        varchar  texto       "NOT NULL (500)"
        boolean  hito        "NOT NULL default false"
        smallint orden       "NOT NULL default 0"
    }

    clases ||--o{ contenidos : "tiene"
```

## Notas

- **`docentes`** es independiente (no tiene relaciones). El listado se ordena Profesor → Ayudante
  → Colaborador. `email` es único (y opcional); `foto` guarda el *path* del archivo en el bucket
  privado de Supabase Storage `docentes-fotos` (la API lo sube/devuelve como base64).
- **`clases` 1—* `contenidos`**: cada clase tiene sus contenidos ordenados por `orden`; borrar una
  clase borra sus contenidos (`ON DELETE CASCADE`). `fecha` es única (un slot lunes/miércoles por
  clase).
- **Campos de valor fijo como `VARCHAR`** (no `ENUM`): la validación vive en Python
  (`constants.py` + validators), para mantener el esquema portable entre motores.
  - `docentes.rol` ∈ `Profesor` | `Ayudante` | `Colaborador`
  - `clases.tipo` ∈ `Presencial` | `Virtual` | `Feriado` | `Sin clases`
- **No hay tabla de usuarios**: el único admin se configura por variables de entorno
  (`ADMIN_USER` / `ADMIN_PASSWORD`).
