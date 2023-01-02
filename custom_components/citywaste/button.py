"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import logging
from threading import Timer
from xmlrpc.client import boolean
import aiohttp
from typing import Optional

import json
import asyncio
import datetime
import math

from homeassistant.helpers.entity import Entity
from pkg_resources import get_provider

from .const import *
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change, track_state_change
from homeassistant.components.button import ButtonEntity


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    device = hass.data[DOMAIN]["device"]

    new_devices = []

    button = CityWasteButton(hass, device)
    new_devices.append(button)

    async_add_devices(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.


class ButtonBase(ButtonEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device
    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._device.device_id,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._device._available

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class CityWasteButton(ButtonBase):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, device):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(DOMAIN, "refresh"), hass=hass)
        self._name = "{}".format("refresh")
        self._state = None
        self._extra_state_attributes = {}
        self._value = 0

        # self._device_class = SENSOR_TYPES[sensor_type][0]
        self._unique_id = self.entity_id
        self._device = device

    def press(self):
        self._device._loop.create_task(self._device.get_price())

    """Sensor Properties"""
    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_state_attributes

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id

    def update(self):
        """Update the state."""


