"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import logging
from .const import *
from homeassistant.components.button import ButtonEntity


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

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
    """Representation of a CityWaste Refresh Button."""

    def __init__(self, hass, device):
        """Initialize the button."""
        super().__init__(device)

        self.hass = hass
        self._device = device

        # HA 최신 규격에 맞춘 변수 할당
        self._attr_name = "Refresh"
        
        # 기기 ID를 포함하여 절대 변하지 않는 고유 ID 생성
        self._attr_unique_id = f"{DOMAIN}_{device.device_id}_refresh_button"

    @property
    def has_entity_name(self) -> bool:
        return True

    # HA 권장 방식: 동기형 press() 대신 비동기형 async_press() 사용
    async def async_press(self) -> None:
        """Handle the button press."""
        await self._device.get_price()

    """Sensor Properties"""
    @property
    def has_entity_name(self) -> bool:
        return True

    def update(self):
        """Update the state."""


