# MCZ Maestro for Home Assistant

[![Release](https://img.shields.io/github/v/release/pvillmann/hass-mcz-maestro?style=flat-square)](https://github.com/pvillmann/hass-mcz-maestro/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.4%2B-41BDF5?style=flat-square&logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![Marketplace](https://img.shields.io/badge/Marketplace-custom%20repository-41BDF5?style=flat-square)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=pvillmann&repository=hass-mcz-maestro&category=integration)
[![License](https://img.shields.io/github/license/pvillmann/hass-mcz-maestro?style=flat-square)](LICENSE)

Control your **MCZ Maestro pellet stove** from Home Assistant: **locally, over the stove's own Wi-Fi, no MCZ cloud.**

Turn it on and off, set the room, puffer and boiler temperature, switch between summer and winter mode and see everything the stove reports: temperatures, fan speeds, pellet sensor, operating phase and more.

> [!NOTE]
> **Works, and is looking for helping hands.** It ran my stove reliably from September to November 2026. I moved on because of the stove's Wi-Fi hotspot, not because of the integration (see [Before you start](#before-you-start)), and now use ESPHome on the stove's second Wi-Fi module: [pvillmann/mcz-maestro-esphome](https://github.com/pvillmann/mcz-maestro-esphome). Since I no longer run it day to day, **your feedback and pull requests decide where it goes from here.** See [Contributing](#contributing).

## Features

| | |
|---|---|
| 🔥 **Thermostat** | Power on/off, room setpoint, real heating state from the stove phase |
| 🌡️ **Setpoints** | Room, puffer (buffer tank) and boiler temperature, power level |
| ☀️ **Modes** | Summer/winter, eco, silent, active, dynamic, chrono |
| 📊 **61 sensors** | Every value the stove reports as its own entity, technical ones tucked away as diagnostics |
| 🕒 **Clock sync** | One button to set the stove's date and time |
| 🔒 **100 % local** | Talks directly to the stove, works without internet |
| 🌍 **Languages** | English, Deutsch, Français |

Tested with an **MCZ Suite/Club Hydromatic 16 M1** (board M1.Hydro, firmware 1.10.10). Other Maestro stoves with the Wi-Fi module should work, please tell me if yours does.

## Before you start

The stove opens its own Wi-Fi hotspot (`MCZ-xxxxxx`). **Home Assistant has to be connected to that hotspot**, the integration cannot reach the stove through your normal home network.

- Your Home Assistant machine needs a Wi-Fi interface that joins the stove hotspot, for example a USB Wi-Fi stick (passed through to the VM if you run HA virtualized). Your normal network connection stays as it is.
- Place it close to the stove, the hotspot signal is weak.
- See [Troubleshooting](#troubleshooting) if the connection keeps dropping.

## Installation

### Marketplace (recommended)

Home Assistant 2026.11 or newer:

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=pvillmann&repository=hass-mcz-maestro&category=integration)

1. Click the button above and confirm your Home Assistant address.
2. Confirm adding the custom repository, then click **Download**.
3. Restart Home Assistant.

<details>
<summary>Without the button</summary>

Open the **Marketplace** in Home Assistant → ⋮ → **Custom repositories**, add `https://github.com/pvillmann/hass-mcz-maestro` with type **Integration**. Search for **MCZ Maestro**, download, restart.

</details>

<details>
<summary>Older Home Assistant with HACS</summary>

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pvillmann&repository=hass-mcz-maestro&category=integration)

Or add `https://github.com/pvillmann/hass-mcz-maestro` as a [custom repository](https://www.hacs.xyz/docs/faq/custom_repositories/) of type Integration. Download, restart.

</details>

<details>
<summary>Manual installation</summary>

Copy `custom_components/mczmaestro` from the [latest release](https://github.com/pvillmann/hass-mcz-maestro/releases/latest) into the `custom_components` folder of your Home Assistant config, then restart.

</details>

## Setup

[![Open your Home Assistant instance and start setting up MCZ Maestro.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mczmaestro)

Or: Settings → Devices & services → **Add integration** → **MCZ Maestro**.

| Field | Default | |
|---|---|---|
| Host | `192.168.120.1` | Address of the stove in its hotspot, usually unchanged |
| Port | `81` | |
| Seconds between updates | `30` | How often the stove is polled |

The stove then shows up as one device with a thermostat and all its entities.

## Troubleshooting

<details>
<summary><b>Setup fails with a connection or "unknown" error</b></summary>

Home Assistant is not connected to the stove hotspot. Check that the Wi-Fi interface is joined to `MCZ-xxxxxx` and has an address in `192.168.120.x`. The stove can only be reached through the hotspot, not through its address in your home network.

</details>

<details>
<summary><b>Entities become unavailable every now and then</b></summary>

The Wi-Fi module runs the hotspot and the home Wi-Fi connection on a single radio. Whenever the home Wi-Fi side changes channel (cloud reconnect, roaming), the hotspot moves with it and every client is kicked off. The integration reconnects by itself, but you will see short gaps.

**Fix:** block the stove's MAC address in your home Wi-Fi. That stopped the drops completely for me (0 drops in 14 h instead of about 4.5 per hour). Downside: the MCZ app and cloud no longer work while the stove is blocked.

</details>

<details>
<summary><b>Debug logging</b></summary>

```yaml
logger:
  logs:
    custom_components.mczmaestro: debug
```

</details>

## Technical details

<details>
<summary>What's different from upstream</summary>

This is a fork of [Aohzan/hass-mcz-maestro](https://github.com/Aohzan/hass-mcz-maestro).

**Fixes**

- **Wrong field mapping:** `Pellet_Sensor` (field 47) was missing and a made-up `Sound_Effects_State` took its place, so fields 47–51 were shifted by one. Corrected against [Chibald/maestrogateway](https://github.com/Chibald/maestrogateway).
- **Switches always off:** the parser returns strings, `is_on` compared with the integer `1`.
- **Stove never powered on:** same string/int problem in the climate entity. Power-on now also covers Standby, Auto Eco and Cooling.
- **Event loop blocked:** connecting, polling and writing ran blocking socket I/O in the event loop. All of it runs in the executor now.
- **Desynced polls:** poll and writes share one socket without request/response framing. A lock serializes them, and the time-sync echo is drained.
- **Dead after Wi-Fi drops:** the socket is rebuilt when it dies. Setup raises `ConfigEntryNotReady`, so HA retries instead of giving up.

**New**

- Every protocol field as its own entity (61 instead of attributes on one sensor). Technical values are diagnostic entities.
- Puffer setpoint, boiler setpoint, power level (numbers).
- Summer/winter mode (switch).
- Sync date & time (button).
- `hvac_action` from the real stove phase.
- Translations: English, French, German.

</details>

<details>
<summary>Write commands (found via MITM)</summary>

Captured from the MCZ app with ARP spoofing on the stove hotspot (the hotspot has no client isolation). Format `C|WriteParametri|<param>|<value>`, temperatures are sent ×2.

| Function | Param | Value | Read back in |
|---|---|---|---|
| Puffer setpoint | 52 | °C ×2 | field 56 `SetPuffer` (÷2) |
| Summer mode | 58 | 0 = winter, 1 = summer | field 51 `Mode` |
| Boiler setpoint | 51 | °C ×2 | field 27 `Boiler_Setpoint` |
| Room setpoint | 42 | °C ×2 | field 26 `Temperature_Setpoint` |
| Power on / off | 34 | 1 / 40 | field 1 `Stove_State` |

Date and time: `C|SalvaDataOra|DDMMYYYYHHMM`, the stove answers `AA|<same string>`.

The WebSocket listens on port 81 and is only reachable through the hotspot.

</details>

## Contributing

You own an MCZ stove and use Home Assistant? Then you can help, no matter whether you write code or not.

- 🙋 **Tell us your stove model.** Open an issue with model, board and firmware (shown in the stove menu) and whether it works. That alone helps the next person a lot.
- 🐛 **Report problems.** Describe what you expected, what happened, and attach a debug log (see [Troubleshooting](#troubleshooting)).
- 🌍 **Translate.** Add a file to [`custom_components/mczmaestro/translations/`](custom_components/mczmaestro/translations/), English is the template.
- 🔧 **Send a pull request.** Fixes, new entities, cleanups, all welcome. Please test it on your own stove and say which model you used.
- 🔍 **Found a new command?** If you sniff more write commands from the MCZ app, add them to the write command table under [Technical details](#technical-details).

I review pull requests as time allows and am happy to hand over maintenance to someone who runs this every day.

## Credits

- [Aohzan/hass-mcz-maestro](https://github.com/Aohzan/hass-mcz-maestro): the original integration
- [Chibald/maestrogateway](https://github.com/Chibald/maestrogateway): protocol reference

Not affiliated with MCZ Group. Licensed under [Apache 2.0](LICENSE).
