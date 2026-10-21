"""
Read the total citation stats from a public Google Scholar profile and write
them as JSON for the shields.io "citations" badge.

Outputs, in ./results/:
    gs_data.json             citedby / hindex / i10index + timestamp
    gs_data_shieldsio.json   shields.io endpoint payload for the badge

Uses a plain HTTP request with hard timeouts rather than the `scholarly`
package: when Google blocks the caller (typical for GitHub-hosted runners),
`scholarly` retries forever and hangs the job, whereas this fails within a
minute with a clear message and writes nothing, so the last good badge data on
the google-scholar-stats branch is left untouched.

Usage:  GOOGLE_SCHOLAR_ID=<user id> python main.py
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
URL = "https://scholar.google.com/citations?user={user}&hl=en"
TIMEOUT = 20  # seconds per request
TRIES = 3


def fetch(user_id: str) -> str:
    last = "unknown error"
    for attempt in range(1, TRIES + 1):
        try:
            req = urllib.request.Request(
                URL.format(user=user_id),
                headers={"User-Agent": UA, "Accept-Language": "en"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                final_url = resp.geturl()
                body = resp.read().decode("utf-8", errors="replace")
            low = body.lower()
            if "/sorry/" in final_url or "unusual traffic" in low or "captcha" in low:
                last = "Google served a CAPTCHA / 'unusual traffic' page (this IP is blocked)"
            else:
                return body
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {e.reason}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = f"network error: {e}"
        print(f"attempt {attempt}/{TRIES} failed: {last}", file=sys.stderr)
        if attempt < TRIES:
            time.sleep(5 * attempt)
    sys.exit(f"Could not read the Scholar profile: {last}")


def parse(page: str) -> dict:
    # The "Cited by" box lists six numbers: citations, h-index, i10-index,
    # each as (all, since-year) pairs.
    cells = re.findall(r'class="gsc_rsb_std">(\d+)<', page)
    if len(cells) < 6:
        sys.exit("Profile loaded but the stats table is missing (private profile or markup changed).")
    return {
        "citedby": int(cells[0]),
        "hindex": int(cells[2]),
        "i10index": int(cells[4]),
    }


def main() -> None:
    user_id = os.environ.get("GOOGLE_SCHOLAR_ID")
    if not user_id:
        sys.exit("GOOGLE_SCHOLAR_ID is not set.")

    stats = parse(fetch(user_id))
    stats["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    os.makedirs("results", exist_ok=True)
    with open("results/gs_data.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)
    with open("results/gs_data_shieldsio.json", "w", encoding="utf-8") as f:
        json.dump(
            {"schemaVersion": 1, "label": "citations", "message": str(stats["citedby"])},
            f,
            ensure_ascii=False,
        )
    print(f"citations={stats['citedby']} h-index={stats['hindex']} i10-index={stats['i10index']}")


if __name__ == "__main__":
    main()
