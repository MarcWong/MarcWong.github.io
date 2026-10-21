#!/usr/bin/env python3
"""
Fetch per-paper citation counts from a public Google Scholar profile and write
them back into the site data files (the `citations:` field under each paper in
`publications.papers`). Citations >10 trigger the badge in publications.html,
so by default only counts above that threshold are written.

The English file (_data/data.yml) is the source of truth. The Chinese page
(_data/data_zh.yml) mirrors it: before citations are written, the whole
`publications.papers` block is copied from the English file into the Chinese
one (paper entries are untranslated English), so both sites always show the
same papers and the same counts. Translated text elsewhere in the Chinese file
cannot be copied automatically; the script only warns when its structure has
drifted from the English file (different photos / education entries).

Usage:
    python3 scripts/fetch_scholar_citations.py [SCHOLAR_USER_ID] [options]

Options:
    --dry-run           Show what would change, write nothing.
    --min N             Only write counts strictly greater than N (default 10).
                        Use --min -1 to write every matched paper.
    --data PATH         Data file to update; repeat for several. The first one
                        is the source of truth, the rest mirror it. Default:
                        _data/data.yml then _data/data_zh.yml.
    --no-sync           Don't copy publications.papers from the first file into
                        the others; just update citations in each file.
    --no-fetch          Skip Google Scholar entirely; only sync and check drift.
    --match-ratio R     Fuzzy title match threshold, 0-1 (default 0.85).

Notes:
    - Scholar has no public API. This scrapes the public profile page.
    - Scholar may rate-limit / show a CAPTCHA after repeated calls.
      Run sparingly (e.g. once a month) from a residential IP.
    - Matching is by title, normalised and fuzzy-compared. Papers that don't
      match anything on the profile are reported and left untouched, as are
      commented-out entries in the data files.
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
DEFAULT_DATA = [
    REPO_ROOT / "_data" / "data.yml",  # English, source of truth
    REPO_ROOT / "_data" / "data_zh.yml",  # Chinese, mirrors the English papers
]


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


def papers_block(lines: list[str]) -> tuple[int, int] | None:
    """Return [start, end) line range of the `papers:` key and its entries,
    including commented-out entries, excluding trailing blank lines."""
    pub = next((i for i, l in enumerate(lines) if re.match(r"^publications:\s*$", l)), None)
    if pub is None:
        return None
    start = indent = None
    for i in range(pub + 1, len(lines)):
        m = re.match(r"^(\s*)papers:\s*$", lines[i])
        if m:
            start, indent = i, len(m.group(1))
            break
        if lines[i] and not lines[i][0].isspace():
            return None  # left the publications block without finding papers
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return start, end


def sync_papers(src: list[str], dst: list[str]) -> bool:
    """Replace dst's publications.papers block with src's. True if dst changed."""
    s_rng, d_rng = papers_block(src), papers_block(dst)
    if s_rng is None or d_rng is None:
        return False
    new = src[s_rng[0]:s_rng[1]]
    if dst[d_rng[0]:d_rng[1]] == new:
        return False
    dst[d_rng[0]:d_rng[1]] = new
    return True


def drift_warnings(src: list[str], dst: list[str]) -> list[str]:
    """Structure that must be translated by hand but should still line up."""
    def photos(lines):
        found = (re.match(r"^\s*-\s*name:\s*(/assets/images/\S+)\s*$", l) for l in lines)
        return [m.group(1) for m in found if m]

    def degrees(lines):
        return [l for l in lines if re.match(r"^\s*-\s*degree:", l)]

    out = []
    sp, dp = photos(src), photos(dst)
    for name in [n for n in sp if n not in dp]:
        out.append(f"memories photo missing (needs a translated desp): {name}")
    for name in [n for n in dp if n not in sp]:
        out.append(f"memories photo not in the English file: {name}")
    if len(degrees(src)) != len(degrees(dst)):
        out.append(f"education entries differ: {len(degrees(src))} (en) vs {len(degrees(dst))}")
    return out


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
def update_citations(lines: list[str], scholar, args) -> int:
    """Print the change table for one file and apply it to `lines` in place.
    Returns the number of papers changed."""
    papers = load_papers(lines)
    if not papers:
        print("No papers found under publications.papers.", file=sys.stderr)
        return 0

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

    # Bottom-up so an inserted citations line never shifts a pending edit.
    for paper, cites in reversed(edits):
        apply_updates(lines, paper, cites)

    if not edits:
        print("all citation counts already up to date")
    if skipped:
        print(f"skipped (<= {args.min} citations, badge threshold):")
        for t in skipped:
            print(f"  - {t}")
    if unmatched:
        print("no Scholar match (left untouched):")
        for t in unmatched:
            print(f"  - {t}")
    return len(edits)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("user", nargs="?", default=DEFAULT_USER, help="Google Scholar user id")
    ap.add_argument("--dry-run", action="store_true", help="show changes without writing")
    ap.add_argument("--min", type=int, default=10, help="only write counts strictly above this (default 10)")
    ap.add_argument("--data", type=Path, action="append", help="data file (repeatable); first is the source of truth")
    ap.add_argument("--no-sync", action="store_true", help="don't mirror publications.papers from the first file")
    ap.add_argument("--no-fetch", action="store_true", help="skip Scholar; only sync and check drift")
    ap.add_argument("--match-ratio", type=float, default=0.85, help="fuzzy title match threshold")
    args = ap.parse_args()
    paths: list[Path] = args.data or DEFAULT_DATA

    for path in paths:
        if not path.is_file():
            print(f"data file not found: {path}", file=sys.stderr)
            return 1

    scholar: list[tuple[int, str, str]] = []
    if not args.no_fetch:
        page = fetch(args.user)
        if "captcha" in page.lower() or "unusual traffic" in page.lower():
            print("Scholar served a CAPTCHA. Try again later.", file=sys.stderr)
            return 2
        scholar = parse(page)
        if not scholar:
            print("No publications parsed. Profile private or markup changed.", file=sys.stderr)
            return 1

    originals = [path.read_text(encoding="utf-8") for path in paths]
    files = [text.split("\n") for text in originals]
    source = files[0]

    synced: list[Path] = []
    if not args.no_sync:
        for path, lines in zip(paths[1:], files[1:]):
            if sync_papers(source, lines):
                synced.append(path)

    for path, lines in zip(paths, files):
        print(f"\n=== {path.name} ===")
        if path in synced:
            print(f"publications.papers mirrored from {paths[0].name}")
        if not args.no_fetch:
            update_citations(lines, scholar, args)

    drift = [(path, w) for path, lines in zip(paths[1:], files[1:]) for w in drift_warnings(source, lines)]

    wrote = []
    for path, text, lines in zip(paths, originals, files):
        new_text = "\n".join(lines)
        if new_text != text:
            wrote.append(path)
            if not args.dry_run:
                path.write_text(new_text, encoding="utf-8")

    print()
    verb = "would update" if args.dry_run else "updated"
    if wrote:
        print(f"{verb}: " + ", ".join(p.name for p in wrote))
    else:
        print("nothing to change; all data files are up to date")
    for path, w in drift:
        print(f"WARNING {path.name}: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
