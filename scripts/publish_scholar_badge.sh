#!/usr/bin/env bash
# Fetch the Scholar total-citations badge data on THIS machine and publish it to
# the google-scholar-stats branch that the site's badge reads from.
#
# Google blocks GitHub-hosted runners (HTTP 403), so the Action cannot do this;
# a home IP normally works. Needs push access to `origin`. Safe to re-run: it
# adds a commit to the branch (created on first run) and never force-pushes.
#
#   bash scripts/publish_scholar_badge.sh
#
# Environment overrides: GOOGLE_SCHOLAR_ID, SCHOLAR_BADGE_REMOTE (default: origin)
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
branch="google-scholar-stats"
remote="${SCHOLAR_BADGE_REMOTE:-$(git -C "$repo" remote get-url origin)}"

cd "$repo/google_scholar_crawler"
export GOOGLE_SCHOLAR_ID="${GOOGLE_SCHOLAR_ID:-X8je0QsAAAAJ}"
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
  exit 0
fi

count="$(python3 -c 'import json;print(json.load(open("gs_data_shieldsio.json"))["message"])')"
git -c user.name="$(git -C "$repo" config user.name)" \
    -c user.email="$(git -C "$repo" config user.email)" \
    commit -q -m "Update citation data: $count"
git push -q origin "HEAD:$branch"
echo "Published $count citations to the $branch branch."
