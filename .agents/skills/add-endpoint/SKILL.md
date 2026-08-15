---
name: add-endpoint
description: Add a new endpoint/resource following the project's layering, error format, tests and OpenAPI docs
argument-hint: "[method and path, e.g. 'POST /materiales']"
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
    - Write(ids_api/**)
    - Write(tests/**)
    - Write(docs/**)
---

Add a new endpoint: **$ARGUMENTS**. Read `AGENTS.md` first and mirror the existing code.

## Checklist (respect the layering `routes → services → validators → db`)

1. **db layer** (`ids_api/db.py`): add the query-builder functions needed (select/insert/update/
   delete) using the shared Supabase `cliente`. Keep a `CAMPOS_*` select string if it's a new table.
   Never write raw SQL.

2. **validator** (`ids_api/validators/<recurso>.py`): if the endpoint takes a body, add a
   `validar_body_<recurso>` that accumulates field errors and returns a validated `dict`. Reuse the
   helpers in `utils.py` (`validar_string_no_vacio`, `validar_entero`, `validar_fecha`, ...).

3. **service** (`ids_api/services/<recurso>.py`): business logic. Build DTOs as `dict`. Raise
   `ValueError(construir_error_api(...), status)` for domain errors (404, 409, ...). No classes.

4. **route** (`ids_api/routes/<recurso>.py`): thin handler. Public reads need no auth; writes use
   `@requiere_auth(rol=ROL_ADMIN)`. Validate path params (`validar_minimo(validar_entero(...))`).
   Translate errors:
   ```python
   except ValueError as error:
       status = error.args[1] if len(error.args) > 1 else 400
       return jsonify(error.args[0]), status
   ```

5. **register** the blueprint in `app.py` (with `url_prefix=BASE_URL`) if the resource is new.

6. **error codes**: add any new `ERROR_CODE_*` to `constants.py` (domain) — do not inline literals.

7. **OpenAPI** (`docs/swagger.yaml`): add the path, request/response schemas, and all status codes
   (including `400/401/403/404/409` where they apply).

8. **tests** (`tests/`): add a service-level test with the `db` layer mocked via `monkeypatch`, and
   an end-to-end route test with `app.test_client()` (use a real JWT via
   `generar_token('admin', 'admin')` for admin routes). Tests are plain functions, no network.

9. **Verify:**
   ```bash
   pytest
   python -m compileall -q ids_api app.py
   ```

## Impact on ids-web (mandatory check)

This changes the API contract, so it can affect the frontend `ids-web` (`../ids-web`), the only
consumer of this API. Before finishing:

- Check whether `ids-web` consumes the affected endpoint: look in `web/services/*.py` (the
  `requests` calls) and the templates that render the data.
- If the change **breaks** `ids-web` (e.g., a renamed/removed field, a new required body field, a
  changed status code the front doesn't handle), **do not leave it silently broken**: report
  exactly what to update there (which `web/services/<recurso>.py` call, which field in which
  template) and, if the user agrees, apply it in `ids-web`.
- Remember requests to the API must carry `X-API-Key` (via `api_headers()` in `web/constants.py`)
  when the backend has `API_KEY` set.

Report the files added/changed, the status codes the new endpoint can return, and any required
`ids-web` change.
