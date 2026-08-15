---
name: sync-bruno
description: Keep the Bruno API collection in sync with the API's endpoints and request/response formats
allowed-tools:
  - read
  - edit
  - write
  - grep
  - glob
permissions:
  allow:
    - Read(**)
  ask:
    - Write(**)
---

Keep the Bruno collection in sync with the current API. Use this after adding/changing/removing
endpoints or changing request/response shapes.

## Reference the source of truth

1. Read `docs/swagger.yaml` and the routes in `ids_api/routes/` to get the current endpoints,
   methods, auth requirements, bodies and status codes.

## Update the collection

The Bruno collection lives in a separate repo (typically
`../../bruno-workspace/ids-api-collection`, mirrored under `bruno/` here). For each change:

- **New endpoint** → add a `.bru` request in the matching folder (Auth / Docentes / Cronograma),
  with method, URL (`{{baseUrl}}` + `/ids_api/...`), headers, and an example body.
- **Admin endpoints** → include `Authorization: Bearer {{token}}` and rely on the collection's
  login/auth setup that populates `{{token}}`.
- **Changed body/format** → update the request body and any example (e.g. CSV multipart field
  `archivo`, docente `foto` as a base64 data URI, cronograma date format `DD/MM/AAAA`).
- **Removed endpoint** → delete the corresponding `.bru`.
- Keep environment variables (`baseUrl`, `token`) consistent across requests.

## Verify

- Every endpoint in `swagger.yaml` has a matching request in the collection, and there are no
  requests pointing to endpoints that no longer exist.
- Report which requests were added, changed, or removed.
