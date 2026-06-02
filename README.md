# Tuya BLE Fingerbot for Home Assistant

Fingerbot-only Home Assistant custom integration for Tuya/Adaprox BLE
Fingerbot devices. It connects locally over Bluetooth, presses the bot, and
disconnects again.

This integration is intentionally small: no Tuya cloud login flow, no generic
Tuya BLE device database. You enter the BLE credentials once in Home Assistant.

## Install With HACS

Add this repository as a HACS custom repository:

```text
https://github.com/theskyisthelimit/hass_tuya_ble
```

Category:

```text
Integration
```

Then install, restart Home Assistant, and add:

```text
Settings -> Devices & services -> Add integration -> Tuya BLE Fingerbot
```

## Configuration

Use values extracted from Tuya/Smart Life:

```text
Name: Fingerbot Plus
MAC address: <BLE MAC>
Local key: <Tuya local key>
UUID: <Tuya UUID>
Device ID: <Tuya device ID>
Product ID: yiihr7zh
Profile: auto
Send position settings before pressing: enabled
BLE timeout: 12
```

For `yiihr7zh` Fingerbot Plus, `Profile: auto` maps to the `classic` datapoint
profile.

The Tuya IoT Access ID, Access Secret, and Project Code are not needed at
runtime. They are only useful for extracting `local_key`, `uuid`, and
`device_id`.

## Supported Fingerbot Profiles

- `classic`: `szjqr` Fingerbot/Fingerbot Plus, including `yiihr7zh`
- `cubetouch`: CubeTouch 1s/II
- `kg`: newer Fingerbot Plus IDs like `mknd4lci` and `riecov42`
- `legacy`: original proof-of-concept datapoints

## Troubleshooting

- Close the Tuya/Smart Life app before testing; it can hold the BLE connection.
- Keep the Fingerbot near the Home Assistant Bluetooth adapter.
- If pressing works inconsistently, disable `Send position settings before pressing`.
- If the device was re-paired in Tuya, extract the credentials again.

## Credits

Protocol work is based on the original
[redphx/poc-tuya-ble-fingerbot](https://github.com/redphx/poc-tuya-ble-fingerbot)
proof of concept and current Home Assistant Tuya BLE community forks.
