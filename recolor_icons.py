"""Make single-color copies of the hub icons: icon-<name>.svg -> hub-<name>.svg.

Why not a CSS filter? A filter turns EVERY color black, so light details
(cream stripes, white cutouts) disappear. Here we rewrite the colors inside
each SVG instead: dark colors -> DARK, light colors -> LIGHT.
"""
import re
from pathlib import Path

IMG = Path(__file__).parent / "static" / "img"

DARK = "#0E3B45"    # icon color (deep teal). Change it here, re-run, rebuild.
LIGHT = "#DCEBEE"   # must match the hub card background (--mist)

ICONS = ["droplet", "seedling", "soap", "readout", "mosquito", "pipette", "pathogen"]

# The mosquito file is light green (drawn for a dark background), so
# "light -> LIGHT" would make it vanish. Force every color in it to DARK.
FORCE_DARK = {"mosquito"}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")   # any hex color: #fff, #1C5D63, ...
NAMED = re.compile(r"((?:fill|stroke)\s*[=:]\s*[\"']?)(white|black)\b")


def luminance(hex_color: str) -> float:
    """Perceived brightness, 0 (black) to 1 (white)."""
    h = hex_color.lstrip("#")
    if len(h) in (3, 4):                      # #abc -> #aabbcc
        h = "".join(c * 2 for c in h[:3])
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b   # standard weighting


def recolor(svg: str, force_dark: bool) -> str:
    def pick(color: str) -> str:
        # re.sub calls this once per hex color it finds
        return DARK if force_dark or luminance(color) < 0.6 else LIGHT

    svg = HEX.sub(lambda m: pick(m.group(0)), svg)
    # Named colors: white -> LIGHT, black -> DARK (group 1 keeps 'fill=')
    svg = NAMED.sub(
        lambda m: m.group(1) + (LIGHT if m.group(2) == "white" and not force_dark else DARK),
        svg)
    # Shapes with NO fill attribute default to black, so give the root <svg>
    # tag a default fill that they inherit.
    root = re.search(r"<svg\b[^>]*>", svg).group(0)
    if "fill=" not in root:
        svg = svg.replace(root, root[:-1] + f' fill="{DARK}">', 1)
    return svg


for name in ICONS:
    src = IMG / f"icon-{name}.svg"
    text = src.read_text(encoding="utf-8")
    print(f"{name}: colors found = {sorted(set(HEX.findall(text)))}")
    out = IMG / f"hub-{name}.svg"
    out.write_text(recolor(text, name in FORCE_DARK), encoding="utf-8")
