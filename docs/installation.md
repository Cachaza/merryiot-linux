# What booted on this unit

This is the historical migration record, not a command-by-command installer. Another board revision, image release or partition layout may need different changes. Do not write another machine's loader or copy raw addresses as universal Rockchip defaults.

## Starting point

The original system booted Debian 10, vendor Linux 4.19.193 and U-Boot 2017.09 from internal eMMC. Docker started during boot. The supplied SD contained miner data, not an OS; its MBR partition type advertised FAT32 while the filesystem was exFAT.

I captured serial output through a Raspberry Pi Pico, then saved the original SD, eMMC user area and both separate eMMC boot regions. Every saved chunk was checked against a readback, then the assembled images were checked on the Mac. Those backups are private. Protected secure-element contents and RPMB are outside their scope.

## Why the Panther-X2 image

Crankk maps MerryIoT V1 to Panther-X2. That was a useful lead, not proof of full compatibility. The image inspected and tested was:

```
Armbian_26.11.0_rockchip_panther-x2_trixie_6.18.63_server_2026.11.14.img.gz
SHA-256 (compressed): 367289934e5b664867a4aad6f28864a35435682ee886ca3143b7a2904cbf18f1
```

Source: [ophub November 2026 Debian Trixie release](https://github.com/ophub/amlogic-s9xxx-armbian/releases/tag/Armbian_trixie_arm64_server_2026.11). This is unofficial community Armbian based on Debian 13, not Ubuntu and not an LG/Browan firmware release. Verify the publisher's asset digest yourself; this receipt identifies my historical input, not whatever a newer release supplies.

## SD first

The first test booted the candidate kernel, initrd and device tree from SD through the existing U-Boot. Its console setting named `ttyS02`; the device-tree alias pointed to `ttyS2`. Correcting the console argument restored the expected serial path at 1,500,000 baud.

The eMMC controller was disabled in the test device tree so the original internal installation stayed protected during early testing. First-boot scripts and automounts also had to be considered: putting Linux on SD does not automatically make the eMMC safe from writes.

## Internal installation

The internal layout retained the original `uboot` and `misc` entries, and the raw factory loader/vendor bytes in the measured range `[17408, 16777216)`. These byte offsets describe this board's captured image only. New Linux boot/root partitions replaced the old OS layout. The protective MBR, primary GPT and backup GPT were rebuilt and verified for the measured target capacity.

The boot/root filesystem UUIDs were made different from the rescue SD's UUIDs. The new fstab, extlinux entry and Armbian environment were updated together. The eMMC controller's device-tree status was changed from `fail` to `okay` for internal use. The installer verified the target identity/capacity and a fresh safety export before writing OS payloads and GPT metadata, then checked readbacks and retained factory bytes.

There was also a boot-script problem: its temporary load address `0x09000000` fell in a firmware-reserved RAM hole on this boot. The prepared fallback script used `0x10000000`, selected from the measured free RAM map after the loaded initrd. The rebuilt legacy `boot.scr` needed valid payload and header CRCs. That address is a finding from this unit, not a recommended default for another bootloader.

The generic `armbian-install` command mentioned in some instructions was absent from the inspected image. Running an unrelated installer was not how this migration happened.

## Proving the SD was no longer needed

Booting a root filesystem on eMMC while the loader still comes from SD is not the same as an independent internal boot. After the guarded write and boot recovery, I shut the miner down, removed the SD, powered it on and captured an unattended boot. U-Boot found extlinux on internal `mmc0:3`, and Linux mounted boot/root from the internal MMC device. No storage SD device was detected.

Docker and container DNS were tested after recovery. The board later entered service with Pi-hole and Tailscale. This does not validate every peripheral or another MerryIoT revision.

## What you still need to reproduce it

Your own verified original images, serial access, the exact candidate image (or a fresh compatibility investigation), a measured partition/RAM map and a reviewed board-specific write/recovery plan. This repo does not yet package that guarded image builder/flasher. It must not be treated as a ready-to-run installation kit.
