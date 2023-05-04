"""Config flow for Hello World integration."""
from copy import deepcopy
from distutils.command.config import config
import logging
from select import select
from unicodedata import name
from xmlrpc.client import boolean
import aiohttp
import asyncio
import json
from markupsafe import string
import voluptuous as vol
import socket
from typing import Any, Dict, Optional
from datetime import datetime

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import *

from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback


_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            # if user_input[CONF_NETWORK_SEARCH] == True:
            #    return self.async_create_entry(title=user_input[CONF_AREA_NAME], data=user_input)
            # else:
            self.data = user_input
            # self.devices = await get_available_device()
            # return await self.async_step_hosts()
            #self.data["modifydatetime"] = datetime.now()
            return self.async_create_entry(title=NAME, data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required(CONF_TAG_ID): cv.string,
                    vol.Required(CONF_DONG): cv.string,
                    vol.Required(CONF_HO): cv.string,
                    vol.Required(CONF_PRICE): int,
                    vol.Required(CONF_REFRESH_PERIOD, "", 60): int
                }), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Naver Weather."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        if user_input is not None:
            #onf.data["modifydatetime"] = datetime.now()
            return self.async_create_entry(title="", data=user_input)

        options_schema = {}
        data_list = [CONF_TAG_ID, CONF_DONG, CONF_HO, CONF_PRICE, CONF_REFRESH_PERIOD]
        for name, default, validation in OPTIONS:
            to_default = conf.options.get(name, default)
            if name in data_list and conf.options.get(name, default) == default:
                to_default = conf.data.get(name, default)
            key = vol.Optional(name, default=to_default)
            options_schema[key] = validation
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options_schema)
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
