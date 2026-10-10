"""One request contract for the local server and Vercel function."""

from .assessment import validate_assumptions, recovery_conflicts
from .pob import BuildInputError, build_profile, decode_build
from .rules import REGEX_LIMIT, classify, make_regex
from .build_signals import infer_build_signals


def analyze_request(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("source"), str):
        raise BuildInputError("Paste a pobb.in link or a PoB export code.")
    try:
        assumptions = validate_assumptions(data.get("assumptions", {}))
    except ValueError as exc:
        raise BuildInputError(str(exc)) from exc
    profile = build_profile(decode_build(data["source"]))
    profile["assumptions"] = assumptions
    profile["signals"] = infer_build_signals(profile)
    profile["recovery_conflicts"] = recovery_conflicts(profile)
    mods = classify(profile)
    from .catalogue_audit import audit_catalogue
    profile['coverage']['issues'] = [issue for issue in profile['coverage']['issues']
        if not (issue.startswith('Supporting aura') and assumptions.get('aura_role', 'unknown') != 'unknown')
        and not (issue.startswith('Hex contribution') and assumptions.get('curse_role', 'unknown') != 'unknown')]
    audit = audit_catalogue(mods)
    profile['coverage']['normal_modifiers'] = audit['summary']
    mods.extend(audit['assessments'])
    # Deduplicate catalogue-specific overrides before reporting and serving them.
    mods = list({row['id']: row for row in mods}.values())
    from .reporting import enrich_assessments, assessment_report
    from .nightmare import assess_nightmare
    nightmare = assess_nightmare(profile, mods)
    ids = {row['id'] for row in nightmare}
    mods = [row for row in mods if row['id'] not in ids] + nightmare
    profile['coverage']['nightmare_modifiers'] = {rating: sum(row['rating'] == rating for row in nightmare) for rating in ('brick','dangerous','uncomfortable','free','review')}
    enrich_assessments(profile, mods)
    report = assessment_report(profile, mods)
    profile['assessment_summary'] = report['summary']
    return {"profile": profile, "mods": mods, "assessment_report": report,
            "presets": {preset: make_regex(mods, preset) for preset in ("safe", "balanced", "greedy")},
            "regex_limit": REGEX_LIMIT}
