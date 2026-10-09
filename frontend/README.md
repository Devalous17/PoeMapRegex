# MapRegex frontend

This is the React + TypeScript source for the local MapRegex screen. The root Python server (using the shared `../backend/` analyzer) serves the compiled files in `../static`, so `python server.py` still starts the app.

## Edit in VS Code

From this folder:

```powershell
npm install
npm run dev
```

The Vite preview runs at `http://127.0.0.1:5173/` and sends `/api` calls to the Python server on port 8765. Run the Python server in another terminal for live pobb.in analysis. The **Try an example build** button uses local sample data and also works without Python.

When changes are ready:

```powershell
npm run build
```

The build replaces `../static` and removes outdated bundles, which the Python server serves. Reload `http://127.0.0.1:8765/` to see the result.

## Design

Warm near-black surfaces, aged gold borders, rarity colors, square beveled controls, and original CSS/SVG ornaments are in `src/styles/theme.css`. The page background is the image the user supplied at `public/images/627187.jpg`. The page uses Tailwind CSS theme tokens, Fontin from exljbris, and custom component styles. The font license notice sits beside the `@font-face` rules; see `public/fonts/Fontin-ReadMe.txt` and [the font author](https://www.exljbris.com/fontin.html).

## Data and logic

- `src/services/analyzer.ts` calls the existing local Python `/api/analyze` endpoint for real builds. `exampleAnalysis()` provides delayed sample data so the UI can be explored before importing a build. The example is generated through the same backend analyzer as live imports.
- Both example and live PoB analysis show 78 top tier normal and 47 Nightmare affixes in `src/data/mapPool.json`. Full English affix effects, reward lines, levels, and spawn weights are in `src/data/poedbNormalAffixes.json` and `src/data/poedbNightmareAffixes.json`, retrieved from [PoEDB normal maps](https://poedb.tw/us/Maps_top_tier) and [Nightmare maps](https://poedb.tw/us/Nightmare_map) on 2026-10-08. Base short fragments came from [poe.re](https://github.com/veiset/poe.re/tree/master/poe/generated/mapmods) and are checked against the PoEDB text; the two supplied avoid lists are in `src/data/mapPoolPatterns.json`. The live analyzer uses the shared rule groups and data in `../backend/`; all normal entries either map to a rule or to the player's explicit Free policy. Unrated Nightmare entries remain Review.
- `src/services/regexBuilder.ts` shortens selections with map-mod fragments and validates candidates against the other entries in the active pool. **Block** excludes a mod; **Want** requires at least one wanted mod; **Allow** accepts without requiring it. The optional supplied avoid list skips modifiers classified Free, including the 54 normal-map entries the player marked Free. `src/services/mapPreferencesRegex.ts` adds live numeric ranges, state, and rarity terms. Item Quantity defaults to at least 40%; users can clear or change it. Eight-mod, Valdo, and Shaper/Elder influence remain trade-only selections because an in-game stash regex cannot reliably check them. If a complete query exceeds 250 characters, the UI disables copying it and shows partial batches for inspection.
- `node --test tests/regexBuilder.mjs` checks that generated fragments match selected mod entries without catching unselected entries in the included catalogue.
- `src/store/useAppStore.ts` holds the interface state in Zustand.

The first live analyzer is a saved PoB snapshot reader, not the full Path of Building engine. Always review conditional defences and secondary skills.
