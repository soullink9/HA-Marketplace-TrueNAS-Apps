from dataclasses import dataclass, field


@dataclass(kw_only=True)
class DeviceInfo:  # a dataclass since 2026.11 (no longer a dict); unknown fields raise TypeError
    identifiers: set = field(default_factory=set)
    name: str | None = None
    manufacturer: str | None = None


class DeviceEntry:
    def __init__(self, identifiers):
        self.identifiers = identifiers
