# What it runs now

Observed 23 November 2026, after the installation work:

- Debian 13 from internal eMMC.
- Secondary Pi-hole DNS resolver. Nebula Sync pulls local DNS records, upstreams, blocklists, custom rules and client groups from the primary hourly. A real temporary DNS record was reconciled through authenticated sync; unchanged settings skip the import.
- Tailscale subnet router with its route approved and tested.
- An infrastructure heartbeat watchdog reporting reachability to an external receiver. Alert/recovery logic was tested in simulation; there has not been an end-to-end outage/failover drill.
- Beszel monitoring.

Both DNS resolvers passed local and upstream lookups and blocking checks. This does not prove client failover behavior: two configured DNS resolvers are not by themselves a tested failover system.

The NPU passed a numerical correctness check; that is not a speed measurement. The kernel driver exposed H.264 decoding and JPEG-only encoding. This is a driver observation, not proof the silicon cannot encode H.264. LoRa operation was not tested during the migration. Detailed service configuration and identities stay private.
