# Linux on a €35 MerryIoT miner

Notes and small tools from repurposing my Browan MerryIoT Hotspot Miner V1 as a Debian server. I bought it for the computer inside, after [Brainstormity's post](https://x.com/brainstormity/status/2118765365123567760) about reusing old Helium hardware.

This unit has an RK3566, about 4 GB RAM and 32 GB eMMC. It now boots Debian 13 from its eMMC and runs a secondary Pi-hole, Tailscale, a heartbeat watchdog and Beszel. Nebula Sync pulls the primary Pi-hole configuration hourly. Service status was checked on 23 November 2026; no real failover drill was performed.

This is a record of one board and its adaptations, not a new Linux distribution or a universal installer. The OS came from ophub's unofficial Armbian Panther-X2 build. The original factory loader remains in place. Nothing here flashes a block device automatically.

## Start here

- [What was done, including the boot fixes](docs/installation.md)
- [Pico serial wiring and bridge](docs/uart.md)
- [What to preserve before changing storage](docs/backups.md)
- [Current jobs and limitations](docs/in-service.md)
- [Sources, scope and provenance](docs/sources.md)

## Included tools

Python 3.11 or newer (the backup verifier uses `hashlib.file_digest`), standard library only. The UART tool uses POSIX terminal APIs (macOS/Linux) and requires MicroPython already installed on the Pico. It is a cleaned-up adaptation of my capture script; this packaged version has offline tests but has not been tried on the physical board yet.

```sh
python3 tools/pico_uart.py --help
python3 tools/verify_backups.py --help
python3 -m unittest discover -s tests -v
```

`pico_uart.py` loads a RAM-only MicroPython bridge, records received bytes and optionally forwards keyboard input. The miner UART was measured at 1,500,000 baud, 8N1. Loading the bridge does not replace the Pico's MicroPython firmware. Running it does interrupt the Pico's current program; only use a Pico dedicated to this job.

`verify_backups.py` compares regular image files with your own previously recorded byte lengths and SHA-256 hashes. It does not acquire a backup or prove that restoration works. See the [manifest format](docs/backups.md).

## What is deliberately absent

No disk images, factory provisioning data, secure-element keys, SSH keys, Tailscale identity, Wi-Fi profiles, raw console logs or personal network configuration. My original flasher and image-preparation scripts embed board-specific identity/layout checks and private paths; they are not included as a generic installation command. The installation notes explain what was changed and where reproduction still needs work.

## Credits

[ophub/amlogic-s9xxx-armbian](https://github.com/ophub/amlogic-s9xxx-armbian), [Crankk's MerryIoT notes](https://github.com/crankkio/docs/wiki/Browan-MerryIoT-V1), [yjdwbj/panther-x2](https://github.com/yjdwbj/panther-x2), [MicroPython](https://micropython.org/), [Pi-hole](https://github.com/pi-hole/pi-hole), [Nebula Sync](https://github.com/lovelaze/nebula-sync), [Tailscale](https://github.com/tailscale/tailscale) and [Beszel](https://github.com/henrygd/beszel). Codex helped write the investigation and bridge scripts; I supplied the hardware and checked the physical results.
