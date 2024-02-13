"""Train information for departures and delays, provided by db.transport.rest."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import json

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_FROM, CONF_TO, DOMAIN
from .coordinator import DBDataUpdateCoordinator, JourneyData

ATTR_PRODUCT_FILTER = "product_filter"


@dataclass(frozen=True)
class DBRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[JourneyData], StateType | datetime]


@dataclass(frozen=True)
class DBSensorEntityDescription(SensorEntityDescription, DBRequiredKeysMixin):
    """Describes DB Journey sensor entity."""


SENSOR_TYPES: tuple[DBSensorEntityDescription, ...] = (
    DBSensorEntityDescription(
        key="departure_time",
        translation_key="departure_time",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.departure_time,
    ),
    DBSensorEntityDescription(
        key="travel_time",
        translation_key="travel_time",
        icon="mdi:clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="s",
        value_fn=lambda data: data.travel_time.total_seconds(),
    ),
    DBSensorEntityDescription(
        key="num_legs",
        translation_key="num_legs",
        device_class=SensorDeviceClass.DATA_SIZE,
        value_fn=lambda data: data.num_legs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the DB Journey sensor entry."""

    coordinator: DBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    http_session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    from_station = entry.data[CONF_FROM]
    to_station = entry.data[CONF_TO]

    async with http_session.get(f"{host}/stations/{from_station}") as resp:
        from_name = json.loads(await resp.text())["name"]

    async with http_session.get(f"{host}/stations/{to_station}") as resp:
        to_name = json.loads(await resp.text())["name"]

    async_add_entities(
        [
            JourneySensor(
                coordinator,
                f"{from_name} => {to_name}",
                entry.entry_id,
                description,
                index=index,
            )
            for description in SENSOR_TYPES
            for index in (0, 1, 2)
        ]
    )


class JourneySensor(CoordinatorEntity[DBDataUpdateCoordinator], SensorEntity):
    """Contains data about a journey."""

    entity_description: DBSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DBDataUpdateCoordinator,
        name: str,
        entry_id: str,
        entity_description: DBSensorEntityDescription,
        index: int = 0,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        if index > 0:
            entry_id = f"{entry_id}-{index}"
            name = f"{name}+{index}"

        self._index = index
        self._attr_unique_id = f"{entry_id}-{entity_description.key}"
        self.entity_description = entity_description
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            name=name,
            configuration_url="https://v6.db.transport.rest/",
        )
        self._update_attr()

    @callback
    def _update_attr(self) -> None:
        """Update _attr."""
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data[self._index]
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_attr()
        return super()._handle_coordinator_update()
