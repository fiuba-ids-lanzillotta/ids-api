---
name: schema-change
description: Apply a database schema change consistently across init_db.sql, the db layer, validators, services and tests
argument-hint: "[what changes, e.g. 'add columna aula to clases']"
allowed-tools:
  - read
  - edit
  - write
  - grep
  - glob
  - exec
permissions:
  allow:
    - Read(**)
    - Exec(pytest*)
    - Exec(python -m compileall*)
  ask:
    - Write(**)
---

Apply the schema change: **$ARGUMENTS**. Keep every layer consistent. Read `AGENTS.md` first.

## Steps

1. **`db/init_db.sql`** — change the `CREATE TABLE` (and the seed if the new/changed column needs
   values). Respect existing constraints (`NOT NULL`, `UNIQUE`, etc.). Remember: schema is applied
   by running this file in Supabase; the app never migrates automatically.

2. **`ids_api/db.py`** — update the `CAMPOS_*` select string and the insert/update payloads so the
   new field is read/written.

3. **`ids_api/validators/<recurso>.py`** — validate the new field (required? length? enum in
   `constants.py`?) and include it in the returned validated `dict`.

4. **`ids_api/services/<recurso>.py`** — include the field in the DTO builder (`construir_*_dto`)
   and pass it through create/update.

5. **`docs/swagger.yaml`** — add the field to the `Schema` and `Body` definitions (type, nullable,
   example, enum).

6. **`tests/`** — update fixtures/mocks that build rows for that table, and add assertions for the
   new field.

7. **Verify:**
   ```bash
   pytest
   python -m compileall -q ids_api app.py
   ```

## Notes

- Prefer `VARCHAR` + Python-side validation over DB `ENUM`/`CHECK` (portability convention).
- If the column is `UNIQUE`, add an app-level uniqueness check that returns `409` (like the
  `email` / `fecha` checks) so it doesn't surface as a raw `500`.
