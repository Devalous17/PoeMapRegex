# Supplied UI assets

These assets were cropped from the UI sheet supplied by the project owner.
The original alpha channel is retained. No generated artwork was added.
asset-map.json records every crop rectangle. panel-texture.webp is a tile from
the supplied panel interior. Buttons and panel frames use nine-slice borders
so their corners keep their proportions at different screen sizes.

Replace files at the same paths to reskin the controls. Adjust border-image
slice values in tool.css when a replacement has different frame thickness.
The Waystone crop is retained as a source asset, but has no unsupported map control.
