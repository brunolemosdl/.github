# House style of the marks

The look shared by every mark of Bruno's brands (Tenebris Forge, Bruno Lemos, Forja). A new
brand follows it, and only its **signature colour** and its **symbol** change.

## The frame

- **Hexagonal ring**, pointy top, outer radius 116 and inner 94 on a 256 grid, with a lighter
  **bevel** from 102 to 94. The ring may open on one side (`open_ring`) or be crossed by one
  element of the symbol (a flame past a lid, a hammer handle): that break is the mark's energy.
- The ring is the brand's signature colour; nothing else in the mark uses it.

## The symbol

- **One idea**, explainable in a sentence (the watching ember; the ember core; the anvil and the
  hammer). Drawn from flat faceted shapes: a body, a lit top face, a shaded side, details only
  where they read at 64 px.
- **Dark outlines** `#1b1e24`, width 10 on the 256 grid (8 for inner parts, 5 to 6 for sparks),
  round joins, drawn under the fill (`paint-order="stroke"`).
- **Ember** gradient `#ffc66e` to `#fb8e31` to `#e95904` for anything hot; **magenta**
  `#e84fc0` with a light core `#ffc2ee` for fire inside the symbol; **violets** `#a155b9`,
  `#713989`, `#52216a`, `#3d1752` for material; **sparks** `#ffd28a`, `#fb8e31`, `#e84fc0`,
  three, outlined, close to where the energy leaves the symbol.
- Background for tiles and avatars: `#120a1a` with a soft radial glow.

## The name

- **Geist ExtraBold (800)**, outlined (`wordmark.py`), never live text.
- White on dark; one accent colour taken from the symbol when the name has two parts
  (Tenebris **Forge**, FOR**JA**). Case as the brand writes itself.

## The kit (every brand)

`mark`, `mark-small` (16 to 48 px: no sparks, cores, bevels or fine details, outlines 14),
`mark-black`, `mark-white`, `mark-mono` (one colour; elements that cross others cut a gap
with a mask), `avatar`, `app-icon` (maskable safe zone), `lockup-horizontal`,
`lockup-stacked`, PNGs (`render.mjs`) and a one-page `README.md` (idea, files, colours,
clear space, minimum sizes, backgrounds, misuse).

## Checks before showing

- 16, 32 and 64 px; one colour; on light and dark; mirrored and upside down for unwanted
  readings (a pointed white hood with eye slits reads as the Ku Klux Klan: avoid).
- Next to the other marks of the family: related, not twins.
