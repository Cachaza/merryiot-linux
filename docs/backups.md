# Preserve before replacing

My backups covered the whole original SD, whole eMMC user area and both 4 MiB eMMC boot regions. Reading eMMC at U-Boot avoided acquiring a live, changing Linux filesystem. A whole-device image also kept reserved loader/vendor bytes that a rootfs-only copy would miss.

The acquisition was after earlier normal boots, so this was not a pristine pre-power-on forensic image. Secure-element private keys, RPMB and OTP/eFuse state were not acquired. Replacing their contents is not part of installing Linux, and a disk image cannot restore a destroyed secure-element identity.

The SD was reused for Linux after its backup was checked. Keep the authoritative verified backups on another machine. A checksum proves agreement with a recorded file; it does not prove a restore procedure or a complete factory recovery path.

## Offline file verification

Create a JSON manifest from trusted acquisition records, not by hashing potentially damaged files and treating the result as proof of an earlier state:

```json
{
  "files": [
    {"path": "original-sd.img", "bytes": 62921900032, "sha256": "YOUR_RECORDED_64_HEX_CHARACTER_SHA256"}
  ]
}
```

The size above is from my original SD. Use your own measured size and recorded digest for every image. The placeholder is intentionally invalid and will be rejected.

```
python3 tools/verify_backups.py --root /path/to/private/backups --manifest /path/to/trusted-manifest.json
```

Only regular files under the selected root are read. Absolute paths, traversal, symlinks, duplicate paths and malformed manifests are rejected. The verifier never writes to a disk or image. Do not place raw images, keys or acquisition logs in this repository.
