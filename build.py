"""Build a static site from Markdown case studies into docs/."""
import argparse
import shutil
from pathlib import Path

import markdown                      # converts Markdown text -> HTML
import yaml                          # parses the front matter block
from jinja2 import Environment, FileSystemLoader  # fills HTML templates with data

ROOT = Path(__file__).parent
CONTENT = ROOT / "content" / "case-studies"
OUT = ROOT / "docs"                  # GitHub Pages will serve this folder

# --- Command-line option -----------------------------------------------
# Local preview:  python build.py                              (base = "")
# GitHub Pages:   python build.py --base-url /SynBio-lab2field
parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="")
args = parser.parse_args()


def load_case_study(path: Path) -> dict:
    """Read one .md file and return its metadata plus rendered HTML body."""
    text = path.read_text(encoding="utf-8")
    # The file starts with '---', so splitting at most twice gives:
    # ['', front_matter, body]
    _, front, body = text.split("---", 2)
    study = yaml.safe_load(front)                # dict: title, summary, tags
    study["html"] = markdown.markdown(body)      # prose -> HTML
    study["slug"] = path.stem                    # filename becomes the URL
    return study


def main() -> None:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"))
    studies = [load_case_study(p) for p in sorted(CONTENT.glob("*.md"))]

    # Start clean so deleted case studies don't linger in the output
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "case-studies").mkdir(parents=True)

    # Copy css/images across unchanged
    shutil.copytree(ROOT / "static", OUT / "static")

    # Empty marker file: tells GitHub Pages to serve the folder as-is
    # instead of processing it with Jekyll
    (OUT / ".nojekyll").touch()

    # Index page listing every study. base_url is passed to every template.
    index = env.get_template("index.html").render(
        studies=studies, base_url=args.base_url
    )
    (OUT / "index.html").write_text(index, encoding="utf-8")

    # One page per study
    template = env.get_template("case_study.html")
    for s in studies:
        page = template.render(study=s, base_url=args.base_url)
        (OUT / "case-studies" / f"{s['slug']}.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
