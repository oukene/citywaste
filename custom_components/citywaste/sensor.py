"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import logging
from threading import Timer
import asyncio

from .const import *
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import async_generate_entity_id

_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    device = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []

    for stype in SENSOR_TYPES:
        sensor = CityWasteSensor(hass, device, stype)
        device.entities[stype] = sensor
        new_devices.append(sensor)

    async_add_devices(new_devices)

    device._loop = asyncio.get_event_loop()
    Timer(1, device.refreshTimer).start()


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
    """Representation of a CityWaste Sensor."""

    def __init__(self, hass, device, sensor_type):
        """Initialize the sensor."""
        super().__init__(device)
        self.hass = hass
        self._device = device

        # 1. 이름은 한글("총 배출량" 등)로 예쁘게 UI에 표시되도록 둡니다.
        self._attr_name = f"{SENSOR_TYPES[sensor_type][0]}"
        
        # 2. HA가 한글 발음(cong_baeculryang)으로 ID를 자동 생성하지 못하도록, 
        #    내부 영문 키값(sensor_type, 예: total_kg)을 사용해 ID를 강제 지정합니다.
        self.entity_id = async_generate_entity_id(
            "sensor" + ".{}", f"{DOMAIN}_{sensor_type}", hass=hass
        )

        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._attr_icon = SENSOR_TYPES[sensor_type][2]
        
        # unique_id는 그대로 유지!
        self._attr_unique_id = f"{DOMAIN}_{device.device_id}_{sensor_type}"
        
        self._attr_extra_state_attributes = {}
        self._attr_native_value = None

    @property
    def has_entity_name(self) -> bool:
        return True

    def update(self):
        """Update the state."""
        pass
