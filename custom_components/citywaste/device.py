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

from .sensor import CityWasteSensor

from homeassistant.helpers.entity import Entity
from pkg_resources import get_provider

from .const import *
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change, track_state_change

_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"


class Device:
    """Dummy roller (device for HA) for Hello World example."""

    def __init__(self, hass, name, tag_id, dong, ho, price, refresh_period):
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
        lastdt = firstDate
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
                            if data["list"] != None:
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
