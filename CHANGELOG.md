# Changelog

## 0.2.0 (fork pvillmann, 2026-11)

Archived fork, see README.

- fix status field mapping (Pellet_Sensor missing, fields 47-51 shifted)
- fix switches always off and stove never powering on (string/int comparisons)
- run blocking socket I/O in the executor, serialize poll and writes
- rebuild the WebSocket after Wi-Fi drops, retry setup with ConfigEntryNotReady
- add all protocol fields as entities
- add puffer setpoint, boiler setpoint, power level, summer mode, time sync
- derive hvac_action from the stove phase
- translations en/fr/de

## 0.1.7

- fix error when adding new integration

## 0.1.6

- fix deviceinfo error
- fix deprecated code

## 0.1.5

- fix state from climate and sensor

## 0.1.4

- add debug
- fix state info error

## 0.1.3

- rename top dir

## 0.1.2

- add debug logs
- handle unknown values

## 0.1.1

- fix config flow dependency

## 0.1.0

- Initial release
