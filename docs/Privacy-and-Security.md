# Privacy and Security

## What leaves your Home Assistant

Nothing goes to the internet. The integration connects only to the TrueNAS host you entered, over an encrypted
websocket (`wss://`). There's no analytics, update check or third-party service.

## The API key

- It's stored in Home Assistant's own configuration storage, like any integration's credentials.
- It is sent only to your TrueNAS, once per connection, to log in.
- It's never written to the log by this integration. Check logs and screenshots for it anyway before sharing them.
- The Reconfigure form never sends the saved key back to your browser: the field starts empty, and leaving it empty
  keeps the saved key.
- Delete the key in TrueNAS if you stop using the integration, and use a key from an account you're happy to give this access.

## Verify SSL certificate

It's **on** by default. With it on, Home Assistant only sends the API key to a server that proves, with a certificate
Home Assistant trusts, that it's the TrueNAS you entered.

TrueNAS ships with a self-signed certificate, which fails that check, so setup tells you the certificate couldn't be
verified. The secure fix is a trusted certificate on TrueNAS (for example from Let's Encrypt), with the name on it as
the host. You can instead turn verification off: the connection is still encrypted, but Home Assistant can't tell
whether the server is really your TrueNAS, so a device on the network path that pretends to be TrueNAS could capture
the API key and use it to control your apps. While it's off, Home Assistant logs a warning each time the integration
starts.

Entries set up before 1.4.0 keep the setting they were saved with (off, unless you changed it): turn it on with
Reconfigure once TrueNAS has a trusted certificate.

## What the integration can do to your TrueNAS

With a key that can change apps, it can start, stop, restart, redeploy and upgrade your apps, and nothing else.
It deliberately **cannot** install a TrueNAS system update, change storage, delete data or touch containers directly.
Anyone who can use buttons and switches in your Home Assistant can use those controls, so think about who has
access to them (for example, hide them from dashboards shared with guests).

## Hardening already in the code

- The host field accepts only a valid hostname, IPv4 or IPv6 address and an optional port from 1 to 65535 (each part
  checked separately), so the connection URL can't be redirected somewhere else. The scheme (`wss://`) and path are
  fixed, and the integration doesn't follow redirects.
- Only a permission refusal from TrueNAS is treated as "this API key may not read that"; any other error on those
  optional calls is logged as a warning, so a fault isn't mistaken for a restricted key.
- When waiting for an app job, only the record of that exact job counts.
- Error text from TrueNAS is stripped of control characters and shortened before it's shown in a notification.
- The CI workflows pin third-party actions that have no maintained release (`hacs/action`, hassfest) to a commit.
- Every network operation has a time limit, so a hung server can't freeze Home Assistant.
- A rejected API key stops polling instead of retrying forever.