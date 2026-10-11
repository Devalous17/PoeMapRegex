# MapRegex flat frontend restyle

The original supplied background has been restored. This is the deliberate exception
to the attached brief's no-background-art rule, following the user's direct request.
The analyzer, catalogues, presets, store, regex generation, fixture, tour steps, FAQ
and page ordering are retained. The fixture tests verify identical recommendations,
selected modifiers, warnings, character limits and generated searches.

## Completed phases

1. Removed generated crests, wings, arches, corners, constellation artwork, fog and
   particle components. Removed gradients, blurred shadows and glows from styles.
   Restored `627187.jpg` from the project backup; no generated replacement artwork.
2. Defined a warm solid palette. Kept self-hosted Cormorant SC for headings and
   Crimson Pro for body text, both licensed under SIL OFL 1.1. Licenses ship with the
   fonts. No Fontin files or external font service are used.
3. Replaced the ornate stylesheet with flat controls: plain header, centered headings,
   straight rules, square panels, crimson actions and consistent selected states.
   Kept the existing layout, filters, selected-mod window and sticky output.
4. Added 13 distinct local Game-icons assets, their author manifest, swap instructions,
   and a footer-linked `/credits.html` page. No game UI icons are used.
5. Added short arrival/reveal transitions and a solid color flash when the regex changes.
   Copy feedback says “Copied!”. Reduced-motion rules remove movement and transitions.
6. Corrected mobile hero readability with an opaque text panel, removed remaining
   preset corner decorations, checked selected-row contrast and keyboard navigation,
   and recorded responsive layout assertions and before/after images.

## Palette

| Role | Hex |
| --- | --- |
| Page | #16130F |
| Panel | #221E18 |
| Raised | #2C2720 |
| Subtle border | #443B2D |
| Bronze border | #6B5A3A |
| Gold / active border | #C8A96A |
| Heading | #E6D49A |
| Body | #D8CFBC |
| Secondary | #B5AB98 |
| Primary / hover | #8A1C26 / #A42A35 |
| Avoid / caution / neutral / free markers | #C0392B / #D4A017 / #6C7FD8 / #4A9D5B |
| Readable rating text: brick / danger / uncomfortable / free / review | #F1A299 / #E8BD56 / #D8C590 / #9ACD9F / #ADB9F2 |
| Selected avoid / want / active surface | #38221E / #202F24 / #393224 |

All controls use square corners, opaque surfaces and simple borders. Primary text
contrast on the panel surface: body 10.71:1, secondary 7.3:1, heading 11.25:1, gold 7.37:1. These exceed AA normal-text contrast;
this is a palette and targeted keyboard/layout check, not a full WCAG certification.

## Icons

[Game-icons license](https://game-icons.net/about.html) was verified on 2026-10-11.
All icons below use [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
White fills were changed to `currentColor`; CSS masks tint silhouettes gold.

| Use | Source | Author | License |
| --- | --- | --- | --- |
| thorns | [thorny-vine](https://game-icons.net/1x1/lorc/thorny-vine.html) | Lorc | CC BY 3.0 |
| recovery | [bleeding-heart](https://game-icons.net/1x1/lorc/bleeding-heart.html) | Lorc | CC BY 3.0 |
| cooldown | [stopwatch](https://game-icons.net/1x1/lorc/stopwatch.html) | Lorc | CC BY 3.0 |
| defences | [bordered-shield](https://game-icons.net/1x1/lorc/bordered-shield.html) | Lorc | CC BY 3.0 |
| resistances | [fire-shield](https://game-icons.net/1x1/lorc/fire-shield.html) | Lorc | CC BY 3.0 |
| charges | [lightning-trio](https://game-icons.net/1x1/lorc/lightning-trio.html) | Lorc | CC BY 3.0 |
| ailments | [poison-bottle](https://game-icons.net/1x1/lorc/poison-bottle.html) | Lorc | CC BY 3.0 |
| monsters | [daemon-skull](https://game-icons.net/1x1/lorc/daemon-skull.html) | Lorc | CC BY 3.0 |
| area | [treasure-map](https://game-icons.net/1x1/lorc/treasure-map.html) | Lorc | CC BY 3.0 |
| other | [cog](https://game-icons.net/1x1/lorc/cog.html) | Lorc | CC BY 3.0 |
| import | [scroll-unfurled](https://game-icons.net/1x1/lorc/scroll-unfurled.html) | Lorc | CC BY 3.0 |
| copy | [files](https://game-icons.net/1x1/delapouite/files.html) | Delapouite | CC BY 3.0 |
| help | [book-aura](https://game-icons.net/1x1/lorc/book-aura.html) | Lorc | CC BY 3.0 |

Replace `frontend/public/icons/<use>.svg` with a transparent square SVG using the same
filename, update the manifest and credits, then rebuild. See the shipped icons README.

## Validation

- Build and TypeScript checks passed after each phase commit. This repository has
  no lint command or linter configuration; TypeScript and whitespace checks were used.
- Existing backend and frontend fixture checks passed after every phase commit;
  expected fixture data and protected functional sources were not rewritten.
- Responsive checks passed in manual and imported Winter Orb views at requested
  viewport widths 360, 768, 1280 and 1920. The scrollbar occupies 9 pixels.
- Header container and section-heading center error: at most 0.008 pixels.
- Multi-card row height difference: 0 pixels. No horizontal overflow or visible
  gradients, shadows or blur detected. See the JSON measurements beside this file.
- `frontend/tests/flatLayout.mjs` exports the read-only `measureLayout` assertion used
  through the browser preview. Re-run it with a blank page state and after importing
  the example at each width. Call `page.evaluate(measureLayout)` in a Playwright harness
  or evaluate its function text with the desktop browser's read-only evaluator.
- UI checks: category filtering, selected-mod toggle, numeric quantity update,
  exact clipboard equality, mobile navigation, tour Next and Escape, credits page.
  No browser console errors were observed.

## Screenshots

| Width | Before | After |
| --- | --- | --- |
| 360 | [Before](flat-restyle/before-360.jpg) | [After](flat-restyle/after-360.jpg) |
| 1440 | [Before](flat-restyle/before-1440.jpg) | [After](flat-restyle/after-1440.jpg) |

[Modifier database](flat-restyle/after-modifiers-1440.jpg)

## Remaining observations

1. The supplied artwork has a cyan character on a black background. That is retained
   deliberately alongside the warm bronze UI; mobile uses an opaque text panel.
2. The map database remains long and dense because its features and layout were kept.
3. Vite still reports a JavaScript chunk over 500 kB (about 125 kB gzip). That is an
   existing bundle-size warning, not a build failure. No Lighthouse score is claimed.

Changes are committed locally in the requested six phases. They are not pushed or deployed.
