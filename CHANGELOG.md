# Changelog

## 1.4.0 (2026-11-22)

Security hardening, from a security review.

- **Verify SSL certificate is now on by default** for new setups. TrueNAS's default certificate is self-signed, so
  setup now says so plainly ("TrueNAS's certificate couldn't be verified") and explains the two ways forward: install a
  trusted certificate, or turn verification off deliberately. With it off, Home Assistant logs a warning each time the
  integration starts, since a device on the network could pose as TrueNAS and capture the API key. Existing entries keep
  their setting; turn it on with Reconfigure once TrueNAS has a trusted certificate.
- The Reconfigure form no longer pre-fills the saved API key (it was sent back to the browser). Leave the field blank
  to keep the saved key. Re-authentication never shows the old or mistyped key either.
- The host field is checked properly: a valid hostname, IPv4 address or IPv6 address (bare or in brackets) and an
  optional port from 1 to 65535. Empty labels, bad ports, stray brackets and IPv6 zones are refused with a clear
  message, and a bare IPv6 address is stored in brackets so the connection works.
- The optional parts (system update, system information) now only go quiet when TrueNAS refuses them for lack of
  permission. Any other error there is logged as a warning naming the call, once, instead of looking like a
  restricted API key. Error messages from TrueNAS now show its actual reason instead of "Method call error".
- When an app action waits for its TrueNAS job, only the record of that exact job counts: an answer about another job
  is reported as an error instead of being taken as done.
- Error text from TrueNAS is stripped of control characters and capped at 500 characters before it's shown in a
  notification.

### Repository

- The Marketplace (HACS) check and hassfest actions are pinned to a commit instead of following a branch.

## 1.3.0 (2026-11-15)

Built for Home Assistant 2026.11 and the Marketplace. **Needs Home Assistant 2026.11 or newer**: older versions keep
being offered 1.2.0, the last release that runs on them.

- App updates now come straight from TrueNAS's own "update available" flag (Home Assistant's new `has_update`), so an
  app shows an update exactly when TrueNAS says it has one, including when TrueNAS doesn't name the version. The
  TrueNAS system update works the same way.
- Set-up and unload follow Home Assistant 2026.11: an unload that fails now says why instead of failing silently.
- The setup form uses Probatio, Home Assistant's own validation library, directly instead of the old voluptuous name.
- "Settings updated" and "Re-authentication successful" now use Home Assistant's shared wording, translated into
  every language Home Assistant has.
- No backwards-compatibility code for older Home Assistant or Python versions remains: the code is Python 3.14 only.
- The Marketplace installs it without a restart the first time; the docs say so.

### Repository

- Gitea is the main copy: its runner checks every push and publishes releases (`.gitea/workflows/`), with nothing
  downloaded from GitHub, so it keeps working when GitHub can't be reached. Gitea push-mirrors to GitHub, and every
  push from it publishes on GitHub the releases GitHub doesn't have yet, with the same files and notes, where the
  Marketplace installs from.
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
