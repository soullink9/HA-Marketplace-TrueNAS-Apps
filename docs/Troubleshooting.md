# Troubleshooting

Start with the log: **Settings → System → Logs**, search for `truenas_apps`.

## Setup says "Cannot connect to TrueNAS"

- Check the host. Use just the name or IP (`truenas.local`, `192.168.1.10`), with `:port` if needed. No `https://`.
- Home Assistant connects with `wss://` (secure websocket), so TrueNAS's HTTPS must be reachable from Home Assistant.
- The API key must be allowed to read apps (setup tests this).

## Setup says "TrueNAS's certificate couldn't be verified"

**Verify SSL certificate** is on (the default) and Home Assistant doesn't trust the certificate TrueNAS presented.
Out of the box TrueNAS uses a self-signed certificate, which always fails this check. Either:

- install a certificate Home Assistant trusts on TrueNAS (for example from Let's Encrypt, in TrueNAS under
  **Credentials → Certificates**) and enter the name on that certificate as the host, or
- turn **Verify SSL certificate** off to connect anyway. The connection stays encrypted, but Home Assistant can't
  tell whether it's really talking to your TrueNAS; see [Privacy and Security](Privacy-and-Security.md#verify-ssl-certificate).

## Setup says the host is invalid

Enter only a hostname or IP address, with `:port` (1–65535) if TrueNAS isn't on 443: `truenas.local`,
`192.168.1.10:8443`, `fd00::10` or `[fd00::10]:8443`. No `https://`, path, `user@` or IPv6 zone (`%eth0`).

## Setup says "Invalid API key"

The key was typed wrong, deleted, or belongs to a user that can't use the API. Make a new one in TrueNAS.

## "Reconfiguration required" appeared later

TrueNAS stopped accepting the key. Open the notice (or ⋮ → **Reconfigure**) and enter a new key.

## Everything is unavailable

TrueNAS is down, rebooting or unreachable. Entities recover on their own at the next poll after it's back
(within a minute).

## One app's entities are unavailable

The app was removed from TrueNAS. Delete its device in Home Assistant (see [Installation](Installation.md)).

## A button or switch does nothing / "another action is still running"

Only one action per app runs at a time. Wait for the first to finish. A very slow job is abandoned after 30 minutes.

## "app.… on <app> failed: …" notification

TrueNAS ran the job and it failed (or the connection dropped while waiting). The text after the colon is TrueNAS's own
error. Check the app in the TrueNAS UI (**Apps**) and its job list.

## Update shows "update available" with no version number

TrueNAS flagged an update without saying which version. The Install button still upgrades to the latest.

## The TrueNAS update entity is unavailable, or the card shows —

The API key isn't allowed to read update status or system information. Those parts are optional; use a key with
more rights if you want them.

If the key is allowed, check the log: when TrueNAS fails one of these for any other reason, the integration logs a
warning naming the call (`update.status`, `webui.main.dashboard.sys_info` or `truenas.is_ix_hardware`) and TrueNAS's
error, once, and logs again when it works.

## Still stuck

[Open an issue](https://github.com/soullink9/HA-Marketplace-TrueNAS-Apps/issues/new/choose) with your versions and the log
lines. Remove your API key and anything private first.