"""Constants for the Scrypted integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "scrypted"
CONF_SCRYPTED_NVR = "scrypted_nvr"

DATA_ENTRY_RUNTIME = "entries"
DATA_TOKEN_LOOKUP = "token_lookup"
PANEL_RESOURCE_VERSION = "1.0.0"


@dataclass(slots=True)
class ScryptedRuntimeData:
	"""Runtime data stored for each config entry."""

	token: str
	host: str
	panel_id: str
	use_nvr_sidebar: bool

