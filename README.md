# MCZ Maestro (local Wi-Fi) for Home Assistant

Fork of [Aohzan/hass-mcz-maestro](https://github.com/Aohzan/hass-mcz-maestro). The `mczmaestro` integration talks to an MCZ Maestro stove over the stove's own Wi-Fi hotspot (WebSocket, default `192.168.120.1:81`). No MCZ cloud involved.

> **Status: archived, not maintained.**
> This fork ran my stove from September to November 2026. I have since moved to ESPHome on the stove's second Wi-Fi module ([pvillmann/mcz-maestro-esphome](https://github.com/pvillmann/mcz-maestro-esphome), based on [lexyan/mcz-maestro-esphome](https://github.com/lexyan/mcz-maestro-esphome)), which needs no hotspot connection. The code here works and is published so others can use the fixes and findings. Issues and PRs are welcome but may not get an answer.

Tested on an **MCZ Suite/Club Hydromatic 16 M1** (board M1.Hydro, firmware 1.10.10).

## What's different from upstream

**Fixes**

- **Wrong field mapping:** `Pellet_Sensor` (field 47) was missing and a made-up `Sound_Effects_State` took its place, so fields 47–51 were shifted by one. Corrected against [Chibald/maestrogateway](https://github.com/Chibald/maestrogateway).
- **Switches always off:** the parser returns strings, `is_on` compared with the integer `1`.
- **Stove never powered on:** same string/int problem in the climate entity. Power-on now also covers Standby, Auto Eco and Cooling.
- **Event loop blocked:** connecting, polling and writing ran blocking socket I/O in the event loop. All of it runs in the executor now.
- **Desynced polls:** poll and writes share one socket without request/response framing. A lock serializes them, and the time-sync echo is drained.
- **Dead after Wi-Fi drops:** the socket is rebuilt when it dies. Setup raises `ConfigEntryNotReady`, so HA retries instead of giving up.

**New**

- Every protocol field as its own entity (61 instead of attributes on one sensor). Technical values are diagnostic entities.
- Puffer (buffer tank) setpoint, boiler setpoint, power level (numbers).
- Summer/winter mode (switch).
- Sync date & time (button).
- `hvac_action` from the real stove phase.
- Translations: English, French, German.

## Write commands found via MITM

Captured from the MCZ app with ARP spoofing on the stove hotspot (the hotspot has no client isolation). Format `C|WriteParametri|<param>|<value>`, temperatures are sent ×2.

| Function | Param | Value | Read back in |
|---|---|---|---|
| Puffer setpoint | 52 | °C ×2 | field 56 `SetPuffer` (÷2) |
| Summer mode | 58 | 0 = winter, 1 = summer | field 51 `Mode` |
| Boiler setpoint | 51 | °C ×2 | field 27 `Boiler_Setpoint` |
| Room setpoint | 42 | °C ×2 | field 26 `Temperature_Setpoint` |
| Power on / off | 34 | 1 / 40 | field 1 `Stove_State` |

Date and time: `C|SalvaDataOra|DDMMYYYYHHMM`, the stove answers `AA|<same string>`.

## Things to know

- **The hotspot drops clients when the stove is also on your home Wi-Fi.** The Wi-Fi module runs AP and station on one radio. When the home Wi-Fi side changes channel (cloud reconnect, roaming), the hotspot moves with it and every client is kicked. Blocking the stove's MAC on the home Wi-Fi stopped the drops completely (0 drops in 14 h, before about 4.5 per hour). Downside: no MCZ app or cloud while blocked.
- The WebSocket on port 81 is only reachable through the hotspot, not via the stove's home network IP.
- Home Assistant needs a Wi-Fi interface that joins the stove hotspot (e.g. a USB/PCIe card passed through to the HA VM).

## Installation

### HACS

Add `https://github.com/pvillmann/hass-mcz-maestro` as a custom repository (type Integration), see <https://www.hacs.xyz/docs/faq/custom_repositories/>.

### Manually

Copy `custom_components/mczmaestro` into your config folder.

## Configuration

Settings → Devices & services → Add integration → MCZ Maestro. Defaults: host `192.168.120.1`, port `81`, scan interval 30 s.

## Credits

- [Aohzan/hass-mcz-maestro](https://github.com/Aohzan/hass-mcz-maestro), the original integration
- [Chibald/maestrogateway](https://github.com/Chibald/maestrogateway), protocol reference
