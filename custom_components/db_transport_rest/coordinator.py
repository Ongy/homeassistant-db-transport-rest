"""DataUpdateCoordinator for the DB Journey (db.transport.rest) integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
TIME_BETWEEN_UPDATES = timedelta(minutes=5)


@dataclass
class JourneyData:
    """Dataclass for DB journey data."""

    departure_time: datetime | None
    travel_time: timedelta | None
    num_legs: int | None


def _journey_data_from_journey(journey) -> JourneyData:
    legs = journey["legs"]
    first = legs[0]
    last = legs[-1]

    departure = datetime.fromisoformat(first["departure"])
    arrival = datetime.fromisoformat(last["arrival"])

    return JourneyData(
        departure_time=departure,
        travel_time=arrival - departure,
        num_legs=len(legs),
    )


class DBDataUpdateCoordinator(DataUpdateCoordinator[list[JourneyData]]):
    """A DB Journey Data Update Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        to_station: str,
        from_station: str,
    ) -> None:
        """Initialize the DB Journey coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=TIME_BETWEEN_UPDATES,
        )
        self._session = async_get_clientsession(hass)
        self.host = entry.data[CONF_HOST]
        self.from_station: str = from_station
        self.to_station: str = to_station

    async def _async_update_data(self) -> list[JourneyData]:
        """Fetch data from db.transport.rest."""
        async with self._session.get(
            f"{self.host}/journeys",
            params={
                "from": self.from_station,
                "to": self.to_station,
                "nationalExpress": "false",
                "national": "true",
            },
        ) as resp:
            val = json.loads(await resp.text())

            return [_journey_data_from_journey(journey) for journey in val["journeys"]]
