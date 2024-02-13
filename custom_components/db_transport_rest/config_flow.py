"""Config flow for Deutsche Bahn Journey (db.transport.rest) integration."""
from __future__ import annotations

from http import HTTPStatus
import json
import logging
from os import path
from typing import Any

import aiohttp
import jsonschema
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_FROM, CONF_TO, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_HOST,
            default="https://v6.db.transport.rest",
            description="The server to use",
        ): str
    }
)

with open(
    path.join(path.dirname(__file__), "schemas", "location.scheme.json"),
    encoding="utf-8",
) as schema_file:
    locationScheme = json.load(schema_file)


async def validate_host(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    async with aiohttp.ClientSession(data[CONF_HOST]) as session, session.get(
        "/stations"
    ) as response:
        if response.status != HTTPStatus.OK:
            return CannotConnect

        body = json.loads(await response.text())
        jsonschema.validate(
            instance=body,
            schema={
                "type": "object",
                "additionalProperties": locationScheme,
            },
        )

        return body


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deutsche Bahn Journey (db.transport.rest)."""

    VERSION = 1
    MINOR_VERSION = 2
    stations = []
    host = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self.stations = await validate_host(user_input)
                self.host = user_input[CONF_HOST]
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self.async_step_stations()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            src = list(
                filter(
                    lambda s: s["name"] == user_input[CONF_FROM],
                    self.stations.values(),
                )
            )[0]["id"]
            dst = list(
                filter(
                    lambda s: s["name"] == user_input[CONF_TO],
                    self.stations.values(),
                )
            )[0]["id"]
            return self.async_create_entry(
                title=f"{user_input[CONF_FROM]} <> {user_input[CONF_TO]}",
                data={CONF_HOST: self.host, CONF_FROM: src, CONF_TO: dst},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_FROM): vol.In(
                    [val["name"] for val in self.stations.values()]
                ),
                vol.Required(CONF_TO): vol.In(
                    [val["name"] for val in self.stations.values()]
                ),
            }
        )
        return self.async_show_form(
            step_id="stations", data_schema=schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
