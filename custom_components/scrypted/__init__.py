"""The Scrypted integration."""
from __future__ import annotations

import asyncio

from aiohttp import ClientConnectorError
from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.persistent_notification import async_create
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_ICON, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_SCRYPTED_NVR,
    DATA_ENTRY_RUNTIME,
    DATA_TOKEN_LOOKUP,
    DOMAIN,
    PANEL_RESOURCE_VERSION,
    ScryptedRuntimeData,
)
from .http import ScryptedView, retrieve_token


PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Auth setup."""
    session = async_get_clientsession(hass, verify_ssl=False)
    hass.http.register_view(ScryptedView(hass, session))

    if DOMAIN in config:
        async_create(
            hass,
            (
                "Your Scrypted configuration has been imported as a config entry and "
                "can safely be removed from your configuration.yaml."
            ),
            "Scrypted Config Import",
        )
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
        return False
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a Scrypted config entry."""
    if not config_entry.data:
        raise ConfigEntryAuthFailed("Missing configuration data")

    session = async_get_clientsession(hass, verify_ssl=False)
    try:
        token = await retrieve_token(config_entry.data, session)
    except ValueError as err:
        raise ConfigEntryAuthFailed("Invalid Scrypted credentials") from err
    except (ClientConnectorError, asyncio.TimeoutError) as err:
        raise ConfigEntryNotReady("Unable to reach the Scrypted host") from err

    domain_data = hass.data.setdefault(DOMAIN, {})
    entry_runtime: dict[str, ScryptedRuntimeData] = domain_data.setdefault(
        DATA_ENTRY_RUNTIME, {}
    )
    token_lookup: dict[str, str] = domain_data.setdefault(DATA_TOKEN_LOOKUP, {})

    if stored_runtime := entry_runtime.get(config_entry.entry_id):
        token_lookup.pop(stored_runtime.token, None)

    panel_id = f"{DOMAIN}_{config_entry.entry_id}"
    panel_config = {
        "_panel_custom": {
            "name": "ha-panel-scrypted",
            "trust_external": False,
            "module_url": f"/api/{DOMAIN}/{token}/entrypoint.js",
        },
        "version": PANEL_RESOURCE_VERSION,
    }

    async_register_built_in_panel(
        hass,
        "custom",
        config_entry.data.get(CONF_NAME, DOMAIN.title()),
        config_entry.data.get(CONF_ICON),
        panel_id,
        panel_config,
        require_admin=False,
    )

    runtime_data = ScryptedRuntimeData(
        token=token,
        host=config_entry.data[CONF_HOST],
        panel_id=panel_id,
        use_nvr_sidebar=config_entry.data.get(CONF_SCRYPTED_NVR, False),
    )
    entry_runtime[config_entry.entry_id] = runtime_data
    token_lookup[token] = config_entry.entry_id

    try:
        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    except Exception:
        await async_unload_entry(hass, config_entry)
        raise

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    domain_data = hass.data.get(DOMAIN)
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if not domain_data:
        return unload_ok

    entry_runtime: dict[str, ScryptedRuntimeData] = domain_data.get(
        DATA_ENTRY_RUNTIME, {}
    )
    token_lookup: dict[str, str] = domain_data.get(DATA_TOKEN_LOOKUP, {})

    runtime_data = entry_runtime.pop(config_entry.entry_id, None)
    if runtime_data:
        token_lookup.pop(runtime_data.token, None)
        async_remove_panel(hass, runtime_data.panel_id)

    if not entry_runtime:
        hass.data.pop(DOMAIN)

    return unload_ok
