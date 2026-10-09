# Build analysis model

MapRegex evaluates a saved PoB snapshot. Its purpose is to find modifiers that interfere with the character's usual setup and expose the evidence behind those decisions.

## Ratings and presets

- Brick: a measured sustain requirement fails, a required mechanic is disabled, or an established central recovery/defence setup is severely countered. Some older defence and cooldown rules remain heuristic and are identified as estimates.
- Dangerous: substantial risk or loss, with continued play still possible.
- Uncomfortable: a meaningful comfort or throughput penalty.
- Free: no issue established by the available rule, or a player-selected default policy. It is not a survival guarantee.
- Review: evidence is missing or the mechanic cannot be evaluated from the snapshot.

Greedy excludes Brick. Balanced also excludes Dangerous and breaks measured recovery conflicts. Safe additionally excludes Uncomfortable and Review. Manual decisions take priority over every preset.

## Recovery and resources

`assessment.py` retains regeneration, leech, recharge, recoup, instant leech, flasks, and gain on hit/kill as separate channels. Missing numbers remain null. Recoup percentages and per-hit/per-kill values are never added to per-second income. Recharge is conditional unless the player confirms sustained availability; even then its saved rate is required.

Mana assessment compares saved skill cost with saved regen/leech and any player-confirmed additional income. If the baseline is already short, missing sustain is reported instead of pretending a map modifier caused that deficit. The Life/ES recovery-rate affix does not reduce Mana income. Continuous self-drain is compared with remaining continuous recovery; finite flasks and on-kill recovery do not establish permanent sustain.

Pair checks detect combinations of no-regen, no-leech and reduced recovery that cross a measured cost/self-drain requirement when each modifier alone leaves enough. Balanced/Safe exclude one member. This is not a simulation of every possible map combination or combat event.

## Numeric effects

Critical reduction uses expected hit damage before and after the reduction to extra critical damage. It does not automatically classify a high-crit build as Brick. Damage-over-time and primary-minion contributions remain Review where the hit formula is insufficient.

Maximum-resistance impact uses the actual resistance and maximum cap. A cap can be inferred from a saved positive over-cap value; the evidence source is retained. No cap is assumed solely because the saved actual resistance is 75%. The resulting damage-taken ratio excludes conversion, penetration and other mitigation.

`map_rule_values.json` contains pool-specific worst rolls extracted from the project's PoEDB catalogue, including normal/nightmare crit reduction, maximum resistance, recovery and leech-cap penalties. Player-entered increased map effect scales these penalties. Fractional scaling is an approximation; detailed in-game rounding and additive leech-cap modifiers are not fully recalculated.

## Player confirmations

The recovery panel allows optional confirmations of additional Mana income, sustained recharge, Hexproof bypass, curse and aura roles, essential flask uptime, charge sustain, and increased map modifier effect. These are validated by the shared local/Vercel request service, apply only to that imported build, and remain in browser memory. No telemetry or override logging is added.

Hexproof does not affect Marks. Reduced curse effect does not inherently disable curse application or Impending Doom triggers. Curse contribution remains unknown unless confirmed. Full aura/curse/flask contribution comparisons require the PoB calculation engine or separately calculated snapshots; the app does not fabricate those comparisons.

## Regex correctness

The frontend checks candidates against full modifier/reward text and every integer combination of catalogue roll ranges, including signed ranges. A selected pattern must cover every roll of its selected modifiers and none of the unselected modifiers. The query keeps all required exclusions even when it exceeds 250 characters; copying remains disabled on overflow. Risk/frequency ranking must not silently omit required exclusions.

## Validation and remaining work

The regression set contains seven sanitized, user-supplied character snapshots (Winter Orb, Armour stacker, Righteous Fire, Vaal Righteous Fire, Storm Burst spell totems, Death Aura, Viper Strike of the Mamba), 32 synthetic mechanic scenarios, and the original parser/rule tests. These are not 20 independently verified full character builds.

Further work needs labeled full PoBs across more archetypes, measured flask/charge uptime, a PoB calculation integration for contribution comparisons, and encounter-specific assumptions for absolute damage/survival headroom. Estimated map exclusion percentages need a valid roll-distribution model; spawn weights alone are insufficient. The 55 normal affixes previously marked Free by player policy retain that policy until reviewed. Nightmare rules outside measured groups still require review.

Sources: [PoB calculation code](https://github.com/PathOfBuildingCommunity/PathOfBuilding/tree/dev/src/Modules), [PoEDB normal maps](https://poedb.tw/us/Maps_top_tier), [PoEDB Nightmare maps](https://poedb.tw/us/Nightmare_map).

## Totems and block investment

Main-skill totem detection checks linked supports, supports supplied by the equipped item socketing that skill, and native totem skills. Ancestral Bond (41970) and Mind over Matter (34098) are read from the active allocated tree. A utility Decoy Totem alone does not reclassify another main skill.

The requested block policy rates reduced block as Brick when saved effective attack block plus saved effective spell block reaches 75 percentage points. This sum measures investment for this policy; it is not a combined probability of blocking a hit. The normal catalogue currently couples 40% reduced block with 30% less Armour.

Spell-totem accuracy is independent of player Accuracy. Main totems without a detected cooldown dependency do not automatically avoid cooldown recovery penalties; utility cooldowns can still slow down. Optional ailments on elemental-hit totems are allowed unless saved Ignite damage or linked ailment-scaling supports establish a dependency. Unmeasured ailment interactions and totem Thorns survival still need review.

Recovery-source detection distinguishes flask base types from incidental modifier text. A Life flask which removes Mana is not counted as a Mana flask. No-regen ratings still depend on measured resource costs and remaining sustain rather than the presence of totems alone.

## Primary damage auras

The selected Death Aura skill is recognized independently of the granting item's name as non-attack chaos damage over time. Its primary damage aura signal is visible in the recommendation evidence. Reduced non-curse aura effect is excluded as Brick by the core-skill policy, including in Greedy. This is a conservative core-damage exclusion, not a calculated guarantee that damage reaches zero or the map is impossible. Reduced and increased aura effect combine additively; atlas modifier effect can amplify the penalty. Supporting auras alone do not prove a Brick. Curse auras and Righteous Fire are not classified as Death Aura-style damage auras. Disabled socket groups do not establish enabled aura presence.

Death Aura does not critically strike or hit; main-skill crit reduction, player accuracy and Thorns are therefore Free, subject to reviewing secondary hit skills.

Sources: [PoB Death Aura skill metadata](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Data/Skills/other.lua), [Death Aura scaling](https://poedb.tw/us/Death_Aura).

## Shared dependency coverage

`dependencies.py` enriches the active selected skill with 701 bundled PoB active-skill records (spell/attack, delivery, channel, aura, curse, cooldown and hit/DoT tags). `skill_metadata.json` records its exact upstream commit and source-file hashes. `scripts/update_skill_metadata.py` is a manual maintainer refresh; imports work offline and never execute remote Lua. Skill recognition is not equivalent to full calculation support. Unrecognized enabled skills remain visible.

Each build receives delivery, scaling, activation, sustain and defence evidence. Main-skill supports and the equipped socketing item establish trigger dependencies; utility groups alone do not. Explicit per-attribute/pool item scaling is recorded without estimating contribution from attribute presence alone. Pure DoT and mixed hit/DoT skills are distinguished.

Selected Hex + Impending Doom without bypass is a core activation counter. Selected cooldown triggers retain conservative Brick policy; native cooldowns without a demonstrated core loop remain Review. Saved majority Ignite DPS is Dangerous under ordinary avoidance and Brick when scaled elemental ailment avoidance reaches 100%; Poison/Bleed are not misclassified as elemental ailments. These thresholds do not simulate secondary skills or boss uptime.

All 78 current normal catalogue entries have an assessment path. `modifier_rules.json` and `normal_free_policy.json` are shared between the backend and frontend; `normal_catalogue.json` is an offline normal-pool snapshot. `scripts/audit_normal_catalogue.py` generates the full inventory in `docs/normal-modifier-audit.md`. Regression checks must keep that snapshot synchronized with the frontend corpus. The 54 remaining user-reviewed Free entries remain policy allowances, explicitly distinct from verified unaffected interactions. This audit does not claim all of their possible build-specific interactions are implemented.

Assessments expose counter/unaffected/uncertain/policy status, affected dependency axes and evidence. Unknown main-skill dependencies cannot produce absence-based Free results for relevant offensive rules. Equipped flasks outside Pathfinder/Traitor are Review until their necessity is confirmed. Missing evidence is not zero. The UI surfaces detected dependencies and unresolved checks both in the profile and beside the copyable regex; Greedy still blocks Brick only and manual decisions remain authoritative.

Validation now includes all seven saved user builds, recognition scenarios across melee, bows, spells, brands, minions, totems, traps, mines, DoT, triggers and explicit stacking, plus the existing sustain/defence tests. Full PoB contribution recalculation, uptime and encounter-specific lethal thresholds remain unimplemented. A recognized build and a complete catalogue inventory are a baseline, not proof that every allowed map is survivable.

## Poison, Bleeding and Impale avoidance

The normal Impervious modifier (`-627831782`, short pattern `son,`) now has its own `avoid_poison_bleed_impale` rule and is removed from the blanket Free policy. It must not be conflated with elemental ailment avoidance. Majority saved Poison/Bleeding damage makes avoidance a conservative Brick exclusion even below immunity, because unreliable primary damage application interrupts usual mapping. Majority Impale contribution is Dangerous below immunity; scaled avoidance reaching 100% makes it Brick. Selected Viper Strike of the Mamba with established majority poison damage receives a conservative Brick exclusion even below immunity because unreliable initial poison application disrupts usual mapping. This policy does not claim 50% avoidance literally prevents all poison or proves the character cannot finish the map. Manual choices still win.

Missing or secondary contribution remains Review, rather than being promoted from a skill name alone. Direct non-ailment DoT is distinguished from hit-applied ailments. Mamba is identified from the selected main skill, so a utility Mamba gem cannot create a core poison dependency.

PoB can save uncapped Poison DPS beside capped CombinedDPS. Corresponding hit-plus-ailment totals are included in the comparison reference to avoid presenting an impossible 176% contribution. These saved quantities remain estimates, not a live damage recalculation. The supplied Mamba fixture and generic poison/bleed/impale, scaled-roll, missing-data, manual-override and numeric-evidence cases are regression tested.

Skill source: [PoB Viper Strike of the Mamba data](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Data/Skills/act_dex.lua).

## Offensive application and conditional scaling

Primary saved Ignite, Poison and Bleeding damage now conservatively exclude their corresponding avoidance modifier in every preset, including Greedy. Below 100% avoidance this is an application-reliability policy, not a mathematical assertion of zero damage. Impale remains separately assessed. The scaled catalogue roll is passed to elemental avoidance exactly once.

Linked main-skill Hypothermia and equipped damage/crit modifiers explicitly conditioned on chilled, frozen or shocked enemies are recorded as conditional scaling dependencies. Elemental avoidance is Dangerous when these bonuses are established, rather than Free merely because the main damage is not Ignite. Utility supports do not establish a main dependency. A lost conditional bonus is not automatically proof of a Brick; its contribution and alternate ailment sources remain unmeasured. Direct cold DoT's unconditional Hypothermia bonus is not treated as requiring chill.

The current catalogue does not contain the quoted fewer-traps/mines, monster status immunity or base 100%-reduced-extra-crit legacy affixes. They are not silently added to the current pools. Existing current crit reductions use the damage factor; core triggers and resource sustain are evaluated separately.

Mechanic references: [PoB Hypothermia data](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Data/Skills/sup_dex.lua), [PoB Heatshiver data](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Data/Uniques/helmet.lua).

## Non-cooldown main damage and Safe exclusions

Recognized main skills without a cooldown, core trigger, Wardloop or mine-detonation dependency now rate reduced cooldown recovery Free for normal damage delivery. Safe no longer blocks it merely because generic missing-signal handling returned Review. Utility movement/guard uptime remains unmeasured; this is not proof of full defensive uptime. Native cooldown skills stay Review, known core trigger policies stay Brick, and unrecognized main skills stay Review. The supplied strength-stacking Kinetic Blast snapshot is a regression fixture. Equipped attribute-scaling evidence is deduplicated.

Coverage target: build a dated, league-specific sample from poe.ninja, group by delivery + scaling + activation + sustain (not skill name alone), and validate representative and held-out real exports for groups covering at least 90% of the sampled characters. Report false Brick exclusions and missed labeled Brick interactions separately. This target is not yet measured and does not establish coverage of all public players.
