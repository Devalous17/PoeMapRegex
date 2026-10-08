# MapRegex — Path of Exile 1 map regex helper

Paste a `pobb.in` link or a raw Path of Building export. MapRegex reads the saved build profile, explains common map modifier risks, and makes a search regex from the preset and mod choices you select.

## Run in VS Code

Open `C:\Users\deva\Documents\regex poe` as the folder in VS Code. Press **F5** and choose **Run MapRegex**, or start it in the VS Code terminal:

```powershell
cd 'C:\Users\deva\Documents\regex poe'
& 'C:\Users\deva\AppData\Local\Python\pythoncore-3.14-64\python.exe' server.py
```

Open <http://127.0.0.1:8765/>. Stop the terminal command with **Ctrl+C**, or an F5 run with **Shift+F5**. The compiled frontend is already in `static/`; you do not need npm just to use the app.

## Edit the frontend

The React + TypeScript source is in `frontend/`. To work on it with hot reload, run the Python server as above and then use another VS Code terminal:

```powershell
cd 'C:\Users\deva\Documents\regex poe\frontend'
npm install
npm run dev
```

Open <http://127.0.0.1:5173/>. To update the page served by Python, run `npm run build` from `frontend/`, then refresh port 8765. See [the frontend guide](frontend/README.md) for its design tokens and services.

## Current scope

- Real imports use the Python analyzer in `pob.py`, `build_signals.py`, and `rules.py`. It rates **25** English map modifier groups by identifying measured avoidance, mitigation, recovery, resource, and damage signals. The frontend presents **78 top tier normal** and **47 Nightmare** PoEDB affix entries. For normal maps, six additional rules check charge theft, flask charges, curse effect, critical damage, area of effect, and stun dependence. The other 55 newly reviewed normal entries are marked **Free** by player preference. Nightmare entries without a build-specific rule still show **Review**. This is a saved PoB snapshot reader, not the full Path of Building calculation engine. Conditional effects, passive tree details, flask reliance, and secondary skills may need manual review.
- **Try an example build** uses a sample profile and illustrative ratings with the same 125-entry map catalogue and shortened regex output. Analyze a real link for build-specific ratings.
- The modifier database has one-click **Avoid** and **Want** modes, search, selected-only view, and optional build-rating/category filters. Build-breaking entries are highlighted red. A separate selected modifiers panel shows every Avoid and Want choice for the current map pool, even when the database list is filtered; click one there to remove it. Normal and Nightmare maps have separate pools. The regex appears above the list and updates immediately. An optional button applies the avoid lists the user supplied as a starting point.
- For small selections, the generator preserves the catalogue's short fragments and order. For example, the five selected Nightmare mods from the reference screenshot produce `"!cco|m resistances$|k damage$|re sha|mum f"`. Larger selections use a shortening pass.
- The generator validates shortened fragments against PoEDB's complete modifier and reward lines for the active map pool, including both ends of numeric roll ranges. It shows the 250-character limit and disables copying when the complete query is too long or cannot safely cover a selection. Partial batches are shown for inspection only; each covers just some selected modifiers.
- Map value MIN/MAX fields, corrupted/unidentified, and rarity update the copyable regex immediately. Item Quantity starts at a 40% minimum; clear or change it in Map Values. The result stays at the top while scrolling. Invalid ranges and searches over 250 characters disable copying.
- Eight-mod, Valdo, Shaper influence, and Elder influence are marked **trade-only** because a stash regex cannot reliably check those properties. "More maps" remains a separate map value field.
- Build ratings treat the current Physical and Elemental Thorns affixes as flat incoming hits, including hits from channelled skills. Chaos immunity and capped Chaos Resistance exempt a build from automatic Extra Chaos exclusions; Armour-based attack damage makes the less-Armour affix a build-breaking choice.
- “Free” on the 55 player-reviewed normal affixes is a chosen default, not proof that the modifier is harmless to every build. You can block any of them manually. The tool does not certify an entire map or encounter.
- The player/minion 5% Life, Mana, and Energy Shield removal affix is not in the current Normal or Nightmare catalogue. It is not silently mixed into either pool. Main-damage and utility minions are identified for catalogue rules and future pool updates.

The build is analyzed in memory. MapRegex does not save PoB exports. For a `pobb.in` link, the local Python server downloads the export from `https://pobb.in/pob/<build-id>`.

## Check the analyzer

```powershell
& 'C:\Users\deva\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m unittest discover -s tests -v
```

The PoB import format follows [Path of Building's import code](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Modules/BuildSiteTools.lua) and [export code](https://github.com/PathOfBuildingCommunity/PathOfBuilding/blob/dev/src/Classes/ImportTab.lua). The page background is the image the user supplied. The current English affix names, effects, reward lines, levels, and spawn weights are stored in `frontend/src/data/poedbNormalAffixes.json` and `frontend/src/data/poedbNightmareAffixes.json`, retrieved from [PoEDB top tier maps](https://poedb.tw/us/Maps_top_tier) and [PoEDB Nightmare maps](https://poedb.tw/us/Nightmare_map) on 2026-10-08. The base short regex fragments were originally extracted from [poe.re's English map catalogue](https://github.com/veiset/poe.re/tree/master/poe/generated/mapmods) at commit `b6f3eba6b5790000de196a547094a70ff7cb676e` and were checked against the PoEDB text. Fontin is from [exljbris](https://www.exljbris.com/fontin.html); the local font files include their readme and a CSS attribution.
