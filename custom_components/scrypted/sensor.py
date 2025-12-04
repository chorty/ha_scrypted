"""Diagnostic sensor for the Scrypted integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ENTRY_RUNTIME, DOMAIN, ScryptedRuntimeData


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scrypted token sensor from config entry."""
    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return

    entry_runtime: dict[str, ScryptedRuntimeData] | None = domain_data.get(
        DATA_ENTRY_RUNTIME
    )
    if not entry_runtime or config_entry.entry_id not in entry_runtime:
        return

    async_add_entities([
        ScryptedTokenSensor(config_entry, entry_runtime[config_entry.entry_id])
    ])


class ScryptedTokenSensor(SensorEntity):
    """Representation of a Scrypted token sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:shield-key"
    _attr_should_poll = False

    def __init__(self, config_entry: ConfigEntry, runtime: ScryptedRuntimeData) -> None:
        """Initialize a ScryptedTokenSensor entity."""
        entry_name = config_entry.data.get(CONF_NAME, DOMAIN.title())
        self._attr_name = f"{entry_name} token"
        self._attr_unique_id = f"{config_entry.entry_id}_token"
        self._attr_native_value = runtime.token
        self._attr_extra_state_attributes = {CONF_HOST: runtime.host}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry_name,
            manufacturer="Scrypted",
        )
