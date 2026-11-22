"""Talking to TrueNAS: a short-lived JSON-RPC 2.0 websocket connection.

TrueNAS exposes its API at wss://<host>/api/current. We open a connection, log in
with the API key, ask what we need, and close it again. Nothing stays connected
between polls, so a TrueNAS reboot or network drop can never leave us half-open.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
import errno
import logging
from typing import Any
import unicodedata

from aiohttp import ClientError
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CALL_TIMEOUT, POLL_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# call("app.query", [args]) -> the "result" of the reply
Call = Callable[..., Awaitable[Any]]


class TrueNASError(RuntimeError):
    """TrueNAS answered a request with an error.

    ``errname`` is TrueNAS's error name (``"EACCES"`` when the API key lacks the role for a
    method), or None when the reply didn't give one.
    """

    def __init__(self, message: str, errname: str | None = None) -> None:
        """Keep the error name next to the message."""
        super().__init__(message)
        self.errname = errname

    @classmethod
    def from_reply(cls, error: Any) -> TrueNASError:
        """Build one from a JSON-RPC ``error`` object, which TrueNAS controls, so trust nothing about its shape.

        TrueNAS puts the useful text in ``data.reason`` ("Not authorized") and the bare ``message`` is
        generic ("Method call error"), so prefer the reason.
        """
        error = error if isinstance(error, dict) else {}
        data = error.get("data") if isinstance(error.get("data"), dict) else {}
        message = data.get("reason") or error.get("message") or "RPC error"
        errname = data.get("errname")
        if errname is None and data.get("error") == errno.EACCES:
            errname = "EACCES"
        return cls(str(message), errname if isinstance(errname, str) else None)


@asynccontextmanager
async def connect(hass: HomeAssistant, data: dict) -> AsyncIterator[Call]:
    """Open the websocket, log in, and yield a ``call(method, params)`` coroutine.

    Raises PermissionError for a rejected API key, aiohttp.ClientError for network
    trouble (aiohttp.ClientConnectorCertificateError when certificate verification
    is on and fails), and TrueNASError (a RuntimeError) when TrueNAS answers a request
    with an error.
    """
    session = async_get_clientsession(hass, data[CONF_VERIFY_SSL])
    async with session.ws_connect(f"wss://{data[CONF_HOST]}/api/current") as ws:
        msg_id = 0

        async def call(method: str, params: list | None = None) -> Any:
            """Send one request and return its result."""
            nonlocal msg_id
            msg_id += 1
            await ws.send_json({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or []})
            while True:
                try:
                    reply = await ws.receive_json(timeout=CALL_TIMEOUT)
                except (TypeError, ValueError) as err:  # socket closed, or a frame that isn't JSON
                    raise ClientError(f"{method}: connection closed or bad frame") from err
                # TrueNAS may also push notifications; only the reply with our id is the answer.
                if isinstance(reply, dict) and reply.get("id") == msg_id:
                    break
            if "error" in reply:
                raise TrueNASError.from_reply(reply["error"])
            return reply.get("result")

        if await call("auth.login_with_api_key", [data[CONF_API_KEY]]) is not True:
            raise PermissionError("Invalid API key")
        yield call


async def optional(call: Call, method: str) -> Any:
    """Call a nice-to-have method without letting it fail the poll; returns None when it can't be read.

    A permission refusal (EACCES: the API key lacks the role) is expected and stays quiet. Any
    other error is a real fault, such as an outage or an API change, so it is logged as a warning
    (once, until the method works again) instead of passing for a restricted key. The matching
    entities show as unavailable either way, while the apps keep working.
    """
    try:
        result = await call(method)
    except TrueNASError as err:
        if err.errname != "EACCES" and method not in _failing:
            _failing.add(method)
            _LOGGER.warning("TrueNAS %s failed (not a permission problem): %s", method, clean_text(str(err)))
        return None
    if method in _failing:
        _failing.discard(method)
        _LOGGER.info("TrueNAS %s works again", method)
    return result


# Optional methods that last failed with something other than a permission refusal.
_failing: set[str] = set()


def clean_text(text: str, limit: int = 500) -> str:
    """Make text from TrueNAS safe to show: control characters become spaces, and it's capped at ``limit``."""
    text = "".join(" " if unicodedata.category(c) in ("Cc", "Cf") else c for c in text)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


async def rpc(hass: HomeAssistant, data: dict, method: str, params: list | None = None) -> Any:
    """Connect, make one call, disconnect. Used by the setup form to test credentials."""
    async with asyncio.timeout(POLL_TIMEOUT), connect(hass, data) as call:
        return await call(method, params)
