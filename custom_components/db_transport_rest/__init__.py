"""The db_transport_rest component."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SOURCE, CONF_TARGET
from homeassistant.core import HomeAssistant

from .const import CONF_FROM, CONF_TO, DOMAIN, PLATFORMS
from .coordinator import DBDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DB Journey from a config entry."""
    from_station = entry.data[CONF_FROM]
    to_station = entry.data[CONF_TO]

    coordinator = DBDataUpdateCoordinator(hass, entry, to_station, from_station)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload db_transport_rest Journey config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


# Example migration function
async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    if config_entry.version > 1:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        new = {**config_entry.data}
        if config_entry.minor_version < 2:
            new[CONF_TO] = config_entry.data[CONF_TARGET]
            new[CONF_FROM] = config_entry.data[CONF_SOURCE]

        hass.config_entries.async_update_entry(
            config_entry, data=new, minor_version=2, version=1
        )

    return True
