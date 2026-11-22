"""The setup form: first-time setup, reconfigure, and re-authentication share one form."""

import ipaddress
import re
from typing import Any

from aiohttp import ClientConnectorCertificateError, ClientError
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
import probatio as pb

from .api import rpc
from .const import DOMAIN

_KEY = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
# Probatio is Home Assistant's validation library (it replaced voluptuous in 2026.9), so it needs no requirement.
# The host is checked properly by valid_host() when the form is submitted, so it can say what's wrong.
SCHEMA = pb.Schema(
    {
        pb.Required(CONF_HOST): pb.All(str, pb.Strip),
        pb.Required(CONF_API_KEY): _KEY,
        # On by default: with it off, anyone on the network path could pose as TrueNAS and capture the API key.
        # TrueNAS ships a self-signed certificate, so the form explains how to turn it off if that's what fails.
        pb.Required(CONF_VERIFY_SSL, default=True): bool,
    }
)
# Reconfigure: a blank API key keeps the saved one, so the key is never sent back to the browser to pre-fill.
RECONFIGURE_SCHEMA = pb.Schema(
    {
        pb.Required(CONF_HOST): pb.All(str, pb.Strip),
        pb.Optional(CONF_API_KEY): _KEY,
        pb.Required(CONF_VERIFY_SSL, default=True): bool,
    }
)

_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")


def valid_host(value: str) -> str | None:
    """Return the host in the form the websocket URL needs, or None if it isn't one.

    Accepts a DNS name, an IPv4 address or an IPv6 address (bare, or in brackets), each with an
    optional :port from 1 to 65535. Anything else (a scheme, path, "user@", "%zone", empty or
    over-long labels, a bad port) is refused, so the URL built from it can only point at that host.
    """
    value = value.strip()
    port = ""
    if value.startswith("["):  # [IPv6] or [IPv6]:port
        host, sep, rest = value[1:].partition("]")
        if not sep or (rest and not rest.startswith(":")):
            return None
        port = rest[1:] if rest else ""
        if rest == ":":
            return None
    elif value.count(":") > 1:  # bare IPv6, which can't carry a port without brackets
        host = value
    else:
        host, sep, port = value.partition(":")
        if sep and not port:
            return None
    if port and not (port.isascii() and port.isdigit() and 1 <= int(port) <= 65535):
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if "%" in host:  # an IPv6 zone ("fe80::1%eth0") can't go in a URL as typed
            return None
        host = f"[{address.compressed}]" if address.version == 6 else address.compressed
    elif value.startswith("[") or value.count(":") > 1:
        return None  # brackets or several colons, but not an IPv6 address
    elif len(host) > 253 or not all(_LABEL.fullmatch(label) for label in host.split(".")):
        return None
    elif host.replace(".", "").isdigit():
        return None  # all digits but not a valid IPv4 address, e.g. 999.1.1.1
    return f"{host}:{port}" if port else host


class TrueNASConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for host, API key and SSL choice, and check that they work before saving."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """First-time setup (Settings > Devices & services > Add integration)."""
        return await self._async_form("user", user_input)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change host, API key or SSL verification of an existing entry."""
        return await self._async_form("reconfigure", user_input, self._get_reconfigure_entry())

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Home Assistant starts this when TrueNAS rejects the stored API key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the new key."""
        return await self._async_form("reauth_confirm", user_input, self._get_reauth_entry())

    async def _async_form(
        self, step_id: str, user_input: dict[str, Any] | None, entry: ConfigEntry | None = None
    ) -> ConfigFlowResult:
        """Show the form; when submitted, test the login and then create or update the entry."""
        errors = {}
        schema = RECONFIGURE_SCHEMA if step_id == "reconfigure" else SCHEMA
        if user_input:
            data = {
                CONF_HOST: valid_host(user_input[CONF_HOST]),
                # Reconfigure with the key left blank: keep the saved one.
                CONF_API_KEY: user_input.get(CONF_API_KEY) or (entry.data[CONF_API_KEY] if entry else ""),
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
            }
            if data[CONF_HOST] is None:
                errors[CONF_HOST] = "invalid_host"
            elif not data[CONF_API_KEY]:
                errors[CONF_API_KEY] = "invalid_auth"
            else:
                if entry is None:  # new setup: refuse a TrueNAS that is already added
                    self._async_abort_entries_match({CONF_HOST: data[CONF_HOST]})
                try:
                    await rpc(self.hass, data, "app.query")  # needs a key allowed to read apps
                except PermissionError:
                    errors["base"] = "invalid_auth"
                except ClientConnectorCertificateError:  # verification on, and TrueNAS's certificate isn't trusted
                    errors["base"] = "cert_failed"
                except ClientError, TimeoutError, RuntimeError:
                    errors["base"] = "cannot_connect"
                else:
                    if entry:
                        return self.async_update_reload_and_abort(entry, data_updates=data)
                    return self.async_create_entry(title=data[CONF_HOST], data=data)
        # Pre-fill with what was just typed, or with the saved settings when editing, but never the API key.
        shown = {k: v for k, v in (user_input or (entry.data if entry else {})).items() if k != CONF_API_KEY}
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(schema, shown or None),
            errors=errors,
        )
