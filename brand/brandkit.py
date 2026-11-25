#!/usr/bin/env python3
"""Shared drawing kit for the marks of Bruno's brands (STYLE.md, BRANDS.md).

A brand's own script imports this, draws its symbol with the helpers and calls write_kit()
to get the standard files. Geometry lives on a 256 grid; colours come from the brand's entry
in BRANDS.md. Standard library only.

    import sys; sys.path.insert(0, "<path to this folder>")
    from brandkit import *
    write_kit(out_dir, title="Name", colour=draw, mono=draw_mono, name=Wordmark(...), signature="#hex")
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

INK, VOID = "#1b1e24", "#120a1a"
SPARKS = ("#ffd28a", "#fb8e31", "#e84fc0")
EMBER_STOPS = (("0", "#ffc66e"), (".55", "#fb8e31"), ("1", "#e95904"))


# ---------------------------------------------------------------- geometry

def hexagon(r: float, cx: float = 128, cy: float = 128, rot: float = -90) -> list[tuple[float, float]]:
    """Pointy-top by default (rot=-90); rot=0 gives a flat-top hexagon."""
    return [(cx + r * math.cos(math.radians(rot + a)), cy + r * math.sin(math.radians(rot + a))) for a in range(0, 360, 60)]


def sub(points) -> str:
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + " Z"


def ring(r_out: float = 116, r_in: float = 94) -> str:
    """The hexagonal ring of the family (use with fill-rule="evenodd")."""
    return f"{sub(hexagon(r_out))} {sub(hexagon(r_in))}"


def open_ring(r_out: float = 116, r_in: float = 94, gap_side: int = 0) -> str:
    """The ring without one side, in one piece (no seams at the corners)."""
    o, i = hexagon(r_out), hexagon(r_in)
    order = [(gap_side + 1 + k) % 6 for k in range(6)]
    return sub([o[k] for k in order] + [i[k] for k in reversed(order)])


def flame(cx: float, top: float, bottom: float, w: float) -> str:
    """One flame tongue with a hooked tip; w is the half width."""
    h = bottom - top
    return (f"M{cx} {top} C{cx + w * .55} {top + h * .25} {cx + w} {top + h * .45} {cx + w * .95} {top + h * .7} "
            f"C{cx + w * .9} {top + h * .9} {cx + w * .45} {bottom} {cx} {bottom} "
            f"C{cx - w * .45} {bottom} {cx - w * .9} {top + h * .9} {cx - w * .95} {top + h * .7} "
            f"C{cx - w} {top + h * .5} {cx - w * .55} {top + h * .38} {cx - w * .2} {top + h * .25} "
            f"C{cx - w * .05} {top + h * .42} {cx + w * .1} {top + h * .45} {cx + w * .2} {top + h * .42} "
            f"C{cx + w * .25} {top + h * .28} {cx + w * .1} {top + h * .12} {cx} {top} Z")


def almond(x0: float, x1: float, cy: float, h: float) -> str:
    k = (x1 - x0) * 0.25
    return f"M{x0} {cy} C{x0 + k} {cy - h} {x1 - k} {cy - h} {x1} {cy} C{x1 - k} {cy + h} {x0 + k} {cy + h} {x0} {cy} Z"


def diamond(x: float, y: float, r: float) -> str:
    return f"M{x} {y - r} L{x + r} {y} L{x} {y + r} L{x - r} {y} Z"


def circle(cx: float, cy: float, r: float) -> str:
    return f"M{cx - r} {cy} A{r} {r} 0 1 0 {cx + r} {cy} A{r} {r} 0 1 0 {cx - r} {cy} Z"


def frame(c, end):
    """A local frame along the segment c -> end: p(a, b) is a along it and b across it."""
    ux, uy = end[0] - c[0], end[1] - c[1]
    n = math.hypot(ux, uy)
    u, v = (ux / n, uy / n), (-uy / n, ux / n)
    return (lambda a, b: (c[0] + a * u[0] + b * v[0], c[1] + a * u[1] + b * v[1])), n


# ---------------------------------------------------------------- paint

def ink(width: float) -> str:
    """The family outline: dark, round joins, drawn under the fill."""
    return f'stroke="{INK}" stroke-width="{width}" stroke-linejoin="round" paint-order="stroke"'


def path(d: str, fill: str, outline: float = 0, evenodd: bool = False, extra: str = "") -> str:
    rule = ' fill-rule="evenodd"' if evenodd else ""
    stroke = f" {ink(outline)}" if outline else ""
    return f'<path{rule} fill="{fill}"{stroke}{extra} d="{d}"/>'


def gradient(gid: str, y0: float, y1: float, stops=EMBER_STOPS) -> str:
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y0}" x2="0" y2="{y1}">{s}</linearGradient>'


def signature_ring(colour: str, bevel: str, small: bool = False, opening: int | None = None) -> str:
    """The ring in the brand's signature colour with its lighter inner bevel."""
    if opening is None:
        out = path(ring(), colour, evenodd=True)
        return out if small else out + path(f"{sub(hexagon(102))} {sub(hexagon(94))}", bevel, evenodd=True)
    out = path(open_ring(gap_side=opening), colour, outline=14 if small else 10)
    return out if small else out + path(open_ring(103, 94, opening), bevel)


def sparks(points, colours=SPARKS) -> str:
    """Three diamonds with the family outline; points are (x, y, r)."""
    return "".join(path(diamond(x, y, r), colours[k % len(colours)], outline=5 if r < 7 else 6)
                   for k, (x, y, r) in enumerate(points))


# ---------------------------------------------------------------- name

@dataclass
class Wordmark:
    """An outlined name from wordmark.json (wordmark.py); parts is [(word, colour), ...] and
    space is inserted between parts unless joined=True (one word in two colours)."""
    json_path: Path
    parts: list[tuple[str, str]]
    joined: bool = False
    data: dict = field(init=False)

    def __post_init__(self):
        self.data = json.loads(Path(self.json_path).read_text())

    def width(self, size: float) -> float:
        s, w = size / self.data["em"], self.data["words"]
        gap = 10 if self.joined else self.data["space"]
        return (sum(w[p]["width"] for p, _ in self.parts) + gap * (len(self.parts) - 1)) * s

    def draw(self, x: float, baseline: float, size: float, anchor: str = "start") -> str:
        s, w = size / self.data["em"], self.data["words"]
        gap = 10 if self.joined else self.data["space"]
        cur = x - self.width(size) / 2 if anchor == "middle" else x
        out = []
        for word, colour in self.parts:
            out.append(f'<path fill="{colour}" transform="translate({cur:.1f} {baseline}) scale({s:.4f})" d="{w[word]["d"]}"/>')
            cur += (w[word]["width"] + gap) * s
        return "".join(out)


# ---------------------------------------------------------------- kit

def svg(w: float, h: float, body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-labelledby="t"><title id="t">{title}</title>{body}</svg>\n')


def write_kit(out: Path, title: str, colour, mono, defs: str = "", name: Wordmark | None = None,
              signature: str = "#e84fc0", glow: str = "#3b1564", prefix: str = "") -> list[str]:
    """Write the standard files. colour(small: bool) -> SVG body on the 256 grid;
    mono(colour: str) -> one-colour body. Returns the file names written."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    d = f"<defs>{defs}</defs>" if defs else ""
    bg = (f'<defs>{defs}<radialGradient id="kit-glow" cx="50%" cy="42%" r="60%"><stop offset="0" stop-color="{glow}"/>'
          f'<stop offset="1" stop-color="{VOID}"/></radialGradient></defs>')
    files = {
        "mark.svg": svg(256, 256, d + colour(False), title),
        "mark-small.svg": svg(256, 256, d + colour(True), f"{title}, small sizes"),
        "mark-black.svg": svg(256, 256, mono("#111111"), title),
        "mark-white.svg": svg(256, 256, mono("#ffffff"), title),
        "mark-mono.svg": svg(256, 256, mono(signature), title),
        "avatar.svg": svg(512, 512, bg + '<rect width="512" height="512" fill="url(#kit-glow)"/>'
                                     f'<g transform="translate(36 36) scale(1.72)">{colour(False)}</g>', title),
        "app-icon.svg": svg(512, 512, d + f'<rect width="512" height="512" fill="{VOID}"/>'
                                       f'<g transform="translate(96 96) scale(1.25)">{colour(True)}</g>', title),
    }
    if name is not None:
        hw = name.width(96)
        files["lockup-horizontal.svg"] = svg(282 + hw + 24, 256, d + colour(False) + name.draw(282, 164, 96), title)
        sw = max(560, name.width(64) + 40)
        files["lockup-stacked.svg"] = svg(sw, 400, d + f'<g transform="translate({sw / 2 - 128:.0f} 0)">{colour(False)}</g>'
                                          + name.draw(sw / 2, 352, 64, "middle"), title)
    for f, s in files.items():
        (out / f"{prefix}{f}").write_text(s)
    return [f"{prefix}{f}" for f in files]
