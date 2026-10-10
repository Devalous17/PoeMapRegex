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

See [Build validation](build-validation.md) for labeled build checks, adding corrections, and current calculation limitations.

See [Nightmare coverage](nightmare-coverage.md) for all 47 entries, example outcomes, and remaining interaction gaps.


## Preset relevance and Accuracy scaling

Unknown ratings remain Review in every preset and are not automatically excluded.
They are not declared Free; the regex output warns about unreviewed modifiers.
Manual block/allow choices still override every preset, and measured recovery
conflicts are excluded by Balanced and Safe.

Accuracy-based offensive modifiers on equipped items establish an attack scaling
dependency even at capped hit chance or with Hits cannot be Evaded. Less Accuracy
is a Balanced exclusion for this dependency; no exact total DPS loss is claimed.
Accuracy bonuses alone and unequipped scaling items do not establish this dependency.

Balanced excludes estimated critical hit-damage losses of at least 25%; this is an
explicit comfort policy, not proof of a Brick. A substantial Life/ES recovery loss
of exactly 60% now enters Balanced instead of slipping through a strict comparison.
The existing regeneration policy and user-reviewed Nightmare decisions remain.
The Accuracy-stacking Reave export is a sanitized development regression, not
independent evidence of population-wide accuracy.


## Marginal modifiers are not automatic exclusions

The visible Safe preset is now Maximum Filtering (internal API ID `safe`).
Uncomfortable ratings alone no longer select a modifier. Explicit `strict_avoid`
marks detected charge/AoE dependencies and the user's reviewed optional Nightmare
exclusions. Measured recovery conflicts still take precedence. Major risks remain
in Balanced; manual decisions always win. Unknowns remain Review.

Ordinary flask use does not establish charge dependence. Recognized main skills
without primary/specialized ailment scaling receive an optional-mechanic allowance
for ailment avoidance, labelled as policy rather than a measured absence of risk.
Unmeasured specialized ailment setups remain Review. Primary Ignite, Poison,
Bleeding/Impale and detected conditional ailment scaling retain their exclusions.
