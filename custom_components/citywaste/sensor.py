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
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    hass.data[DOMAIN]["listener"] = []

    tag_id = config_entry.data.get(CONF_TAG_ID)
    dong = config_entry.data.get(CONF_DONG)
    ho = config_entry.data.get(CONF_HO)
    price = config_entry.data.get(CONF_PRICE)
    refresh_period = config_entry.data.get(CONF_REFRESH_PERIOD)

    if config_entry.options.get(CONF_TAG_ID) != None:
        tag_id = config_entry.options.get(CONF_TAG_ID)
        dong = config_entry.options.get(CONF_DONG)
        ho = config_entry.options.get(CONF_HO)
        price = config_entry.options.get(CONF_PRICE)
        refresh_period = config_entry.options.get(CONF_REFRESH_PERIOD)

    device = Device(hass, NAME, async_add_devices, tag_id, dong, ho, price, refresh_period)

class Device:
    """Dummy roller (device for HA) for Hello World example."""

    def __init__(self, hass, name, add_entities, tag_id, dong, ho, price, refresh_period):
        """Init dummy roller."""
        self._id = name
        self.name = name
        self._tag_id = tag_id
        self._dong = dong
        self._ho = ho
        self._price = price
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.

        # Some static information about this device
        self.firmware_version = VERSION
        self.model = NAME
        self.manufacturer = NAME
        self._refresh_period = refresh_period
        self.entities = {}
        self._available = False

        new_devices = []

        for stype in SENSOR_TYPES:
            sensor = CityWasteSensor(hass, self, stype)
            self.entities[stype] = sensor
            new_devices.append(sensor)
            
        add_entities(new_devices)
        self._loop = asyncio.get_event_loop()
        Timer(1, self.refreshTimer).start()

    def refreshTimer(self):
        self._loop.create_task(self.get_price())
        Timer(self._refresh_period*60, self.refreshTimer).start()
        
    async def get_price(self):
        """Get the latest data from the City waste."""
        totalkg = 0
        lastkg = 0
        totalPageCount = 1
        lastdt=""
        totalCount = 0

        now = datetime.datetime.now()
        firstDate = now.strftime("%Y%m01")
        nowDate = now.strftime("%Y%m%d")
        pageIndex = 1
        
        self._available = True

        try:
            while pageIndex <= totalPageCount:
                _LOGGER.debug(
                    f"page index - {pageIndex}, totalCount - {totalPageCount}")
                async with aiohttp.ClientSession(headers=headers) as session:
                    _LOGGER.debug("url : " + CONF_URL)

                    params = {
                        'tagprintcd': self._tag_id,
                        'aptdong': self._dong,
                        'apthono': self._ho,
                        'startchdate': firstDate,
                        'endchdate': nowDate,
                        'pageIndex': pageIndex
                    }
                    async with session.get(CONF_URL, params=params, headers=headers) as response:
                        raw_data = await response.read()
                        if response.status == 200:
                            data = json.loads(raw_data)
                            totalPageCount = data['paginationInfo']['totalPageCount']

                            totalCount = data['paginationInfo']['totalRecordCount']
                            for item in data["list"]:
                                _LOGGER.debug(f"item - {item}")
                                totalkg += item['qtyvalue'];

                                # 최근 배출량
                                if lastkg == 0:
                                    lastkg = item['qtyvalue']
                                    lastdt = item['dttime']
                pageIndex = pageIndex + 1

        except Exception as e:
            _LOGGER.error(f"get price error - {e}")
            self._available = False

        finally:
            _LOGGER.debug("call next timer")
            #Timer(self._refresh_period*60, self._loop.create_task(self.get_price())).start()
            self.entities[STYPE_TOTAL_COUNT]._value = totalCount
            self.entities[STYPE_LAST_KG]._value = lastkg
            self.entities[STYPE_LAST_KG]._extra_state_attributes["datetime"] = lastdt
            self.entities[STYPE_TOTAL_KG]._value = totalkg
            self.entities[STYPE_TOTAL_PRICE]._value = int(totalkg * self._price / 10 * 10)
            self.entities[STYPE_TOTAL_PRICE]._extra_state_attributes["price per kg"] = self._price
            self.publish_updates()

    @property
    def device_id(self):
        """Return ID for roller."""
        return self._id

    def register_callback(self, callback):
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.


class SensorBase(SensorEntity):
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


class CityWasteSensor(SensorBase):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, device, sensor_type):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(DOMAIN, sensor_type), hass=hass)
        self._name = "{}".format(SENSOR_TYPES[sensor_type][0])
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._icon = SENSOR_TYPES[sensor_type][2]
        self._state = None
        self._extra_state_attributes = {}
        self._value = 0

        # self._device_class = SENSOR_TYPES[sensor_type][0]
        self._unique_id = self.entity_id
        self._device = device

    """Sensor Properties"""
    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def icon(self):
        return self._icon

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id

    def update(self):
        """Update the state."""
