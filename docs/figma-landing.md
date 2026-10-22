# Figma landing page

Source: [MapRegex / Landing, frame 16:2](https://www.figma.com/design/IPRoEz7ntn7Lnqh3mmY0TR/MapRegex-UI?node-id=16-2).

The landing page uses the Figma sprite sheet and hero glow as local assets. LandingSprite maps 27 visual slots to their source nodes, including panel corners, feature icons, buttons and status pills. The existing import component and analyzer handle both manual input and the example-build actions. Successful analysis opens the existing workspace, and Reset returns to the landing page.

The preview is explicitly an example. Its regex uses the current catalogue and builder; the example copy action identifies it as illustrative. Current Thorns terminology, the 250-character limit, the previously requested single heading, and the user's shared background replace outdated mockup content. Catalogue counts are derived from the current data.

Responsive layouts stack the hero and preview, then the step and feature cards. Keyboard interaction uses native forms, buttons, disclosures and visible focus styles. Privacy information is available on the landing page.

TypeScript and production build checks pass. Visual browser verification remains pending because local preview access was rejected by browser security policy in this session.
