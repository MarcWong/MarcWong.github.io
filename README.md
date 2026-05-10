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

