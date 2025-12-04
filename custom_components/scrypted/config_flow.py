"""Config flow for Scrypted integration."""
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientConnectorError, ClientError
import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_HOST,
    CONF_ICON,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .const import CONF_SCRYPTED_NVR, DOMAIN
from .http import retrieve_token


def text_selector(type: selector.TextSelectorType) -> selector.TextSelector:
    """Create a text selector."""
    return selector.TextSelector(selector.TextSelectorConfig(type=type))


def _get_config_schema(default: dict[str, Any] | None) -> vol.Schema:
    """Get config schema."""
    if not default:
        default = {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=default.get(CONF_NAME, DOMAIN.title())
            ): text_selector(type=selector.TextSelectorType.TEXT),
            vol.Required(
                CONF_ICON, default=default.get(CONF_ICON, "mdi:memory")
            ): selector.IconSelector(selector.IconSelectorConfig()),
            vol.Required(CONF_HOST, default=default.get(CONF_HOST)): text_selector(
                type=selector.TextSelectorType.TEXT
            ),
            vol.Required(
                CONF_USERNAME, default=default.get(CONF_USERNAME)
            ): text_selector(type=selector.TextSelectorType.TEXT),
            vol.Required(
                CONF_PASSWORD, default=default.get(CONF_PASSWORD)
            ): text_selector(type=selector.TextSelectorType.PASSWORD),
            vol.Optional(
                CONF_SCRYPTED_NVR,
                default=default.get(CONF_SCRYPTED_NVR, False),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
        }
    )


class ScryptedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Scrypted config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self.data = {}

    async def validate_input(self, data: dict[str, Any]) -> None:
        """Validate that the host is valid."""
        session = async_get_clientsession(self.hass, verify_ssl=False)
        try:
            await retrieve_token(data, session)
        except ValueError as err:
            raise InvalidAuth from err
        except ClientConnectorError as err:
            raise CannotConnect from err
        except ClientError as err:
            raise CannotConnect from err
        except asyncio.TimeoutError as err:
            raise CannotConnect from err

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle user flow."""
        errors = {}
        if user_input is not None and CONF_USERNAME in user_input:
            try:
                await self.validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(slugify(user_input[CONF_HOST]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_config_schema(user_input),
            errors=errors,
        )

    async_step_import = async_step_user

    async def async_step_reauth(
        self, _: dict[str, Any] | None
    ) -> config_entries.FlowResult:
        """Handle reauth flow."""
        if CONF_PASSWORD not in self.context["data"]:
            return await self.async_step_upgrade()
        return await self.async_step_credentials()

    async def _async_step_reauth(
        self, step_id: str, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle reauth step."""
        errors = {}
        if user_input is not None:
            try:
                await self.validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
            else:
                unique_id = slugify(user_input[CONF_HOST])
                config_entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                assert config_entry
                if not any(
                    entry
                    for entry in self.hass.config_entries.async_entries(DOMAIN)
                    if entry != config_entry and entry.unique_id == unique_id
                ):
                    self.hass.config_entries.async_update_entry(
                        config_entry, data=user_input, options={}, unique_id=unique_id
                    )
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(config_entry.entry_id)
                    )
                    return self.async_abort(reason="success")

                errors[CONF_NAME] = "already_configured"

        return self.async_show_form(
            step_id=step_id,
            data_schema=_get_config_schema(user_input or self.context.get("data")),
            errors=errors,
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle credentials step."""
        return await self._async_step_reauth("credentials", user_input)

    async def async_step_upgrade(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle upgrade step."""
        return await self._async_step_reauth("upgrade", user_input)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
