"""Resize and compress site images.

Reads originals from assets-src/, writes web-ready versions to static/img/.
Photos and diagrams become resized WebP files; SVGs (already tiny vector
files) are copied as-is. Run from the repo root with the venv active:

    python resize_images.py
"""
import shutil
from pathlib import Path

from PIL import Image, ImageOps   # Pillow: image I/O, resizing, EXIF handling

SRC = Path("assets-src")
DEST = Path("static/img")

# ---------------------------------------------------------------------------
# What to process: filename -> (max width in px, WebP quality 1-100)
#   - Max width is a CEILING: smaller images are never enlarged (upscaling
#     only adds blur and file size).
#   - Hero-size photos get 1600 px: wide enough for large and retina screens.
#   - Inline photos get 1000 px: they never display wider than the 60rem
#     (~960 px) container.
#   - Diagrams get higher quality (90) because compression artifacts show up
#     around text and thin lines much more than in photos.
# Files NOT listed here are ignored, which is how duplicates and the
# inspiration screenshots stay out of the site.
# ---------------------------------------------------------------------------
IMAGES = {
    "photo-field-julius.jpg":      (1600, 82),   # landing-page hero + ROSALIND
    "photo-crop-team.jpg":         (1000, 82),
    "photo-pardee-team.jpg":       (1000, 82),
    "photo-paper-diagnostic.jpg":  (1000, 82),
    "photo-tz-lab.webp":           (1000, 82),
    "photo-mosquito-lab.jpg":      (1000, 82),
    "illo-device.jpg":             (900, 88),
    "dia-freezedry.png":           (1000, 90),
    "dia-sensor.png":              (1000, 90),
    "dia-zika-readout.jpg":        (1000, 90),
}


def kb(path: Path) -> float:
    """File size in kilobytes (for the before/after report)."""
    return path.stat().st_size / 1024


def process_raster(name: str, max_width: int, quality: int) -> tuple[float, float]:
    """Resize one raster image to WebP. Returns (original KB, new KB)."""
    src = SRC / name
    out = DEST / (Path(name).stem + ".webp")   # same name, .webp extension

    with Image.open(src) as img:
        # Phone cameras often store rotation as EXIF metadata instead of
        # rotating the pixels. exif_transpose applies it, so a portrait
        # photo doesn't come out sideways once the metadata is stripped.
        img = ImageOps.exif_transpose(img)

        # Only shrink: skip resizing if already narrower than the ceiling
        if img.width > max_width:
            new_height = round(img.height * max_width / img.width)  # keep aspect ratio
            # LANCZOS is a high-quality downsampling filter (sharp, few artifacts)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        # WebP supports transparency, but keep RGB/RGBA only so exotic
        # modes (palette PNGs, CMYK) convert cleanly
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")

        # method=6 is the slowest/best WebP compression; fine for ~10 images
        img.save(out, "WEBP", quality=quality, method=6)

    return kb(src), kb(out)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    total_before = total_after = 0.0

    # --- Raster images: resize + convert ---------------------------------
    for name, (max_width, quality) in IMAGES.items():
        if not (SRC / name).exists():
            print(f"  MISSING   {name}  (check the filename in IMAGES)")
            continue
        before, after = process_raster(name, max_width, quality)
        total_before += before
        total_after += after
        print(f"  {name:32s} {before:7.0f} KB -> {after:6.0f} KB")

    # --- SVGs: copy unchanged. Only top-level files (glob, not rglob),
    # so anything left in a subfolder like uploads/ is never copied.
    svgs = sorted(SRC.glob("*.svg"))
    for svg in svgs:
        shutil.copy2(svg, DEST / svg.name)   # copy2 preserves timestamps
    print(f"  Copied {len(svgs)} SVG files unchanged")

    print(f"\nRasters: {total_before:.0f} KB -> {total_after:.0f} KB "
          f"({100 * (1 - total_after / max(total_before, 1)):.0f}% smaller)")


if __name__ == "__main__":
    main()
