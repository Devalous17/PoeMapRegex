# Build validation workflow

## Purpose

Each correction should become a reusable dependency rule and a labeled regression case. We track missed requested Brick exclusions and unnecessary exclusions separately. Passing a label is agreement with that label, not proof of in-game safety.

## Run the complete saved-build check

From the repository root:

```powershell
python -B scripts/validate_builds.py
python -B scripts/validate_builds.py --output reports/build-validation.json
python -B scripts/audit_free_policy.py --output docs/free-policy-audit.md
```

The report includes every current normal and Nightmare modifier for every saved build, evidence, ratings, estimate inputs/outputs, assumptions and model limitations. Unknown Nightmare interactions remain unknown. Duplicate modifier IDs are consolidated before reporting.

The command exits unsuccessfully when a label fails or a fixture's content changes without its recorded hash being reviewed. This supports CI and agent workflows. A changed fixture must have its labels reviewed before updating the recorded hash.

## Add a correction

Save a PoB export code in a local text file, then supply the expected decision and its reason:

```powershell
python -B scripts/add_regression_build.py "C:\path\build.txt" --name example_attack --expect reduced_cooldown=free --rationale "The main attack has no cooldown dependency; the cooldown skill is utility only."
python -B scripts/validate_builds.py
```

Use an existing rule ID (for example `no_regen`) or catalogue ID (`map--627831782`). Multiple `--expect` arguments are supported. XML exports are also accepted. The helper validates the export locally, removes Notes and nonessential sections, preserves skill, item-slot and configuration attributes, and does not upload the build. Existing fixtures cannot be overwritten accidentally.

Label origins are `reviewer_judgment`, `in_game_test`, and `conservative_policy`. Do not use `in_game_test` without actually testing the interaction. The initial labels preserve earlier user requirements; they are not fabricated combat observations.

`--split holdout` is available for independently collected cases that have not been used to design rules. The original eight builds are development cases because they have already influenced the implementation. A holdout case loses that independence once its result is used to tune a rule; move it to development and collect a replacement.

## Assessment basis

- `snapshot_model`: a bounded numerical estimate from saved stats.
- `dependency_rule`: a detected dependency or explicit mechanic rule.
- `user_confirmation`: the user supplied missing role information.
- `conservative_policy`: an exclusion protecting usual play without proving total failure.
- `policy_allowance`: a historical Free allowance that is not a safety proof.
- `unknown`: insufficient information or unsupported interaction.

Severity, confidence, basis and quantities are separate fields. The website explains the basis in modifier explanations and provides counts in the build profile. Manual decisions still take priority. Existing presets are preserved.

## Calculation capabilities

Currently implemented models cover expected main-hit critical damage, resistance-only damage-taken factors, measured recovery and skill-cost surplus, and the probability of passing an ailment-avoidance check. Missing values remain missing. Poison avoidance is not treated as elemental avoidance. Avoidance pass probability is not a DPS multiplier.

These are **saved-snapshot models, not a full PoB recalculation**. Unsupported cooldown timing, supporting aura/curse contribution, alternative resources, entity durability and condition uptime remain uncalculated. The API states this explicitly.

A full-engine integration still requires a pinned Path of Building checkout, its Lua runtime/dependencies and a tested adapter. No Lua/LuaJIT runtime is installed in the current environment. The upstream [headless wrapper](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/HeadlessWrapper.lua) supports XML loading; this does not establish that all map effects can be applied correctly or that its native dependencies run inside Vercel. Validate that integration separately before presenting results as full-engine calculations.

## Population coverage

The manifest records sample provenance, league/date/population fields and whether sampling weights exist. The current user-provided set has no population weights and no independent holdout set. Reports therefore return `population_coverage_percent: null`.

To measure the 90% target, collect a dated league sample, group by delivery/scaling/activation/sustain, label representative and held-out builds, and assign documented sampling weights. Validate variants across budgets/configurations. Main-skill popularity alone cannot establish interaction accuracy. Report held-out failures and unreviewed interactions alongside any future coverage figure.

## Next implementation queue

The full Free-policy audit identifies all 54 allowances and their unanswered questions. Highest-priority topics include required buff uptime, Exposure, enemy suppression/resistances, Blind, player curses, and taunt/slow dependencies. Their presence in this queue does not automatically justify a Brick rating.

## Targeted cooldown and curse exclusions

For a 60% or greater Life/ES recovery penalty, substantial regeneration reliance is a Balanced exclusion: regeneration provides at least half of measured continuous recovery and at least 3% of the affected pool per second. This is a conservative policy, not proof of failure. A measured deficit against ongoing self-drain remains Brick. Mana-only regeneration is not reduced by the current Life/ES affix; mana builds are assessed using their affected Life/ES recovery. The uploaded RF Chieftain is saved as an additional regression case.

Recognized main skills use their own cooldown metadata; a saved global Cooldown stat and utility guard/movement skills do not create a primary cooldown dependency. CoC, equipped socketed triggers, Wardloop, mine detonation and native main-skill cooldowns remain assessed. Cast while Channelling alone uses a trigger interval and does not establish a CDR dependency; an independently cooldown-based triggered spell can still be affected.

Ordinary damage/utility curses are allowed in all presets by default, even with two enabled Hexes. A confirmed core curse mechanic, selected Hex with Impending Doom, or Anathema with more than two enabled Hexes remains assessed. Reduced curse effect does not inherently disable curse triggers. These allowances follow the requested selection policy and do not prove zero damage loss.
