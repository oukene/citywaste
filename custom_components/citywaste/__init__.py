"""The Detailed Hello World Push integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import *

from .device import Device

from homeassistant.helpers.device_registry import (
    async_get_registry,
    async_entries_for_config_entry
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS = ["sensor", "button"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hello World component."""
    # Ensure our name space for storing objects is a known type. A dict is
    # common/preferred as it allows a separate instance of your class for each
    # instance that has been created in the UI.
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hello World from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    _LOGGER.debug("call async_setup_entry")
    hass.data[DOMAIN][entry.entry_id] = DOMAIN

    entry.async_on_unload(entry.add_update_listener(update_listener))

    tag_id = entry.data.get(CONF_TAG_ID)
    dong = entry.data.get(CONF_DONG)
    ho = entry.data.get(CONF_HO)
    price = entry.data.get(CONF_PRICE)
    refresh_period = entry.data.get(CONF_REFRESH_PERIOD)

    if entry.options.get(CONF_TAG_ID) != None:
        tag_id = entry.options.get(CONF_TAG_ID)
        dong = entry.options.get(CONF_DONG)
        ho = entry.options.get(CONF_HO)
        price = entry.options.get(CONF_PRICE)
        refresh_period = entry.options.get(CONF_REFRESH_PERIOD)

    device = Device(hass, NAME, tag_id,
                    dong, ho, price, refresh_period)

    hass.data[DOMAIN]["device"] = device

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    for component in PLATFORMS:
        _LOGGER.debug("async create component : " + component)
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def update_listener(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    _LOGGER.debug("call async_unload_entry")

    for listener in hass.data[DOMAIN]["listener"]:
        listener()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(
                    entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
