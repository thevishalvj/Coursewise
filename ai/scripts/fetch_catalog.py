"""Download the UT Austin C S course catalog and write one markdown file per course.

Usage:
    python ai/scripts/fetch_catalog.py

Output: data/markdown/catalog/<slug>.md, each with YAML front matter
(course_code, course_number, title, level, doc_type, source_url).

Catalog codes use "X" for the credit-hour digit, so "C S X39" covers CS 339
and CS 439. `course_number` keeps only the part after that digit ("39") so a
search for "CS 439" can match it.
"""

from __future__ import annotations

import html
import re
import sys
from collections import Counter
import urllib.request
from pathlib import Path

CATALOG_URL = "https://catalog.utexas.edu/general-information/coursesatoz/c-s/"
ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "cs_catalog.html"
OUT_DIR = ROOT / "data" / "markdown" / "catalog"

HEADING_RE = re.compile(r"<(h4|h5)[^>]*>(.*?)</\1>", re.S)
CODE_RE = re.compile(r"^C S ([X0-9])(\d{2}[A-Z]?(?:\.\d+)?)\.\s*(.+?)\.?$")


def clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "coursewise-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse(page: str) -> list[dict]:
    start = page.find('id="textcontainer"')
    body = page[start:] if start != -1 else page
    matches = list(HEADING_RE.finditer(body))
    courses, level = [], ""
    for i, m in enumerate(matches):
        tag, text = m.group(1), clean(m.group(2))
        if tag == "h4":
            level = text.replace(" Courses", "")
            continue
        code = CODE_RE.match(text)
        if not code:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        paragraphs = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body[m.end():end], re.S)]
        hours, number, title = code.groups()
        courses.append({
            "course_code": f"CS {hours}{number}",
            "course_number": number,
            "title": title,
            "level": level,
            "description": "\n\n".join(p for p in paragraphs if p),
        })
    return courses


def to_markdown(c: dict) -> str:
    title = c["title"].replace('"', "'")
    desc = c["description"] or "No description listed in the catalog."
    return (
        "---\n"
        f"course_code: {c['course_code']}\n"
        f'course_number: "{c["course_number"]}"\n'
        f'title: "{title}"\n'
        f"level: {c['level']}\n"
        "doc_type: catalog\n"
        f"source_url: {CATALOG_URL}\n"
        "---\n\n"
        f"# {c['course_code']}: {c['title']}\n\n"
        "## Description\n\n"
        f"{desc}\n"
    )


def main() -> int:
    page = fetch(CATALOG_URL)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(page, encoding="utf-8")
    courses = parse(page)
    if not courses:
        print("No courses parsed; the catalog layout may have changed.", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = Counter(c["course_code"] for c in courses)
    for c in courses:
        slug = c["course_code"].lower().replace(" ", "-").replace(".", "-")
        if counts[c["course_code"]] > 1:  # generic topics codes repeat per level
            slug += "-" + c["level"].lower().replace("-", "")
        (OUT_DIR / f"{slug}.md").write_text(to_markdown(c), encoding="utf-8")
    print(f"Wrote {len(courses)} course files to {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
