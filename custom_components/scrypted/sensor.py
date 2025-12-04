"""Representation of Z-Wave sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
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

    runtime_store: dict[str, ScryptedRuntimeData] | None = domain_data.get(
        DATA_ENTRY_RUNTIME
    )
    if not runtime_store or config_entry.entry_id not in runtime_store:
        return

    async_add_entities(
        [ScryptedTokenSensor(config_entry, runtime_store[config_entry.entry_id])]
    )


class ScryptedTokenSensor(SensorEntity):
    """Representation of a Scrypted token sensor."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        runtime: ScryptedRuntimeData,
    ) -> None:
        """Initialize a ScryptedTokenSensor entity."""
        self._attr_name = f"{DOMAIN.title()} token: {config_entry.data[CONF_HOST]}"
        self._attr_unique_id = config_entry.data[CONF_HOST]
        self._attr_native_value = runtime.token
        self._attr_icon = "mdi:shield-key"
        self._attr_should_poll = False
        self._attr_extra_state_attributes = {CONF_HOST: runtime.host}
