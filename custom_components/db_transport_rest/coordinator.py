"""DataUpdateCoordinator for the Trafikverket Train integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
TIME_BETWEEN_UPDATES = timedelta(minutes=5)


@dataclass
class TrainData:
    """Dataclass for Trafikverket Train data."""

    departure_time: datetime | None
    travel_time: timedelta | None
    num_legs: int | None


#    departure_state: str
#    cancelled: bool
#    delayed_time: int | None
#    planned_time: datetime | None
#    estimated_time: datetime | None
#    actual_time: datetime | None
#    other_info: str | None
#    deviation: str | None
#    product_filter: str | None
#    departure_time_next: datetime | None
#    departure_time_next_next: datetime | None


class DBDataUpdateCoordinator(DataUpdateCoordinator[TrainData]):
    """A Trafikverket Data Update Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        to_station: str,
        from_station: str,
    ) -> None:
        """Initialize the Trafikverket coordinator."""
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

    async def _async_update_data(self) -> TrainData:
        """Fetch data from Trafikverket."""
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

            journey = val["journeys"][0]
            legs = journey["legs"]
            first = legs[0]
            last = legs[-1]

            departure = datetime.fromisoformat(first["departure"])
            arrival = datetime.fromisoformat(last["arrival"])

            return TrainData(
                departure_time=departure,
                travel_time=arrival - departure,
                num_legs=len(legs),
                #                delayed_time=delay_time.seconds if delay_time else None,
                #                planned_time=_get_as_utc(state.advertised_time_at_location),
                #                estimated_time=_get_as_utc(state.estimated_time_at_location),
                #                actual_time=_get_as_utc(state.time_at_location),
                #                other_info=_get_as_joined(state.other_information),
                #                deviation=_get_as_joined(state.deviations),
                #                product_filter=self._filter_product,
                #                departure_time_next=_get_as_utc(depart_next),
                #                departure_time_next_next=_get_as_utc(depart_next_next),
            )
