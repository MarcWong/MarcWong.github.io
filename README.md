<a href="https://jekyll-themes.com">
<img src="https://img.shields.io/badge/featured%20on-JT-red.svg" height="20" alt="Jekyll Themes Shield" >
</a>

# Orbit
> This theme is designed by Xiaoying Riley at [3rd Wave Media](http://themes.3rdwavemedia.com/).
> Visit [her website](http://themes.3rdwavemedia.com/) for more themes.

I have made this into a Jekyll Theme. Checkout the live demo [here](https://online-cv.webjeda.com).

<table>
  <tr>
    <th>Desktop</th>
    <th>Mobile</th>
  </tr>
  <tr>
    <td>
        <img src="https://online-cv.webjeda.com/assets/images/desktop.png?raw=true" width="600"/>
    </td>
    <td>
        <img src="https://online-cv.webjeda.com/assets/images/mobile.png?raw=true" width="250"/>
    </td>
  </tr>
</table>

## Installation

* [Fork](https://github.com/sharu725/online-cv/fork) the repository;
* Go to settings and set master branch as Github Pages source;
* Your new site should be ready at `https://<username>.github.io/online-cv/`;
* Printable version of the site can be found at `https://<username>.github.io/online-cv/print`. Use a third party link https://pdflayer.com/, https://www.web2pdfconvert.com/ etc to get the printable PDF.

Change all the details from one place: `_data/data.yml`.

### To preview/edit locally with docker

```sh
docker-compose up
```

*docker-compose.yml* file is used to create a container that is reachable under <http://localhost:4000>.
Changes *_data/data.yml* will be visible after a while.

### Local machine

* Get the repo into your machine 

```bash
git clone https://github.com/sharu725/online-cv.git
```

* Install required ruby gems

```bash
bundle install
```

* Serve the site locally

```bash
bundle exec jekyll serve
```

* Navigate to `http://localhost:4000`


## Updating Google Scholar citation counts

Each entry under `publications.papers` carries a `citations:` field. When the
value is `> 10`, `_includes/publications.html` renders a small "Cited by N"
badge linking to the Scholar profile defined by `publications.scholar_url`.

The site has two data files, and the script keeps both in step:

| File | Page | Role |
| --- | --- | --- |
| `_data/data.yml` | English (`/`) | source of truth |
| `_data/data_zh.yml` | Chinese (`/zh/`) | mirrors the English papers |

```bash
# Dry run first: shows what would change in both files, writes nothing
python3 scripts/fetch_scholar_citations.py --dry-run

# Apply (Scholar user id defaults to the one in the script)
python3 scripts/fetch_scholar_citations.py
```

What a run does:

1. Copies the whole `publications.papers` block from `data.yml` into
   `data_zh.yml`, so a paper added, removed or reworded in English shows up
   on the Chinese page too (paper entries are untranslated English).
2. Scrapes Scholar once and rewrites the `citations:` lines in **both** files.
3. Warns if the translated parts of `data_zh.yml` have fallen out of step with
   English, e.g. a new memories photo that still needs a Chinese `desp`, or a
   different number of education entries. These need translating by hand.

Useful flags: `--no-sync` (only update counts, don't copy papers),
`--no-fetch` (only sync and check for drift, no Scholar request),
`--min N` (badge threshold), `--data PATH` (repeatable; first file is the
source of truth). Run `python3 scripts/fetch_scholar_citations.py --help`.

Edit paper entries in `data.yml` only; the next run overwrites the papers
block in `data_zh.yml`.

**Caveats**

- Scholar rate-limits and serves a CAPTCHA after repeated scrapes: run
  sparingly (e.g. once a month) and from a residential IP.
- Titles are matched fuzzily; papers with no Scholar match (e.g. very new
  ones) are listed and left untouched.
- Counts at or below `--min` are not written, so a stale larger number is
  never lowered by this script.
- Set `publications.scholar_url` to the profile the badge should link to.

### Total-citations badge

Besides the per-paper badges above, the Publications section also shows a
single **total citations** badge (the shields.io "Cited by N" pill seen on
sites like [taohu.me](https://taohu.me/)) that is refreshed with a single
command instead of manual copy-pasting.

It works like this:

1. [`.github/workflows/google_scholar_crawler.yml`](.github/workflows/google_scholar_crawler.yml)
   can be triggered manually via "Run workflow" in the Actions tab. It has no
   schedule, because Google blocks GitHub's servers (see Troubleshooting).
2. It runs [`google_scholar_crawler/main.py`](google_scholar_crawler/main.py),
   which requests the public Scholar profile of the user in the
   `GOOGLE_SCHOLAR_ID` secret and reads the total citation count (standard
   library only, no dependencies). Requests have hard timeouts, and the job
   itself is capped at 5 minutes: if Google blocks GitHub's servers the run
   fails fast with a CAPTCHA/network message and the last good badge data is
   kept.
3. The result is written as a [shields.io endpoint JSON](https://shields.io/badges/endpoint-badge)
   file and force-pushed to an orphan branch named `google-scholar-stats`
   in this same repo.
4. `_data/data.yml`'s `publications.scholar_badge_url` points a shields.io
   badge at that JSON file on GitHub's raw content CDN, so the badge always
   reflects the last successful crawl.

**One-time setup** (only needed once per fork/repo):

1. Go to **Settings → Secrets and variables → Actions** and add a repository
   secret named `GOOGLE_SCHOLAR_ID` with your Scholar profile's user id
   (the `user=` parameter in your Scholar profile URL, e.g. `X8je0QsAAAAJ`).
2. Go to **Settings → Actions → General → Workflow permissions** and select
   "Read and write permissions" so the workflow's `GITHUB_TOKEN` is allowed
   to push the `google-scholar-stats` branch.
3. Trigger the workflow once manually (Actions tab → "Update Google Scholar
   citation badge" → Run workflow).
4. Update `publications.scholar_badge_url` in `_data/data.yml` to point at
   your own `<owner>/<repo>` on the `google-scholar-stats` branch, e.g.:
   ```
   https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2F<owner>%2F<repo>%2Fgoogle-scholar-stats%2Fgs_data_shieldsio.json&logo=Google%20Scholar&labelColor=f6f6f6&color=9cf&style=flat&label=citations
   ```

Until the workflow has run at least once, the badge URL returns a 404 and
shields.io shows an "invalid" pill — that's expected and resolves itself
after the first successful run.

**Troubleshooting.** Google blocks GitHub-hosted runners (the fetch step fails
with `HTTP 403`), so in practice the badge data is published from your own
machine, where home IPs are normally not blocked:

```bash
bash scripts/publish_scholar_badge.sh
```

This is the one command that refreshes **every** Scholar number on the site:

1. `scripts/fetch_scholar_citations.py` updates the per-paper counts in
   `_data/data.yml` and `_data/data_zh.yml` (see the section above). It only
   edits the files; review and commit them to update the pages.
2. `google_scholar_crawler/main.py` fetches the total, and the script adds a
   commit to the `google-scholar-stats` branch (created on the first run, never
   force-pushed) that the badge reads.

The two steps are independent: if one fails the other still runs and the exit
code is non-zero. Re-run it whenever you like, or schedule it with
`cron`/`launchd`. The Action's daily schedule was removed because it could only
fail while Google blocks it; it is now manual-only.

Do not use the `scholarly` package for this job: when blocked it retries
forever and hangs the workflow.

## Skins

There are 6 color schemes available:

| Blue | Turquoise | Green |
|---------|---------|---------|
| <img src="https://online-cv.webjeda.com/assets/images/blue.jpg" width="300"/> | <img src="https://online-cv.webjeda.com/assets/images/turquoise.jpg" width="300"/> | <img src="https://online-cv.webjeda.com/assets/images/green.jpg" width="300"/> |

| Berry | Orange | Ceramic |
|---------|---------|---------|
| <img src="https://online-cv.webjeda.com/assets/images/berry.jpg" width="300"/> | <img src="https://online-cv.webjeda.com/assets/images/orange.jpg" width="300"/> | <img src="https://online-cv.webjeda.com/assets/images/ceramic.jpg" width="300"/> |

## Credits

Thanks to [Nelson Estevão](https://github.com/nelsonmestevao) for all the [contributions](https://github.com/sharu725/online-cv/commits?author=nelsonmestevao).

Thanks to [t-h-e(sfrost)](https://github.com/t-h-e) for all the [contributions](https://github.com/sharu725/online-cv/commits?author=t-h-e).

Check out for more themes: [**Jekyll Themes**](http://jekyll-themes.com).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sharu725/online-cv&type=Date)](https://star-history.com/#sharu725/online-cv&Date)

