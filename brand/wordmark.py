#!/usr/bin/env python3
"""Outline words of a brand's name in Geist (fonts/, SIL Open Font Licence) so lockups carry
paths, not live text.

    uv run --no-project --with 'fonttools[woff]==4.60.1' python3 wordmark.py OUT.json WORD [WORD ...] [--weight 800]

Writes OUT.json: one SVG path per word on a 1000-unit em (baseline y=0), widths and the
space width. brandkit.Wordmark reads it.
"""

import argparse
import json
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT = Path(__file__).resolve().parent / "fonts" / "geist-latin-wght-normal.woff2"
TRACKING = 10


def outline(font, text):
    glyphs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    scale = 1000 / font["head"].unitsPerEm
    pen, x = SVGPathPen(glyphs), 0.0
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
        x += hmtx[name][0] * scale + TRACKING
    return pen.getCommands(), x - TRACKING


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("words", nargs="+")
    ap.add_argument("--weight", type=int, default=800)
    a = ap.parse_args()
    font = instantiateVariableFont(TTFont(FONT), {"wght": a.weight})
    words = {}
    for w in a.words:
        d, width = outline(font, w)
        words[w] = {"d": d, "width": round(width, 1)}
    space = font["hmtx"][font.getBestCmap()[ord(" ")]][0] * 1000 / font["head"].unitsPerEm
    Path(a.out).write_text(json.dumps({"font": "Geist", "weight": a.weight, "em": 1000, "space": round(space, 1),
                                       "words": words}, indent=1) + "\n")
    print({w: v["width"] for w, v in words.items()})
