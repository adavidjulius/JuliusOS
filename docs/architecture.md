# Julius OS Architecture

## Overview
Julius OS is a custom embedded Linux OS for a mini handheld device.

## Layers

### Layer 0 — Hardware
- Custom PCB with Allwinner H3 SoC
- 320x480 IPS display (SPI)
- Capacitive touch (I2C)
- Fingerprint sensor (SPI)
- MagSafe wireless charging
- WiFi + Bluetooth (RTL8723DS)
- 2000mAh Li-Ion battery

### Layer 1 — Bootloader (U-Boot)
- Custom julius_defconfig
- Julius OS boot logo
- Fast boot target under 5 seconds
- Secure boot verification

### Layer 2 — Kernel
- Linux 6.x with Julius patches
- Custom display driver (julius_display.ko)
- Custom touch driver (julius_touch.ko)
- Custom fingerprint driver (julius_fp.ko)
- Custom charging driver (julius_magsafe.ko)

### Layer 3 — Drivers
- julius_display.c — SPI display framebuffer
- julius_touch.c  — I2C capacitive touch
- julius_fp.c     — SPI fingerprint sensor
- julius_magsafe.c — Wireless charging control

### Layer 4 — Services (C daemons)
- julius_core     — Main service orchestrator (PID 2)
- julius_power    — Battery and charging manager
- julius_ota      — OTA update receiver
- julius_security — Fingerprint auth and keystore

### Layer 5 — UI (Python/Pygame)
- julius_ui.py    — Main launcher and UI
- All apps in src/apps/

### Layer 6 — Apps
- 34 apps covering all device functions

## OTA Update System
- Only admin device with valid key can push
- SHA256 verification before applying
- Automatic rollback on failure
- Wireless only — no physical ports

## Security
- Fingerprint authentication on unlock
- Admin key required for OTA
- Encrypted keystore for passwords
- No USB data port (MagSafe only)
```

---

## 📋 Summary — What to Create on GitHub

Create these files directly on GitHub:
```
services/julius_core/main.c
services/julius_core/ipc.c
services/julius_core/ipc.h
services/julius_ota/ota_client.c
services/julius_security/fingerprint_auth.c
drivers/display/julius_display.c
services/julius_power/power_manager.c
buildroot/board/julius/rootfs-overlay/etc/init.d/S99julius
tools/ota_push.sh
buildroot/configs/julius_defconfig
docs/architecture.md
```

---

## 🗺️ What We Now Have
```
UI Layer          DONE  Python/Pygame julius_ui.py
Core Service      DONE  C julius_core
IPC System        DONE  C unix sockets
OTA Updates       DONE  C + Python push tool
Fingerprint Auth  DONE  C SPI driver
Display Driver    DONE  C Linux kernel module
Power Manager     DONE  C battery + MagSafe
Boot Script       DONE  Shell init.d
Buildroot Config  DONE  Full OS config
Architecture Doc  DONE  Complete reference
