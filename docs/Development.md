# Development

The full contributor guide is [CONTRIBUTING.md](../CONTRIBUTING.md).
This page is the quick map.

## Files

```
custom_components/truenas_apps/
  __init__.py        entry setup/unload, deleting an app's device
  const.py           domain, platforms, timing numbers
  api.py             websocket connection and JSON-RPC calls
  coordinator.py     polling + background app actions
  entity.py          base entity classes, adds entities for new apps/pools
  sensor.py switch.py button.py update.py   one entity platform each
  config_flow.py     setup / reconfigure / re-auth form
  translations/en.json   form text
  brand/             icon.png, icon@2x.png
tests/
  README.md            what each test checks
  test_integration.py  the test run
  test_release.py      the release scripts, publishing against a fake Gitea
  fake_truenas.py      a fake TrueNAS plus a virtual clock
  stubs/               tiny stand-ins for Home Assistant and aiohttp
scripts/             the release helpers both release workflows use (see Tests and releases below)
.gitea/workflows/    tests and releases on Gitea, the main copy (no GitHub needed)
.github/workflows/   GitHub's checks (hassfest, the Marketplace's) and its copy of each release
examples/
  system_information_card.yaml
```

## How it works

1. `coordinator.py` opens a connection (`api.connect`), logs in with the API key, calls `app.query`, `pool.query`,
   `system.version_short` and (optionally) `update.status`, `webui.main.dashboard.sys_info`, `truenas.is_ix_hardware`,
   and closes it. The result is one dict that every entity reads.
2. Entities never talk to TrueNAS themselves, except through `coordinator.app_action`, which starts a job
   (`app.start`, `app.stop`, `app.redeploy`, `app.upgrade`), waits for it via `core.get_jobs`, shows the outcome and refreshes.
3. `entity.add_per_item` creates entities for every app and pool now and for any that appear later.

## Tests

`python3 tests/test_integration.py [days]` runs the real integration against a fake TrueNAS on a virtual clock (a
simulated month in a few seconds; use 90 days before a release). It covers normal running, flaky networks, a revoked
key, odd websocket frames, hangs and outages, apps and pools coming and going, API changes, and every control. It
uses stand-ins instead of real Home Assistant, so real-world testing and GitHub's `hassfest` check still matter.

`python3 tests/test_release.py` checks the release scripts, and `python3 scripts/build_package.py` builds
`dist/truenas_apps.zip` and checks it installs. Gitea's runner runs all of these on every push (30 simulated days).

## Tests and releases: the files

Gitea is the main copy of this repository; it push-mirrors to GitHub, the public copy people install from.

| File | What it does |
|---|---|
| `.gitea/workflows/test.yml` | Runs every check on each push to Gitea (lint, the tests and building the zip, on Python 3.14), with no actions downloaded from GitHub |
| `.gitea/workflows/release.yml` | Publishes a release on Gitea (Run workflow button, or a pushed version tag); its tag then reaches GitHub through the push mirror |
| `.github/workflows/release.yml` | Publishes the same release on GitHub when a version tag arrives there (or from its own Run workflow button): the copy the Marketplace installs from |
| `.github/workflows/ci.yml` | GitHub's checks on every push: lint, the tests and Home Assistant's `hassfest` (which comes from GitHub, so it runs only there) |
| `.github/workflows/validate.yml` | The Marketplace's own checks (the HACS action), which its catalog requires; GitHub only, for the same reason |
| `scripts/release_notes.py` | Shared by both release workflows: checks the version, gives the release's title, writes the notes (install steps with the zip's address on GitHub, then the changelog section) |
| `scripts/build_package.py` | Builds `dist/truenas_apps.zip`, the same bytes every time, and checks it with `check_package.py` |
| `scripts/check_package.py` | Checks the zip the way it gets installed: one `truenas_apps/` folder, a manifest for that domain at the repository's version, the icon, exactly the integration's files |
| `scripts/publish_gitea_release.py` | Creates or updates the Gitea release and uploads its files, through Gitea's API (standard library only) |
| `tests/test_release.py` | Tests all four scripts, publishing against a fake Gitea server |
