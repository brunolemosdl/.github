# Brand kit

Tools and rules for the marks of Bruno's brands, all in one house style. The skill
`brand-mark` (in his vault) runs the process; this folder holds what it needs.

| File | What |
|---|---|
| [`STYLE.md`](STYLE.md) | The house style: frame, symbol, colours, name, kit, checks |
| [`BRANDS.md`](BRANDS.md) | Every brand with its symbol, signature colour and where its kit lives |
| [`brandkit.py`](brandkit.py) | Drawing helpers on the 256 grid and `write_kit()` for the standard files |
| [`wordmark.py`](wordmark.py) | Outlines a name in Geist from `fonts/` (needs fontTools, run with `uv`) |
| [`render.mjs`](render.mjs) | Renders the kit's PNGs with resvg |
| [`upstream/logo-design/`](upstream/logo-design/) | The method of `kaankiziltug/logo-design-skill`, pinned (texts only, MIT) |

A new brand: a `scripts/logo.py` in its repository that imports `brandkit`, draws the symbol
with `colour(small)` and `mono(colour)`, outlines the name with `wordmark.py`, calls
`write_kit()` into `brand/`, then `node render.mjs brand`.
