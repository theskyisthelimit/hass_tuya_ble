"""The Tuya BLE integration."""
from __future__ import annotations

import logging

from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS, get_device

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .tuya_ble import TuyaBLEDevice

from .cloud import HASSTuyaBLEDeviceManager
from .const import (
    CONF_CATEGORY,
    CONF_DEVICE_NAME,
    CONF_FUNCTIONS,
    CONF_PRODUCT_MODEL,
    CONF_PRODUCT_NAME,
    CONF_PRODUCT_ID,
    CONF_STATUS_RANGE,
    DOMAIN,
)
from .devices import TuyaBLECoordinator, TuyaBLEData, get_device_product_info

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
]

_LOGGER = logging.getLogger(__name__)

LEGACY_CONF_MAC = "mac"
DEFAULT_FINGERBOT_CATEGORY = "szjqr"
DEFAULT_FINGERBOT_PRODUCT_NAME = "Fingerbot Plus"
DEFAULT_FINGERBOT_PRODUCT_ID = "yiihr7zh"


def _entry_manager_data(entry: ConfigEntry) -> dict:
    """Merge current options with legacy fingerbot-only config entry data."""
    data = entry.options.copy()
    data.update(entry.data)
    if CONF_ADDRESS not in data and LEGACY_CONF_MAC in data:
        data[CONF_ADDRESS] = data[LEGACY_CONF_MAC]
    if CONF_CATEGORY not in data:
        data[CONF_CATEGORY] = DEFAULT_FINGERBOT_CATEGORY
    if CONF_PRODUCT_ID not in data:
        data[CONF_PRODUCT_ID] = DEFAULT_FINGERBOT_PRODUCT_ID
    if CONF_PRODUCT_NAME not in data:
        data[CONF_PRODUCT_NAME] = DEFAULT_FINGERBOT_PRODUCT_NAME
    if CONF_DEVICE_NAME not in data:
        data[CONF_DEVICE_NAME] = entry.title or data[CONF_PRODUCT_NAME]
    if CONF_PRODUCT_MODEL not in data:
        data[CONF_PRODUCT_MODEL] = ""
    data.setdefault(CONF_FUNCTIONS, [])
    data.setdefault(CONF_STATUS_RANGE, [])
    return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya BLE from a config entry."""
    manager_data = _entry_manager_data(entry)
    address: str = manager_data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), True
    ) or await get_device(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Tuya BLE device with address {address}"
        )
    manager = HASSTuyaBLEDeviceManager(hass, manager_data)
    device = TuyaBLEDevice(manager, ble_device)
    await device.initialize()
    product_info = get_device_product_info(device)

    coordinator = TuyaBLECoordinator(hass, device)

    '''
    try:
        await device.update()
    except BLEAK_EXCEPTIONS as ex:
        raise ConfigEntryNotReady(
            f"Could not communicate with Tuya BLE device with address {address}"
        ) from ex
    '''
    hass.add_job(device.update())

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Update from a ble callback."""
        device.set_ble_device_and_advertisement_data(
            service_info.device, service_info.advertisement
        )

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            BluetoothCallbackMatcher({ADDRESS: address}),
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = TuyaBLEData(
        entry.title,
        device,
        product_info,
        manager,
        coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await device.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    if entry.title != data.title:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data: TuyaBLEData = hass.data[DOMAIN].pop(entry.entry_id)
        await data.device.stop()

    return unload_ok
