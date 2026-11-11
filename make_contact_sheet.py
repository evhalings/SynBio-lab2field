"""Make labeled contact sheets of every image under static/img so we can
identify them at a glance. Run from the repo root."""
import io
from pathlib import Path

from PIL import Image, ImageDraw      # Pillow: opens, resizes, and draws on images

FOLDER = Path("static/img")           # scan this folder and all subfolders
OUT_DIR = Path("notes")               # output goes here (not published by the site)
THUMB = 220                           # each thumbnail fits a 220x220 px box
COLS = 5                              # thumbnails per row
ROWS_PER_SHEET = 4                    # keeps each sheet small enough to read clearly
LABEL_H = 34                          # vertical space under each thumbnail for its filename
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}


def load_thumb(path: Path):
    """Return a thumbnail as an RGBA image, or None if the file can't be read."""
    try:
        if path.suffix.lower() == ".svg":
            # Pillow can't open SVGs, so cairosvg renders to PNG bytes first
            import cairosvg
            png = cairosvg.svg2png(url=str(path), output_width=THUMB)
            img = Image.open(io.BytesIO(png))
        else:
            img = Image.open(path)
        img = img.convert("RGBA")     # RGBA keeps transparency from PNGs and SVGs
    except Exception:
        return None                   # blank cell; the filename label still prints
    img.thumbnail((THUMB, THUMB))     # shrinks in place, preserving aspect ratio
    return img


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    files = sorted(p for p in FOLDER.rglob("*") if p.suffix.lower() in EXTS)
    per_sheet = COLS * ROWS_PER_SHEET

    # Slice the file list into batches, one contact sheet per batch
    for sheet_no, start in enumerate(range(0, len(files), per_sheet), start=1):
        batch = files[start:start + per_sheet]
        rows = -(-len(batch) // COLS)             # ceiling division
        # Mid-gray background so white logos and icons stay visible
        sheet = Image.new("RGB", (COLS * THUMB, rows * (THUMB + LABEL_H)), "#bbbbbb")
        draw = ImageDraw.Draw(sheet)

        for i, path in enumerate(batch):
            col, row = i % COLS, i // COLS        # position in the grid
            x, y = col * THUMB, row * (THUMB + LABEL_H)
            img = load_thumb(path)
            if img:
                # Center the thumbnail in its cell; passing img as the mask
                # (third argument) respects transparency
                sheet.paste(img, (x + (THUMB - img.width) // 2,
                                  y + (THUMB - img.height) // 2), img)
            draw.text((x + 4, y + THUMB + 4), path.name[:34], fill="black")

        out = OUT_DIR / f"contact-sheet-{sheet_no}.png"
        sheet.save(out)
        print(f"Wrote {out} ({len(batch)} images)")


if __name__ == "__main__":
    main()
