import asyncio
from typing import Generic, TypeVar

T = TypeVar("T")


class ConfigEntry(Generic[T]):
    def __init__(self, entry_id="E1", data=None):
        self.entry_id, self.data = entry_id, data or {}
        self._unload, self.bg, self.bg_errors = [], [], []

    def async_on_unload(self, cb):
        self._unload.append(cb)

    def async_create_background_task(self, hass, coro, name):
        t = asyncio.get_running_loop().create_task(coro, name=name)
        self.bg.append(t)

        def done(t):
            if not t.cancelled() and t.exception() is not None:
                self.bg_errors.append(type(t.exception()).__name__)

        t.add_done_callback(done)
        return t


ConfigFlowResult = dict


class ConfigFlow:
    def __init_subclass__(cls, domain=None, **kw):
        cls.domain = domain

    # Just enough of the flow API for the config-flow test: results are plain dicts.
    def _async_abort_entries_match(self, match):
        pass

    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}

    def async_update_reload_and_abort(self, entry, data_updates):
        entry.data = {**entry.data, **data_updates}
        return {"type": "abort", "reason": "reconfigure_successful"}

    def add_suggested_values_to_schema(self, schema, suggested):
        return (schema, suggested)

    def async_show_form(self, step_id, data_schema, errors):
        return {"type": "form", "step_id": step_id, "suggested": data_schema[1], "errors": errors}

    def _get_reconfigure_entry(self):
        return self.entry

    _get_reauth_entry = _get_reconfigure_entry
