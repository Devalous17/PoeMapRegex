# Figma frontend implementation

Reference: [MapRegex / Sprite UI v2, frame 7:2](https://www.figma.com/design/IPRoEz7ntn7Lnqh3mmY0TR/MapRegex-UI?node-id=7-2).

The frontend uses the supplied Figma sprite sheet without modifying the source image. `Sprite.tsx` maps Figma slice geometry to stretchable buttons, frames, inputs, rows, and badges. Cinzel and Inter are bundled locally with their font licenses.

Desktop follows the two-column reference: import, map type, presets, preferences and modifier database on the left; generated regex, selections, calculations and assessment reasons on the right. Narrow screens stack the import and output before the remaining controls. Native keyboard controls and visible focus styles are retained.

Mockup values are replaced with live application results. The app retains its 250-character search limit, current modifier catalogue, NOT/AND behavior, actual assessment reasons, and existing build dependency review. No nonfunctional PoE 2 or OR controls were introduced. The analyzer, state store and regex services were verified unchanged by file hashes.

Validation: TypeScript and production builds pass. Browser visual and interaction verification remains pending because the browser tool rejected local preview access under its security policy. Do not treat this report as visual sign-off.
