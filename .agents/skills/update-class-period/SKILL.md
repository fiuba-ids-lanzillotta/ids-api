---
name: update-class-period
description: Update the cronograma class period (INICIO_CLASES / FIN_CLASES) and remap the seed dates and tests for a new cuatrimestre
argument-hint: "[first-monday DD/MM/YYYY] [last-monday DD/MM/YYYY]"
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
    - Exec(python*)
  ask:
    - Write(**)
---

Update the class period for a new cuatrimestre. The period drives the number of weeks and classes
(2 per week: Monday and Wednesday → 16 weeks → 32 classes).

Arguments: **$ARGUMENTS** = the Monday of the first week and the Monday of the last week
(format `DD/MM/YYYY`). If not provided, ask the user for both dates and confirm they are Mondays.

## Steps

1. **Validate the dates.** Both must be Mondays. Compute the number of weeks:
   `((last_monday - first_monday).days // 7) + 1`. Confirm it matches the intended term length.

2. **Update `ids_api/constants.py`:**
   ```python
   INICIO_CLASES = date(YYYY, M, D)   # Monday of the first week
   FIN_CLASES    = date(YYYY, M, D)   # Monday of the last week
   ```

3. **Remap the seed in `db/init_db.sql`.** The old dates appear in the `INSERT INTO clases` block
   AND in the `contenidos` inserts (referenced as `WHERE fecha = '...'`). Each of the 32 ordered
   dates (week 1 Mon, week 1 Wed, week 2 Mon, ...) maps 1:1 to the new ordered dates. Generate the
   mapping and replace every occurrence globally. Example generator:
   ```python
   from datetime import date, timedelta
   inicio = date(YYYY, M, D)  # first Monday
   nuevas = []
   for semana in range(16):
       lunes = inicio + timedelta(weeks=semana)
       nuevas += [lunes.isoformat(), (lunes + timedelta(days=2)).isoformat()]
   # zip old ordered dates -> nuevas, then str.replace each in db/init_db.sql
   ```
   After remapping, confirm **0** old dates remain and the new first/last dates are present.

4. **Update the tests** in `tests/test_cronograma.py` that assert concrete dates
   (`test_semanas_esperadas`, `test_semana_de_fecha`) so the expected values match the new period.

5. **Update docs** if the dates are mentioned: `README.md` (period section) and the CSV example,
   and the `fecha` examples in `docs/swagger.yaml`.

6. **Verify:**
   ```bash
   pytest
   python -m compileall -q ids_api app.py
   ```

## Notes

- `_semana_de_fecha` and `semanas_esperadas` derive everything from the constants, so no service
  code changes are needed — only the constants, the seed, the tests, and the docs.
- Any class already stored outside the new period becomes invalid; a fresh `db/init_db.sql` run (or
  a `PUT /cronograma/csv`) re-materializes the schedule.
