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

Each entry under `publications.papers` in `_data/data.yml` carries a
`citations:` field. When the value is `> 10`, `_includes/publications.html`
renders a small "Cited by N" badge linking to the Scholar profile defined by
`publications.scholar_url`.

Google Scholar has no public API, so the workflow is **scrape → eyeball → paste**:

```bash
# Uses the Scholar user id from _data/data.yml by default
python3 scripts/fetch_scholar_citations.py

# Or pass another profile's id explicitly
python3 scripts/fetch_scholar_citations.py X8je0QsAAAAJ
```

The script prints the full publication list with citation counts and marks
the rows that qualify for the badge:

```
Cites  Year  Title
----------------------------------------------------------------------
  123 *2018  Large-scale Structure from Motion with Semantic Constraints ...
   41 *2023  Scanpath Prediction on Information Visualisations
   25 *2024  SalChartQA: Question-driven Saliency on Information ...
   ...
* = qualifies for the citation badge (citations > 10).
```

Copy the numbers into the matching `citations:` lines in
`_data/data.yml`. Titles in Scholar may differ slightly from the ones in
`data.yml`, so match by eye rather than by string equality.

**Caveats**

- Scholar rate-limits and serves a CAPTCHA after repeated scrapes — run
  sparingly (e.g. once a month) and from a residential IP.
- The script never edits `data.yml` for you; that step is manual on
  purpose so a flaky scrape can't corrupt the data.
- Set `publications.scholar_url` in `_data/data.yml` to the profile the
  badge should link to.

### Live total-citations badge (auto-updating)

Besides the per-paper badges above, the Publications section also shows a
single **total citations** badge (the shields.io "Cited by N" pill seen on
sites like [taohu.me](https://taohu.me/)) that updates itself daily without
any manual copy-pasting.

It works like this:

1. [`.github/workflows/google_scholar_crawler.yml`](.github/workflows/google_scholar_crawler.yml)
   runs on a daily cron (and can be triggered manually via
   "Run workflow" in the Actions tab).
2. It runs [`google_scholar_crawler/main.py`](google_scholar_crawler/main.py),
   which uses the [`scholarly`](https://pypi.org/project/scholarly/) Python
   package to look up the author identified by the `GOOGLE_SCHOLAR_ID`
   secret and read their total citation count.
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
   citation badge" → Run workflow) instead of waiting for the next cron run.
4. Update `publications.scholar_badge_url` in `_data/data.yml` to point at
   your own `<owner>/<repo>` on the `google-scholar-stats` branch, e.g.:
   ```
   https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2F<owner>%2F<repo>%2Fgoogle-scholar-stats%2Fgs_data_shieldsio.json&logo=Google%20Scholar&labelColor=f6f6f6&color=9cf&style=flat&label=citations
   ```

Until the workflow has run at least once, the badge URL returns a 404 and
shields.io shows an "invalid" pill — that's expected and resolves itself
after the first successful run.

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

