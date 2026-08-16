# AGENTS.md

Guide for agents (and people) working on **ids-api**. Keep it short and actionable.

## Overview

REST API in **Flask** that exposes the course's docentes and cronograma, with admin login (JWT).
Data backend: **Supabase** (PostgREST). Consumed by the `ids-web` frontend.

## How to run

```bash
# setup + run (creates venv, installs deps, starts the API on :5000)
setup_virtualenv.bat        # Windows
./setup_virtualenv.sh       # Linux / macOS

# or manually
python -m venv .venv && .venv\Scripts\activate   # (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python app.py
```

Requires a `.env` (see `.env.example`): `SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET`,
`ADMIN_USER`, `ADMIN_PASSWORD` (bcrypt hash), optional `CORS_ORIGINS`, `JWT_EXPIRACION_HORAS`,
`SUPABASE_BUCKET_DOCENTES`, `API_KEY`, and for Upstash Redis (rate limiting + cache):
`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW`,
`CACHE_TTL_CRONOGRAMA`, `CACHE_TTL_DOCENTES`. The API is mounted under `/ids_api`.

`API_KEY` (if set) restricts consumption to the frontend: every request must send `X-API-Key`
with that value. It is shared with `ids-web` and the Bruno collection — rotate it in all of them
at once (see the `manage-secrets` skill).

**Redis (Upstash, REST)** powers two features, both **env-gated** (disabled without credentials)
and **fail-open** (never break the request if Redis is down):
- **Rate limiting** per IP (`before_request` in `app.py` → `ratelimit.py`). With a server-rendered
  frontend, all its traffic shares one IP, so set `RATE_LIMIT_MAX` accordingly.
- **Cache** (`cache.py`): cache-aside for the GETs (`cronograma:clases`, `docentes:filas`),
  **invalidated on every write**. Photos are NOT cached in Redis (only the path); they come from
  the bucket via the in-process `lru_cache` in `services/storage.py`. The public GETs are
  `Cache-Control: no-store` (no CDN caching) so invalidation takes effect immediately.

## Verification (run before considering a change done)

```bash
pip install -r requirements-dev.txt
pytest                                   # ~85 tests, pure functions (no network)
python -m compileall -q ids_api app.py   # syntax check
```

The tests set dummy `SUPABASE_URL`/`SUPABASE_KEY` in `conftest.py`, so they never hit Supabase.
Importing `ids_api.db` creates the Supabase client, so those env vars must be set (even if dummy)
in order to import/test.

## Code conventions

- **Functional style: do NOT use classes.** DTOs and payloads are `dict`.
- **Avoid `break`/`continue`/`pass`** unless strictly necessary or unavoidable (e.g. `pass` in an
  `except`); prefer clear `if`/`else` or `try/except/else`.
- **Spanish naming, no abbreviations** (self-explanatory variables: `error` not `e`,
  `respuesta` not `r`, `indice_semana` not `w`, etc.). The domain vocabulary stays in Spanish.
- **Layers**: `routes → services → validators → db`. Routes hold no business logic; the `db`
  layer uses the Supabase client (query builder), **never raw SQL** from the app.
- **Constants vs config**: `constants.py` = domain constants (roles, types, class period, error
  codes); `config.py` = environment configuration (Supabase, JWT, admin, CORS). Anything shared
  by several modules goes in `constants.py`; module-only values stay local to that module.
- **Errors**: raised as `raise ValueError(construir_error_api(...), status)` (status defaults to
  400) and routes translate them to `jsonify(payload), status`. Payload shape:
  `{"errors": [{"code", "message", "level", "description"}]}`.
- Don't add/remove comments needlessly; mirror the existing style.
- **Any change to the API contract** (endpoints, DTO fields, status codes, `API_KEY`) can break the
  consumer `ids-web` (`../ids-web`). Verify `web/services/*.py` and the templates; if it breaks,
  propose (and, if agreed, apply) the `ids-web` change instead of leaving it broken.

## Domain (gotchas)

- **Cronograma**: the period is defined by `INICIO_CLASES`/`FIN_CLASES` in `constants.py`
  (Mon 2026-08-17 → Mon 2026-11-30). Two classes per week (Monday and Wednesday) → **16 weeks,
  32 classes**. Both GET endpoints (`/cronograma/clases` and `/cronograma/csv`) and the import
  **auto-fill** the missing dates with a default class (`Virtual` / "A definir"); the import
  persists them, the GET only returns them (with a null `id`).
- **CSV**: `semana,fecha,tipo,titulo,desc1,hito1,desc2,hito2,...` (fecha `DD/MM/AAAA`, Mon/Wed).
- **Date validations** (PUT clase and import): must be Mon/Wed within the period; the week is
  derived from the date; the date is unique (409 on clash).
- **Docentes**: `foto` is a base64 data URI (uploaded to a private bucket and returned as
  base64); `email` is unique (409); the list is ordered Profesor → Ayudante → Colaborador;
  `GET /docentes` returns 404 when there are none.
- **Auth**: single admin user via env (no users table); stateless JWT.

## Deploy

- Vercel (`vercel.json`, Python function over `app.py`). Environment variables are set in the
  Vercel dashboard (not via `.env`, which is not committed).

## Do not

- Do not introduce classes.
- Do not run raw SQL from the app (use the Supabase client).
- Do not expose or commit secrets (`.env`, the `service_role` key).
- Do not weaken security controls to work around CI.

## Git

- Commit messages in Spanish, focused on the "why".
- Do not push unless explicitly asked.

## Pointers

- API documented in `docs/swagger.yaml` (OpenAPI 3.0).
- Frontend that consumes it: `../ids-web`.

## Status / known issues

- `listar_docentes` downloads each photo from the bucket (N+1 over HTTP); fine with few docentes.
- CORS open by default (`CORS_ORIGINS=*`); restrict to the frontend domain in production.
