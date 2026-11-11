"""Build a static site from Markdown content into docs/."""
import argparse
import shutil
from pathlib import Path

import markdown                      # converts Markdown text -> HTML
import yaml                          # parses front matter and home.yml
from jinja2 import Environment, FileSystemLoader  # fills HTML templates with data

ROOT = Path(__file__).parent
CASES = ROOT / "content" / "case-studies"   # one .md per case study
PAGES = ROOT / "content" / "pages"          # NEW: researchers, practitioners, about
HOME = ROOT / "content" / "home.yml"        # landing-page wording
OUT = ROOT / "docs"                         # GitHub Pages will serve this folder

# --- Command-line option -----------------------------------------------
# Local preview:  python build.py                              (base = "")
# GitHub Pages:   python build.py --base-url /SynBio-lab2field
parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="")
args = parser.parse_args()


def load_markdown(path: Path, env: Environment, base_url: str) -> dict:
    """Read one .md file; return its front matter plus the rendered HTML body.

    Used for BOTH case studies and ordinary pages, since both files have the
    same shape: a YAML block between '---' lines, then Markdown.
    """
    text = path.read_text(encoding="utf-8")
    # The file starts with '---', so splitting at most twice gives:
    # ['', front_matter, body]
    _, front, body = text.split("---", 2)
    item = yaml.safe_load(front)                 # dict: title, summary, ...

    # NEW: treat the body as a tiny Jinja template FIRST, so that
    # {{ base_url }} inside the .md file (image paths, links) gets filled in.
    # Because of this, never write a literal "{{" or "{%" in content files.
    body = env.from_string(body).render(base_url=base_url)

    item["html"] = markdown.markdown(body)       # Markdown -> HTML
    item["slug"] = path.stem                     # filename becomes the URL
    return item


def load_home() -> dict:
    """Read content/home.yml and return it as a plain dict."""
    return yaml.safe_load(HOME.read_text(encoding="utf-8"))


def write_page(env: Environment, template: str, out_path: Path, **context) -> None:
    """Render one template with the given data and save it to out_path.

    **context collects any extra keyword arguments into a dict, so each call
    can pass different data (page=..., studies=..., etc.).
    """
    html = env.get_template(template).render(**context)
    out_path.write_text(html, encoding="utf-8")


def main() -> None:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"))
    base = args.base_url

    # Load case studies and put them in the order set by `order:` in each
    # file's front matter (not alphabetical by filename).
    studies = [load_markdown(p, env, base) for p in CASES.glob("*.md")]
    studies.sort(key=lambda s: s["order"])

    # NEW: give each study links to its neighbors for the "previous / next"
    # navigation at the bottom of a case page. None means "no neighbor".
    for i, s in enumerate(studies):
        s["prev"] = studies[i - 1] if i > 0 else None
        s["next"] = studies[i + 1] if i < len(studies) - 1 else None

    pages = [load_markdown(p, env, base) for p in sorted(PAGES.glob("*.md"))]
    home = load_home()

    # Start clean so deleted pages don't linger in the output
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "case-studies").mkdir(parents=True)

    # Copy css/images across unchanged
    shutil.copytree(ROOT / "static", OUT / "static")

    # Empty marker file: tells GitHub Pages to serve the folder as-is
    # instead of processing it with Jekyll
    (OUT / ".nojekyll").touch()

    # Landing page
    write_page(env, "index.html", OUT / "index.html",
               studies=studies, home=home, base_url=base)

    # NEW: case-study index at /case-studies/index.html
    write_page(env, "case_index.html", OUT / "case-studies" / "index.html",
               studies=studies, base_url=base)

    # One page per case study
    for s in studies:
        write_page(env, "case_study.html",
                   OUT / "case-studies" / f"{s['slug']}.html",
                   study=s, base_url=base)

    # NEW: one page per file in content/pages/ -> docs/researchers.html, etc.
    # `studies` is passed too, because the practitioners page shows case cards.
    for p in pages:
        write_page(env, "page.html", OUT / f"{p['slug']}.html",
                   page=p, studies=studies, base_url=base)


if __name__ == "__main__":
    main()
