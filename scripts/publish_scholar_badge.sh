#!/usr/bin/env bash
# One command to refresh every Google Scholar number on the site, from THIS machine:
#
#   1. per-paper citation counts in _data/data.yml and _data/data_zh.yml
#      (scripts/fetch_scholar_citations.py; edits the files, does not commit)
#   2. the total-citations badge, published to the google-scholar-stats branch
#      (google_scholar_crawler/main.py)
#
# Google blocks GitHub-hosted runners (HTTP 403), so the Action cannot do this;
# a home IP normally works. Step 2 needs push access to `origin`; it adds a
# commit to the branch (created on first run) and never force-pushes.
# Each step is independent: if one fails the other still runs, and the exit
# code is non-zero.
#
#   bash scripts/publish_scholar_badge.sh
#
# Environment overrides: GOOGLE_SCHOLAR_ID, SCHOLAR_BADGE_REMOTE (default: origin)
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
branch="google-scholar-stats"
remote="${SCHOLAR_BADGE_REMOTE:-$(git -C "$repo" remote get-url origin)}"
export GOOGLE_SCHOLAR_ID="${GOOGLE_SCHOLAR_ID:-X8je0QsAAAAJ}"
failed=0
data_hash() { cat "$repo/_data/data.yml" "$repo/_data/data_zh.yml" | shasum; }
data_before="$(data_hash)"

echo "==> 1/2 Per-paper citation counts (data.yml + data_zh.yml)"
python3 "$repo/scripts/fetch_scholar_citations.py" "$GOOGLE_SCHOLAR_ID" \
  || { echo "WARNING: per-paper update failed (see above); continuing." >&2; failed=1; }

echo
echo "==> 2/2 Total-citations badge"
cd "$repo/google_scholar_crawler"
python3 main.py

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
  git clone -q --depth 1 --branch "$branch" "$remote" "$work/data"
else
  git init -q "$work/data"
  git -C "$work/data" symbolic-ref HEAD "refs/heads/$branch"
  git -C "$work/data" remote add origin "$remote"
fi

cp results/gs_data.json results/gs_data_shieldsio.json "$work/data/"
cd "$work/data"
git add gs_data.json gs_data_shieldsio.json

# Nothing to publish if the badge number did not change.
if git rev-parse -q --verify HEAD >/dev/null && git diff --cached --quiet -- gs_data_shieldsio.json; then
  echo "Badge already shows the current count; nothing to publish."
else
  count="$(python3 -c 'import json;print(json.load(open("gs_data_shieldsio.json"))["message"])')"
  git -c user.name="$(git -C "$repo" config user.name)" \
      -c user.email="$(git -C "$repo" config user.email)" \
      commit -q -m "Update citation data: $count"
  git push -q origin "HEAD:$branch"
  echo "Published $count citations to the $branch branch."
fi

echo
if [ "$(data_hash)" != "$data_before" ]; then
  echo "Citation counts changed in _data/data.yml / data_zh.yml; commit them to update the pages."
fi
exit "$failed"
