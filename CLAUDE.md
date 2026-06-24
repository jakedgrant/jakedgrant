# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two unrelated things share this repo:

1. **GitHub profile** — `README.md` renders on the GitHub profile page at https://github.com/jakedgrant (this is the special `jakedgrant/jakedgrant` repo). Editing it just updates the profile.
2. **A static website published via GitHub Pages from `docs/`**, served at `jakegrant.dev`. Pages runs Jekyll: `docs/index.md` (Markdown) is the site root, and `docs/smartfilter/` is a hand-written static HTML/CSS/JS promo + privacy site for the SmartFilter iOS app.

There is no build step you run locally and no package manager — Pages builds and deploys on push to `main`.

## Commands

The only tooling is the Python test suite for the SmartFilter site (standard library only, no dependencies):

```bash
python3 -m unittest discover -s tests -v          # run all tests
python3 -m unittest tests.test_site -v            # run the one test module
python3 -m unittest tests.test_site.TestClass.test_method -v   # single test
```

CI (`.github/workflows/site-tests.yml`) runs the same `unittest discover` on push/PR, but **only** when `docs/smartfilter/**`, `tests/**`, or the workflow file change.

## What the tests guard (read before editing `docs/smartfilter/`)

`tests/test_site.py` enforces invariants that silently break hosting or the App Store download flow. When editing the SmartFilter pages, keep these intact or update the test constants to match:

- **No Jekyll processing of the HTML.** The pages must have no YAML front-matter and no Liquid tags so Pages serves them verbatim instead of wrapping them in a theme. (`docs/index.md` is the opposite — it *is* Jekyll Markdown.)
- **App Store ID `1271258894`** must stay consistent across the Smart App Banner and store links. It's hardcoded in the test because the app source lives in a separate repo.
- Canonical/social URLs anchored to `https://jakegrant.dev/smartfilter/`, support email `smartfilterapp@gmail.com`, link/asset/anchor integrity, and the Apple Smart App Banner meta tag.

## Gotchas

- **The custom domain lives in `docs/CNAME` (`jakegrant.dev`), not the repo root.** Pages reads `CNAME` from the publishing source root, which is `docs/`. The apex `jakegrant.dev` is canonical and is hardcoded throughout the SmartFilter site and tests, so keep any domain config on the apex.
- `docs/smartfilter/js/main.js` is intentionally dependency-free progressive enhancement (footer year, dismissible banner). It hides the custom download banner on iOS Safari because Apple's native Smart App Banner takes over there.
