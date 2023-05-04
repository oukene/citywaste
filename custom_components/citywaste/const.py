"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    MASS_KILOGRAMS
)

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "citywaste"
NAME = "citywaste"
VERSION = "1.0.2"

CONF_ADD_ANODHER = "add_another"

CONF_TAG_ID = "tag_id"
CONF_DONG = "dong"
CONF_HO = "ho"
CONF_PRICE = "price"
CONF_REFRESH_PERIOD = "refresh_period"

STYPE_TOTAL_KG = "total_kg"
STYPE_LAST_KG = "last_kg"
STYPE_TOTAL_COUNT = "total_count"
STYPE_TOTAL_PRICE = "total_price"

SENSOR_TYPES = {
    STYPE_TOTAL_KG: ["총 배출량", MASS_KILOGRAMS, "mdi:scale"],
    STYPE_LAST_KG: ["최근 배출량", MASS_KILOGRAMS, "mdi:scale"],
    STYPE_TOTAL_COUNT: ["총 횟수", "회", "mdi:counter"],
    STYPE_TOTAL_PRICE: ["예상 요금", "원", "mdi:currency-krw"],
}

CONF_URL = "https://www.citywaste.or.kr/portal/status/selectDischargerQuantityQuickMonthNew.do"

headers: dict = {
    "Referer": 'https://www.citywaste.or.kr/portal/status/selectSimpleEmissionQuantity.do',
}

OPTIONS = [
    (CONF_TAG_ID, "", cv.string),
    (CONF_DONG, "", cv.string),
    (CONF_HO, "", cv.string),
    (CONF_PRICE, "", int),
    (CONF_REFRESH_PERIOD, 30, vol.Coerce(int)),
]
