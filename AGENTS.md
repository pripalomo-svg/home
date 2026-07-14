# home

## Cursor Cloud specific instructions

### What this repo is
The only project lives in `reembolsos/`: a local, offline, single-user health-insurance
reimbursement tracker (pt-BR). There is **no web/app server, DB server, or API** — it is
Python 3 CLI/generator scripts + a committed SQLite DB (`reembolsos/reembolsos.db`) + two
self-contained static HTML files (`index.html` read-only dashboard, `controle.html` editable
panel that persists edits to browser `localStorage`).

### Environment
- Runs on Python 3 (3.10+); `sqlite3` ships with Python stdlib.
- Only third-party dependency is `openpyxl`, used **only** by `importar_dados.py` (to rebuild
  the DB from the source `.xlsx`). The update script installs it. Everything else is stdlib.
- There is no package manager manifest, no test suite, and no linter/formatter configured.

### Running / building (all commands run from `reembolsos/`)
Standard commands are documented in `reembolsos/README.md`. Key ones:
- CLI: `python3 reembolsos.py resumo` / `listar` / `add ...` / `atualizar ...` / `importar ...`
- Rebuild DB from spreadsheet: `python3 importar_dados.py` (needs `openpyxl`).
- Regenerate dashboards from the DB: `python3 gerar_dashboard.py` and `python3 gerar_controle.py`.
- View the UI: serve statically with `python3 -m http.server 8000` and open
  `http://localhost:8000/index.html` or `/controle.html` (or just open the HTML files directly).

### Gotchas
- `reembolsos.db`, `index.html`, and `controle.html` are intentionally committed (generated
  artifacts). Re-running `importar_dados.py` rewrites `reembolsos.db` (binary diff) even when
  the data is unchanged; `git checkout -- reembolsos.db` to discard a no-op rebuild.
- Any `reembolsos.py` subcommand except `init` auto-creates the DB from `schema.sql` if missing.
- `controle.html` edits live in browser `localStorage` only; to persist to the DB, export JSON
  and run `python3 importar_controle.py arquivo.json`, then regenerate the panels.
