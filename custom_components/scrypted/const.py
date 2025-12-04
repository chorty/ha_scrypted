"""Constants for the Scrypted integration."""

from dataclasses import dataclass

DOMAIN = "scrypted"
CONF_SCRYPTED_NVR = "scrypted_nvr"
CONF_AUTO_REGISTER_RESOURCES = "auto_register_resources"

DATA_ENTRY_RUNTIME = "entry_runtime"
DATA_TOKEN_LOOKUP = "token_lookup"
PANEL_RESOURCE_VERSION = "1.0.0"


@dataclass(slots=True)
class ScryptedRuntimeData:
	"""Runtime data stored per config entry."""

	token: str
	host: str
	panel_id: str
	use_nvr_sidebar: bool
