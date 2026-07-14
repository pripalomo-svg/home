# AGENTS.md

## Cursor Cloud specific instructions

This repo is a small **Python 3 + SQLite** project for tracking a family's health-insurance
reimbursements, plus two self-contained static HTML dashboards. All code lives under
`reembolsos/`. See `reembolsos/README.md` for the full workflow and command reference.

### Services / components

- **CLI + data scripts** (Python, stdlib + `openpyxl`): `reembolsos.py` (add/list/update
  claims), `importar_dados.py` (rebuilds `reembolsos.db` from the source spreadsheet/PDF data),
  `gerar_dashboard.py` / `gerar_controle.py` (regenerate the HTML from the DB),
  `importar_controle.py` (apply exported JSON back into the DB).
- **Static dashboards**: `index.html` (read-only viewer) and `controle.html` (editable, saves to
  browser `localStorage`). Both are generated files that embed the DB data — they work offline by
  just opening the file, no server strictly required.

### Running / testing (run from `reembolsos/`)

- There is **no test suite, linter, or build step** — this is a scripts + static-HTML project.
- Quick smoke check of the CLI: `python3 reembolsos.py resumo` and `python3 reembolsos.py listar --ano 2026`.
- To preview the dashboards in a browser, serve the folder statically, e.g.
  `python3 -m http.server 8000` and open `http://localhost:8000/index.html` (or `controle.html`).
  Opening the `.html` files directly via `file://` also works.

### Non-obvious gotchas

- `importar_dados.py` **recreates `reembolsos.db` from scratch**. The generated `index.html` /
  `controle.html` are byte-reproducible, but the SQLite binary file may show a diff (internal
  page ordering) even with identical data — `git checkout -- reembolsos/reembolsos.db` to discard
  a no-op DB change.
- `reembolsos.db` and the generated HTML are **committed on purpose** (see
  `reembolsos/.gitignore`); after changing data, regenerate the panels with `gerar_dashboard.py`
  and `gerar_controle.py`.
- `python3 reembolsos.py add` (and other subcommands) auto-create the DB from `schema.sql` if
  `reembolsos.db` is missing.
- Only third-party dependency is `openpyxl` (used by `importar_dados.py` to read the source
  `.xlsx`); it is installed by the startup update script.
