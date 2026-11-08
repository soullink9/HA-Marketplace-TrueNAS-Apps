# Contributing to TrueNAS Apps

Thanks for helping. This page is for anyone changing the code: where things live, the rules the code keeps, how
to check a change, and how to release one.

## Ground rules

- **Stay slim.** The integration deliberately exposes only Docker apps, their status and updates, controls, pool
  usage and the TrueNAS system update. Please open an issue before adding a new kind of entity.
- **No dependencies.** `manifest.json` has no `requirements`. The websocket client is the `aiohttp` that ships
  with Home Assistant, and the API is plain JSON-RPC.
- **No JavaScript, no custom cards.** Dashboards use Home Assistant's built-in cards (see `examples/`).
- **Never install a TrueNAS system update from Home Assistant.** That should stay a deliberate action in the
  TrueNAS UI, after a backup. `SystemUpdate.async_install` refuses on purpose.
- **Never let a failure escape unseen.** Polling failures become `UpdateFailed` (entities go unavailable and retry);
  background actions end in a persistent notification; everything has a timeout.
- **Keep unique ids stable.** Changing them orphans every user's entities.

## Where things live

| File | What it does |
|---|---|
| `const.py` | The domain, the platform list and every timing number. |
| `api.py` | The websocket connection: connect, log in, `call(method, params)`. |
| `coordinator.py` | Polls TrueNAS once a minute and runs start/stop/restart/upgrade jobs in the background. |
| `entity.py` | Base classes (`AppEntity`, `SystemEntity`) and `add_per_item`, which adds entities for new apps and pools. |
| `sensor.py`, `switch.py`, `button.py`, `update.py` | One entity platform each. |
| `config_flow.py` | Setup, reconfigure and re-authentication share one form. |
| `__init__.py` | Entry setup/unload and deleting an app's device. |
| `translations/en.json` | Text for the setup form. |
| `brand/` | The integration's icon (used by Home Assistant 2026.3 and newer, no brands repository needed). |

**Adding a button:** add a line to `BUTTONS` in `button.py` (name, device class, the `app.*` methods to run).

**Asking TrueNAS for something new:** add the call to `_async_update_data` in `coordinator.py` (use `optional()` if a
limited API key might not be allowed), add its result to the returned dict, and document the key in the class
docstring.

## Checking a change

You need Python 3.13 or newer (Home Assistant 2026.9 itself runs on 3.14, which is what the workflows use) and
[ruff](https://docs.astral.sh/ruff/) (`pip install ruff`).

| Command | When |
|---|---|
| `ruff check custom_components tests` and `ruff format custom_components tests` | every change |
| `python3 tests/test_integration.py` | every change (seconds) |
| `python3 tests/test_integration.py 90` | before a release (90 simulated days) |
| `python3 tests/test_release.py` | any change to `scripts/` or the release workflows |
| `python3 scripts/build_package.py` | before a release: builds `dist/truenas_apps.zip` and checks it installs |

The tests use a fake TrueNAS (`fake_truenas.py`) and small stand-ins for Home Assistant and aiohttp (`stubs/`), so
they need no installs and no real server, and months of polling take seconds. They exercise the integration's own
code paths (polling, failure handling, app actions, entity values, device removal), but can't prove it works with
real Home Assistant. Try a change on a real instance too.

Gitea's runner runs `ruff`, 30 simulated days, the release tests and the zip build on every push
(`.gitea/workflows/test.yml`). On GitHub the same checks run plus Home Assistant's `hassfest` and the Marketplace's
own checks, which come from GitHub and can only run there. [tests/README.md](tests/README.md) lists what each test
checks.

Code style: `ruff` settles formatting and import order (see `pyproject.toml`). Every function and class has a
docstring, and comments say why, not what.

## Documentation

[README.md](README.md) is the front page, and every other page lives in [`docs/`](docs). When a change alters
something a page describes, update that page in the same commit.

## Standards for every change

- **Readable over clever.** Write code a newcomer can follow on the first read. Prefer a few plain lines with a named
  variable to a dense one-liner, a nested conditional expression, or a trick that needs a comment to decode.
- **Comment the why.** Every function and class has a docstring. Comments explain why the code does something
  non-obvious (a quirk of the device or service, a Home Assistant rule, a deliberate trade-off), not what each line
  does.
- **Keep names consistent.** Follow the names already used in the integration: the same words for
  the same things, Home Assistant's conventions for entities and config entries, `snake_case` for Python names and
  `camelCase` for JavaScript.
- **Keep the docs in step.** When you change a function, class or behaviour, update its docstring, its comments and the
  pages under `docs/` (and the README) that describe it in the same commit.
- **Keep the tests green.** Every change keeps existing behaviour and passes all of the tests. When you
  fix a bug, add the situation that caused it to the tests so it stays fixed.
- **No new dependencies without approval.** Don't add a third-party library (to a `manifest.json`, a
  `requirements.txt` or CI) without asking in an issue first. This page says what it already depends on and why.

### Test layout

The tests use these names:

```
tests/
  stubs.py                stand-ins for Home Assistant and the libraries the integration uses
  test_integration.py     the real integration against the stand-ins and a fake device or service
  test_<subject>.py       any other checks (test_engine.py, test_blueprint.py, test_live_proxy.py)
  test_<subject>_soak.py  a long simulation: it takes a length as an argument, and CI runs a short one
  fake_<service>.py       a fake device or service, when it's too big to live inside the test
  requirements.txt        what the tests need beyond Python, if they need anything
```

Every `test_*.py` is a plain script, not a pytest suite: run it with `python3` from the repository root, and it
exits non-zero if any check fails.

### The Marketplace

`hacs.json` at the root is the Marketplace's file: the name it lists and the oldest Home Assistant version the
integration works with. Keep that version in step with the README's requirements.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): a type, an optional scope, then a short summary in
the imperative.

```
feat: add a diagnostics download
fix: keep the last value when the service is briefly unreachable
refactor: split the coordinator's update into steps
docs: explain the safety settings
test: cover a reply with a missing field
chore: update the CI actions
```

## Releasing

Gitea is the main copy of this repository. It push-mirrors to GitHub, which is the public copy: the Marketplace
installs from GitHub's releases, so every link in the docs and release notes points there.

1. Bump `version` in `custom_components/truenas_apps/manifest.json`. Versions go up together: there is only this
   one.
2. Add the release to the top of [CHANGELOG.md](CHANGELOG.md), under a heading `## X.Y.Z (date)` (move what's under
   `## Unreleased` into it).
3. Run the checks above, the 90-day run included.
4. Commit and push to Gitea, then publish with Gitea's **Release** workflow (`.gitea/workflows/release.yml`),
   either way:
   - **Actions → Release → Run workflow**, and enter the version without the `v` (for example `1.2.1`). It
     creates the tag `v1.2.1` on the commit it releases.
   - or push a version tag: `git tag v1.2.1 && git push origin v1.2.1`.

   The workflow checks the version matches the manifest and `CHANGELOG.md` (`scripts/release_notes.py`), runs every
   check, builds `truenas_apps.zip` and checks it installs as `custom_components/truenas_apps/`
   (`scripts/build_package.py`), and publishes the release on Gitea with the zip and notes: install steps, then that
   version's changelog section (`scripts/publish_gitea_release.py`). A version with a suffix (`-beta`) is published
   as a pre-release. If any check fails, nothing is published. Running it again for the same version updates the
   release and replaces its zip.

5. Gitea's push mirror then sends the commits and the new tag to GitHub, where the tag starts GitHub's own
   **Release** workflow (`.github/workflows/release.yml`), which runs the same checks and publishes the same
   release there. The Marketplace picks it up from GitHub. If GitHub is down, the mirror catches up later; the Gitea
   release is already done.

The Gitea workflows use no actions (`actions/checkout` and the like download from GitHub): each job runs in a plain
image from Docker Hub (`python:3.14-bookworm`) and fetches the code from Gitea with git, so testing and releasing
keep working when GitHub can't be reached. Only `ruff` comes from PyPI. When the runner's jobs can't reach Gitea at
its public address (a runner on the same Docker network as Gitea, say), set an Actions variable `GITEA_INTERNAL_URL`
to the address they can reach (`http://gitea-server:3000`); both workflows and the publish script use it.

Keep every tag on Gitea: the push mirror makes GitHub's tags match Gitea's, so a tag missing from Gitea is deleted on
GitHub, and the GitHub release on it turns into a draft.

## Reporting bugs

Open an issue with your Home Assistant, TrueNAS and integration versions, what you did and what you expected.
The log helps: **Settings → System → Logs**, search for `truenas_apps`. Remove API keys and hostnames you don't
want public before posting.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).
