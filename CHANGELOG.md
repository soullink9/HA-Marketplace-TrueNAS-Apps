# Changelog

## Unreleased

### Repository

- Gitea is the main copy: its runner checks every push and publishes releases (`.gitea/workflows/`), with nothing
  downloaded from GitHub, so it keeps working when GitHub can't be reached. Gitea push-mirrors to GitHub, and a
  version tag arriving there publishes the same release on GitHub, where the Marketplace installs from.
- The release helpers live in `scripts/` and are used by both: the version check and notes, building the zip, and
  publishing on Gitea. Every release's notes now start with how to install it.
- The release's zip is now always `truenas_apps.zip` (it had the version in its name), so
  `.../releases/latest/download/truenas_apps.zip` always gets the newest. Each zip is checked before it's published.
- The tests run on Python 3.14 (Home Assistant 2026.9's Python, which the workflows use): they stopped before the
  first check there, on a function Python 3.14 deprecates.

## 1.2.0 (2026-11-04)

- Moved to its own repository, [HA-Marketplace-TrueNAS-Apps](https://github.com/soullink9/HA-Marketplace-TrueNAS-Apps), so it can be installed and updated
  from the Home Assistant Marketplace (Home Assistant 2026.11 and newer). Installing by hand works as before.
- Lists its categories, so it shows up in the right place when browsing the Marketplace. No other changes to how
  the integration works.

## 1.1.1 (2026-11-02)

- No changes to the integration.

## 1.1.0 (2026-11-01)

- No changes to the integration.

## 1.0.2 (2026-11-01)

- No changes to the integration.

## 1.0.0 (2026-11-01)

Initial release.

- Every Docker app on TrueNAS becomes a Home Assistant device with:
  - a **status** sensor (running, stopped, crashed, deploying, stopping),
  - an on/off **switch**,
  - **Restart** and **Force recreate** buttons,
  - an **update** entity that shows in Settings → Updates and can install the app update.
- A **TrueNAS** device with a usage-percent sensor per storage pool and a system **update** entity. The system update
  entity shows that an update exists but deliberately cannot install it. Its attributes (hostname, platform, edition,
  version name) feed the example System Information card.
- Setup, **reconfigure** (host, API key, SSL check) and **re-authentication** when TrueNAS rejects the API key.
- Apps removed from TrueNAS can be deleted from Home Assistant's device page.
- Actions run in the background with one action per app at a time; a failure leaves a persistent notification.
- Built to survive long unattended runs: every poll has a time limit, odd or dropped websocket frames are handled,
  and a rejected API key stops polling instead of retrying forever.
