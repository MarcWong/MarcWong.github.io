#!/usr/bin/env python3
"""
Fetch per-paper citation counts from a public Google Scholar profile and
print them so they can be pasted into _data/data.yml (the `citations:` field
under each paper). Citations >10 trigger the badge in publications.html.

Usage:
    python3 scripts/fetch_scholar_citations.py [SCHOLAR_USER_ID]

If no user id is given, falls back to the one in _data/data.yml.

Notes:
    - Scholar has no public API. This scrapes the public profile page.
    - Scholar may rate-limit / show a CAPTCHA after repeated calls.
      Run sparingly (e.g. once a month) from a residential IP.
    - Title strings in Scholar may differ slightly from data.yml; match by
      eye when copying numbers across.
"""
from __future__ import annotations

import html
import re
import sys
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
DEFAULT_USER = "X8je0QsAAAAJ"  # Yao Wang
URL_TEMPLATE = (
    "https://scholar.google.com/citations?"
    "user={user}&hl=en&cstart=0&pagesize=200"
)


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


def main() -> int:
    user = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    page = fetch(user)
    if "captcha" in page.lower() or "unusual traffic" in page.lower():
        print("Scholar served a CAPTCHA. Try again later.", file=sys.stderr)
        return 2
    rows = parse(page)
    if not rows:
        print("No publications parsed. Profile private or markup changed.", file=sys.stderr)
        return 1
    print(f"{'Cites':>5}  {'Year':<4}  Title")
    print("-" * 70)
    for cites, year, title in rows:
        marker = " *" if cites > 10 else "  "
        print(f"{cites:>5}{marker}{year:<4}  {title}")
    print("\n* = qualifies for the citation badge (citations > 10).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
