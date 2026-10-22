# Compact MapRegex redesign

## Visual direction

The supplied 1024px reference is the basis for the new workbench. The large hero and
landing-page section order have been replaced by compact import controls, search,
Normal/Nightmare tabs, a 60/40 selection-and-regex layout, and vulnerability and
analysis panels. Existing database, preferences, build confirmations, defensive
summary, tour, FAQ and export remain available below the workbench.

## Supplied assets and fonts

- 23 transparent PNG crops came directly from the supplied UI sheet. The existing
  alpha channel was preserved. Crop rectangles are recorded in
  `frontend/public/assets/ui/asset-map.json`.
- Bronze, amber and crimson buttons, the regex title frame, colored risk tags and
  lower panel frames use CSS nine-slice borders to preserve corner proportions.
- A dark atmospheric background tile was extracted from the supplied panel interior.
- Fontin SmallCaps is self-hosted for navigation, major actions and the regex title.
  The original unmodified Fontin files were recovered from this project's earlier
  backup. The foundry's font-face attribution is placed beside the declarations.
  Original font notices are preserved and the credits page links the
  [foundry's web embedding terms](https://www.exljbris.com/eula.html).
- Regular controls use Arial for legibility. No new generated illustration or line
  ornament was created.

## Adaptations to supported features

- Normal maps (T16) and Nightmare maps (T17) are the supported pools. Unique-map and
  Waystone selectors were not added. The top-tier-roll label explains catalogue scope;
  no unsupported item-level filter is presented.
- NOT/Avoid and AND/Want share the existing database selection handlers. Avoiding any
  selected mod and requiring every wanted mod preserve existing regex semantics.
  Arbitrary nested OR groups were not added as visual-only controls.
- Min/max controls remain in Map preferences, where they affect the generated regex.
- Generated Regex is live. Generate Regex submits the existing PoB analyzer. Import
  opens the URL/export field; the field collapses after successful analysis.
- Reset clears the import field and restores modifier choices and map preferences.
  The saved analyzed build remains available; the button tooltip describes its scope.
- Risk tags are derived from the current build's blocked, assessed modifiers. Labels
  such as No Regeneration and Elemental Thorns are presentation labels for actual mods,
  not permanent example results.
- The desktop output follows the viewport while scrolling. Lower editing controls
  occupy the left column to reserve space for it. On mobile the panels stack and the
  output scrolls normally.

## Exile-UI reference

Reviewed [Lailloken/Exile-UI](https://github.com/Lailloken/Exile-UI), especially the
[map-info panel](https://github.com/Lailloken/Exile-UI/wiki/Map-info-panel), as an
additional reference for compact categorized map information and difficulty markings.
It is an AutoHotkey desktop overlay, so no overlay code or assets were imported.
Its repository has an [MIT license](https://github.com/Lailloken/Exile-UI/blob/main/LICENSE.md).

## Validation

- Production and Vercel builds and TypeScript checks pass. There is no configured lint
  script in this project; TypeScript and whitespace checks are used.
- Existing 23 frontend regex tests pass.
- The saved backend and frontend regression fixtures pass unchanged: same parsed build,
  modifier ratings, selections, warnings, character limits and searches.
- Protected backend, API, catalogue, store, regex services and type files are unchanged.
- Browser checks: malformed export error, successful raw export import, modifier search,
  manual block/removal, positive wanted term, Normal/Nightmare switching, Greedy/Balanced,
  numeric quantity updates, exact clipboard equality and desktop floating output.
- 360, 768, 1024 and 1440px checks found no horizontal overflow. Measurements and
  screenshots are beside this document. Fontin SmallCaps requests returned HTTP 200/304.
- No browser console errors were observed during the final checks.

## Review images

- [1024px desktop reference size](compact-redesign/desktop-1024.jpg)
- [1440px desktop](compact-redesign/desktop-1440.jpg)
- [768px tablet](compact-redesign/desktop-768.jpg)
- [360px mobile](compact-redesign/desktop-360.jpg)

Vite retains its existing warning about the main JS chunk exceeding 500 kB. The bundle
is approximately 125 kB gzip. No performance score or guarantee of map safety is claimed.
This work is local and has not been pushed or deployed.
