#!/usr/bin/env python3
"""
Fetch per-paper citation counts from a public Google Scholar profile and write
them back into _data/data.yml (the `citations:` field under each paper in
`publications.papers`). Citations >10 trigger the badge in publications.html,
so by default only counts above that threshold are written.

Usage:
    python3 scripts/fetch_scholar_citations.py [SCHOLAR_USER_ID] [options]

Options:
    --dry-run           Show what would change, write nothing.
    --min N             Only write counts strictly greater than N (default 10).
                        Use --min -1 to write every matched paper.
    --data PATH         Path to data.yml (default: _data/data.yml next to this
                        script's repo root).
    --match-ratio R     Fuzzy title match threshold, 0-1 (default 0.85).

Notes:
    - Scholar has no public API. This scrapes the public profile page.
    - Scholar may rate-limit / show a CAPTCHA after repeated calls.
      Run sparingly (e.g. once a month) from a residential IP.
    - Matching is by title, normalised and fuzzy-compared. Papers that don't
      match anything on the profile are reported and left untouched, as are
      commented-out entries in data.yml.
    - Editing is line-based so YAML comments and formatting survive.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
DEFAULT_USER = "X8je0QsAAAAJ"  # Yao Wang
URL_TEMPLATE = (
    "https://scholar.google.com/citations?"
    "user={user}&hl=en&cstart=0&pagesize=200"
)
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = REPO_ROOT / "_data" / "data.yml"


# --------------------------------------------------------------------------- #
# Google Scholar
# --------------------------------------------------------------------------- #
def fetch(user_id: str) -> str:
    req = urllib.request.Request(URL_TEMPLATE.format(user=user_id), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(page: str) -> list[tuple[int, str, str]]:
    rows = re.findall(r'<tr class="gsc_a_tr">.*?</tr>', page, re.S)
    out = []
    for r in rows:
        title_m = re.search(r'gsc_a_at[^>]*>([^<]+)</a>', r)
        cites_m = re.search(r'gsc_a_ac[^>]*>([^<]*)</', r)
        year_m = re.search(r'gsc_a_h[^>]*>([^<]*)</', r)
        if not title_m:
            continue
        title = html.unescape(title_m.group(1))
        cites_raw = (cites_m.group(1) if cites_m else "").strip() or "0"
        try:
            cites = int(cites_raw)
        except ValueError:
            cites = 0
        year = year_m.group(1).strip() if year_m else ""
        out.append((cites, year, title))
    return out


# --------------------------------------------------------------------------- #
# data.yml
# --------------------------------------------------------------------------- #
class Paper:
    """One `- title:` entry under publications.papers, located by line number."""

    def __init__(self, title: str, title_line: int):
        self.title = title
        self.title_line = title_line
        self.citations_line: int | None = None
        self.citations: int | None = None


def normalise(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def load_papers(lines: list[str]) -> list[Paper]:
    """Locate the publications.papers block and each uncommented paper in it."""
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^publications:\s*$", line):
            start = i
            break
    if start is None:
        return []

    papers: list[Paper] = []
    current: Paper | None = None
    in_papers = False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        # A new top-level key ends the publications block.
        if line and not line[0].isspace() and not stripped.startswith("#"):
            break
        if re.match(r"^\s*papers:\s*$", line):
            in_papers = True
            continue
        if not in_papers or stripped.startswith("#") or not stripped:
            continue

        title_m = re.match(r"^\s*-\s*title:\s*(.+?)\s*$", line)
        if title_m:
            current = Paper(unquote(title_m.group(1)), i)
            papers.append(current)
            continue
        cites_m = re.match(r"^\s*citations:\s*(\d+)\s*$", line)
        if cites_m and current is not None and current.citations_line is None:
            current.citations_line = i
            current.citations = int(cites_m.group(1))
    return papers


def best_match(title: str, scholar: list[tuple[int, str, str]], ratio: float):
    """Return (cites, scholar_title, score) for the closest Scholar entry."""
    target = normalise(title)
    best = None
    for cites, _year, s_title in scholar:
        score = SequenceMatcher(None, target, normalise(s_title)).ratio()
        if best is None or score > best[2]:
            best = (cites, s_title, score)
    if best is None or best[2] < ratio:
        return None
    return best


def apply_updates(lines: list[str], paper: Paper, cites: int) -> None:
    """Rewrite (or insert) the citations line for one paper."""
    if paper.citations_line is not None:
        line = lines[paper.citations_line]
        indent = line[: len(line) - len(line.lstrip())]
        lines[paper.citations_line] = f"{indent}citations: {cites}"
        return
    # No citations field yet: insert one indented to match the title's siblings.
    title_line = lines[paper.title_line]
    indent = " " * (len(title_line) - len(title_line.lstrip()) + 2)
    lines.insert(paper.title_line + 1, f"{indent}citations: {cites}")
    paper.citations_line = paper.title_line + 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("user", nargs="?", default=DEFAULT_USER, help="Google Scholar user id")
    ap.add_argument("--dry-run", action="store_true", help="show changes without writing")
    ap.add_argument("--min", type=int, default=10, help="only write counts strictly above this (default 10)")
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA, help="path to data.yml")
    ap.add_argument("--match-ratio", type=float, default=0.85, help="fuzzy title match threshold")
    args = ap.parse_args()

    if not args.data.is_file():
        print(f"data file not found: {args.data}", file=sys.stderr)
        return 1

    page = fetch(args.user)
    if "captcha" in page.lower() or "unusual traffic" in page.lower():
        print("Scholar served a CAPTCHA. Try again later.", file=sys.stderr)
        return 2
    scholar = parse(page)
    if not scholar:
        print("No publications parsed. Profile private or markup changed.", file=sys.stderr)
        return 1

    text = args.data.read_text(encoding="utf-8")
    lines = text.split("\n")
    papers = load_papers(lines)
    if not papers:
        print("No papers found under publications.papers in data.yml.", file=sys.stderr)
        return 1

    edits: list[tuple[Paper, int]] = []
    unmatched: list[str] = []
    skipped: list[str] = []
    print(f"{'old':>5} {'new':>5}  {'score':>5}  Title")
    print("-" * 78)
    for paper in papers:
        match = best_match(paper.title, scholar, args.match_ratio)
        if match is None:
            unmatched.append(paper.title)
            continue
        cites, s_title, score = match
        if cites <= args.min:
            skipped.append(f"{paper.title} ({cites} citations)")
            continue
        old = "-" if paper.citations is None else str(paper.citations)
        if str(cites) == old:
            continue
        print(f"{old:>5} {cites:>5}  {score:>5.2f}  {paper.title}")
        if score < 0.97:
            print(f"{'':>19}  ^ Scholar title: {s_title}")
        edits.append((paper, cites))

    changed = len(edits)
    if changed and not args.dry_run:
        # Bottom-up so an inserted citations line never shifts a pending edit.
        for paper, cites in reversed(edits):
            apply_updates(lines, paper, cites)
        args.data.write_text("\n".join(lines), encoding="utf-8")

    print()
    if changed:
        action = "would update" if args.dry_run else "updated"
        print(f"{action} {changed} paper(s) in {args.data}")
    else:
        print("all citation counts already up to date")
    if skipped:
        print(f"\nskipped (<= {args.min} citations, badge threshold):")
        for s in skipped:
            print(f"  - {s}")
    if unmatched:
        print("\nno Scholar match (left untouched):")
        for t in unmatched:
            print(f"  - {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
