# Sources and provenance

This repo was prepared from saved work, not a fresh installation replay. The main migration evidence dates to 16–19 November 2026; service/sync checks date to 23 November. Historical notes contained interim states, so the final SD-removed cold boot and later authenticated DNS sync supersede earlier “not verified” and “snapshot only” descriptions.

The Pico bridge was adapted from Codex-written RAM-bridge scripts used with this board. The verification utility is new repository tooling; it was not the tool used to acquire the original images. No third-party source files or firmware blobs are bundled. Upstream projects retain their own licenses.

- Inspiration: https://x.com/brainstormity/status/2118765365123567760
- Platform relationship: https://github.com/crankkio/docs/wiki/Browan-MerryIoT-V1
- Community OS builds: https://github.com/ophub/amlogic-s9xxx-armbian
- Historical release: https://github.com/ophub/amlogic-s9xxx-armbian/releases/tag/Armbian_trixie_arm64_server_2026.11
- Hardware reference: https://github.com/yjdwbj/panther-x2
- MicroPython: https://micropython.org/
- Pi-hole: https://github.com/pi-hole/pi-hole
- Nebula Sync: https://github.com/lovelaze/nebula-sync
- Tailscale: https://github.com/tailscale/tailscale
- Beszel: https://github.com/henrygd/beszel

The adaptation and documentation are not a claim to have invented Debian-on-RK3566, the upstream device tree, MicroPython or any of the services. Current releases and hardware compatibility can change; these links credit the original work rather than promise that today's download matches the inspected historical image.
