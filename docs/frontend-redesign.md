# MapRegex frontend redesign

## Scope and stack
MapRegex is an English Path of Exile 1 map-search tool. Only the presentation changed.
The app uses React, TypeScript and Zustand; Vite produces static assets.
The local Python server serves these assets and performs PoB analysis.
Vercel uses the existing Python API and the Vercel frontend build.
Existing CSS provides structural rules; tokens.css and redesign.css supply the new theme.
No npm dependencies, paid services, analytics or accounts were added.

## Reference analysis
1. Hero/nav: near-black surround, navy atmosphere, centered small-cap gold title, split metal navigation, crimson framed CTA and gold secondary plates.
2. Classes: large open spacing, warm gold typography and circular selectors with a brighter active ring.
3. Atlas panels: bronze double frames, scroll corners, dark vignette, asymmetric content inside a wide frame.
4. Equipment/endgame: dark negative space, large serif headings, crest plaques and framed content.
5. World: tall gothic arches, tracery, a dark inner text plate, arrow cues and diamond pagination.
The new UI interprets these with original SVG geometry rather than GGG illustrations, logos, statues or icons.

## Changes by area
A. Tokens/fonts: self-hosted Cormorant SC headings and Crimson Pro body, with SIL Open Font License files. Fontin's included readme requires permission for online redistribution; the old files were removed from public/static assets. Cormorant SC provides the reference's small-cap silhouette and sharper display contrast; Crimson Pro is denser and clearer in controls than Cormorant body text. Compared visually against the supplied screenshots; these are substitutes, not identical fonts.
B. Frames: original crest, arch tracery, corners, scrolled nav ends, inset plaques, bottom emblems, medallion glyphs, diamond pager and patterned footer. The existing original folded-map regex emblem stays as the app identity.
C. Structure: centered hero, clickable step plates, three-step instructions, import panel, sticky output, presets, modifier workspace, preferences, defence profile and FAQ. Dead community placeholders were replaced with useful guide/privacy links.
D. Motion: CSS mist, twelve embers, hero arrival, scroll reveals, hover glows and regex pulse. Ambient animations pause when hidden. Reduced-motion disables particles and movement. No parallax was added.
E. Highlights: existing ratings retain labels and coloured indicators. Selected counts and length budget stay visible. Top-level regex alternatives map to matching source mods for mouse hover; focusing a mod highlights its corresponding alternatives. Shared alternatives may highlight several source mods.
F. Onboarding: first-visit four-step native dialog, Next/Back/Skip, diamond navigation, replay, Escape and focus restoration. Only dismissal is saved to localStorage. The example button now analyzes the sanitized fixture through the existing analyzer; it requires the API, like a normal import. FAQ explains privacy and uncertainty truthfully.
G. QA: checked desktop, 390px phone and 360px narrow phone. No document overflow. Verified real example import, selection, copied text, numeric filters, sticky output, four-step guide, Escape/focus return and no browser warning/error logs during these checks.

## Palette
Exact sampled reference golds: bronze #8E884E, mid gold #BDB781.
Adapted palette: background #050607 / #101214 / #1B1C1C; fog #142338; stone #17191A; border #6D6040; heading #E7DF9A; body #D1CCBF; secondary body #ADA99D; crimson #601B23 / #943C38; parchment #D5C591.
Rating colours: brick #EC9189; danger #E2B273; uncomfortable #D5C48B; free #A6C9A0; review #A8B9E4. Labels accompany colour.
Spacing: 8 / 16 / 24 / 40 / 64 / 104px; motion: 180 / 450 / 900ms.
Primary and secondary body tokens exceed AA contrast on the charcoal panel token. This is not a full independent accessibility audit.
An optional licensed background slot is documented in tokens.css; it is empty by default.

## Regression evidence
- 105 Python tests and 23 regex tests passed.
- Both local and Vercel production builds passed TypeScript checking.
- scripts/check_redesign.py compares SHA256 of protected sources and the complete analyzed fixture result against the pre-redesign snapshot.
- frontend/tests/redesignFixture.mjs compares all preset regex, selections, warnings and limits for that snapshot.
- These fixture checks passed during development and on the final build.
- No lint script/configuration exists in this project; TypeScript checking was used. No claim of a lint pass.

Protected sources: backend/*, api/*, frontend/src/services/regexBuilder.ts, frontend/src/services/mapPreferencesRegex.ts, frontend/src/store/useAppStore.ts, frontend/src/data/mapCatalogue.ts, frontend/src/types.ts. The parser, rules, policies, state decisions and regex engine were not edited.
Fixture: fixtures/test-build.pob.txt, derived from the existing sanitized Winter Orb test export. Its before snapshot is committed beside it. The example UI uses the same fixture.

## Remaining visual differences from the references
1. Original Atlas linework replaces all full-colour game artwork; no characters, cinematic scenes or photographic textures are included.
2. The emblem is MapRegex's folded-map/regex symbol, rather than the official PoE logo. The navbar is shorter and simpler, with vector scroll ends instead of sculpted cast-metal relief.
3. Cormorant SC has finer strokes and more contrast than Fontin; Crimson Pro differs in width and serif shape. Gold is slightly brighter for readability.
4. Frames are thinner and more geometric; corner scrolls, crest and arch are deliberately original. There are no statues or creatures. Plaques and repeated dividers are less dense than the references.
5. The hero contains a functional import/review/copy flow instead of platform sales links. On mobile, its title wraps and ornamental nav ends disappear.
6. Category medallions use three original geometric glyph families with text labels, rather than twelve distinct class icons. They wrap into a grid on mobile instead of staying in a single row.
7. The Atlas panels contain readable controls rather than overlapping artwork and right/left cinematic copy. Mobile panels stack vertically and use smaller corners.
8. The arch is decorative around the workspace and hero; the import form uses a rectangular panel. The guided tour is a spotlight dialog, not an image carousel.
9. The sticky search output, selected modifier lists, rating legend and numeric forms have no equivalents on the reference site. Their spacing prioritises interaction; the dock is taller on phones.
10. Mist/embers and hover light are restrained. No video, canvas, heavy image layers or parallax. No claim that glow strength or frame detail is pixel-identical.

## Limits / issues not changed
- Build analysis still depends on saved PoB evidence. This redesign does not make map recommendations a guarantee or extend archetype coverage.
- Vite reports a >500 kB minified JavaScript chunk (about 126 kB gzip). The catalogue and app are still bundled together. No Lighthouse baseline or mobile performance score was measured, so >=90 is not claimed.
- Old structural CSS remains under the new token/theme layer; a future CSS consolidation could reduce duplication.
- Shared regex fragments can correspond to several modifiers; hover correctly highlights the group rather than pretending each fragment has only one source. Touch devices use the selected lists and labels instead of hover.
- Reference comparison screenshots are outside the repository and production assets, in the local redesign-review artifact.
- Development phases were validated in a staged checkout; changes are delivered together rather than claiming seven independently completed phase commits.
