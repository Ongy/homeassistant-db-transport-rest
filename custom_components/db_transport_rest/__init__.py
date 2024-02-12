"""The trafikverket_train component."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SOURCE, CONF_TARGET
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import DBDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trafikverket Train from a config entry."""
    from_station = entry.data[CONF_SOURCE]
    to_station = entry.data[CONF_TARGET]

    #    try:
    #        to_station = await train_api.async_get_train_station(entry.data[CONF_TO])
    #        from_station = await train_api.async_get_train_station(entry.data[CONF_FROM])
    #    except InvalidAuthentication as error:
    #        raise ConfigEntryAuthFailed from error
    #    except (NoTrainStationFound, MultipleTrainStationsFound) as error:
    #        raise ConfigEntryNotReady(
    #            f"Problem when trying station {entry.data[CONF_FROM]} to"
    #            f" {entry.data[CONF_TO]}. Error: {error} "
    #        ) from error

    coordinator = DBDataUpdateCoordinator(hass, entry, to_station, from_station)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Trafikverket Weatherstation config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
