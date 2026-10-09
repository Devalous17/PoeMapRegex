# Project layout

- `backend/`: Python PoB reader, dependency analysis, ratings, and bundled catalogue/skill data.
- `frontend/`: React/TypeScript source, public images/fonts, and regex tests.
- `api/`: Vercel HTTP entrypoint; imports the shared backend.
- `static/`: generated frontend served locally; rebuilt from `frontend/`, never edited by hand. The current build is committed so a fresh checkout can run with Python.
- `tests/`: analyzer regressions and sanitized PoB fixtures.
- `scripts/`: manual catalogue audit and metadata refresh tools.
- `docs/`: implementation notes and coverage inventory.
- `.vscode/`: editor run/debug settings.
- `server.py`: local HTTP entrypoint.
- `vercel.json`: hosted build settings; Vercel Root Directory is the repository root.

## Local development

From the repository root, `python server.py` serves the site at http://127.0.0.1:8765/.

After frontend edits, run `npm run build --prefix frontend`, then reload the page. Builds replace the generated static directory to avoid keeping old bundles. Original fonts/images live in `frontend/public/`, including their license notice.

For a live frontend preview, run `npm run dev --prefix frontend` alongside the Python server.

## Verification

- `python -B -m unittest discover -s tests -q`
- From `frontend/`: `node --test tests/regexBuilder.mjs`
- `npm run build --prefix frontend`
- `npm run build:vercel --prefix frontend`
- `python -B scripts/audit_normal_catalogue.py` regenerates the audit document.

`frontend/node_modules/`, `frontend/dist/`, and Python bytecode caches are generated/ignored. The package lock, tests, fixtures, catalogue snapshots, and font notices are needed for repeatable builds, validation, or attribution.
