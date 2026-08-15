---
name: generate-admin-credentials
description: Generate the bcrypt hash for ADMIN_PASSWORD and a random JWT_SECRET for the .env
allowed-tools:
  - exec
permissions:
  allow:
    - Exec(python*)
---

Generate admin credentials / secrets for the `.env`. **Never** print or commit real secrets into
tracked files — only output them for the user to paste into their local `.env`.

## Steps

1. Ask the user for the desired admin password (or let them run the command themselves).

2. Generate the **bcrypt hash** for `ADMIN_PASSWORD` (the app stores the hash, not the plaintext):
   ```bash
   python -c "import bcrypt; print(bcrypt.hashpw(b'THE-PASSWORD', bcrypt.gensalt()).decode())"
   ```

3. Generate a random **`JWT_SECRET`**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Tell the user to set in `.env` (which is gitignored):
   ```
   ADMIN_USER=admin
   ADMIN_PASSWORD=<bcrypt hash from step 2>
   JWT_SECRET=<value from step 3>
   ```

## Notes

- On Vercel, set these as environment variables in the dashboard, not via `.env`.
- Do not write the generated values into `.env.example`, README, or any committed file.
