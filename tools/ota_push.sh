#!/bin/bash
# Julius OS OTA Push Tool
# Run from admin MacBook: ./tools/ota_push.sh <device_ip> <update.pkg>

set -e

DEVICE_IP="$1"
UPDATE_PKG="$2"
OTA_PORT=9876
ADMIN_KEY_FILE="$HOME/.julius/admin.key"

if [ -z "$DEVICE_IP" ] || [ -z "$UPDATE_PKG" ]; then
    echo "Usage: $0 <device_ip> <update_package>"
    exit 1
fi

if [ ! -f "$ADMIN_KEY_FILE" ]; then
    echo "Admin key not found at $ADMIN_KEY_FILE"
    echo "Generate with: julius_keygen --admin"
    exit 1
fi

if [ ! -f "$UPDATE_PKG" ]; then
    echo "Update package not found: $UPDATE_PKG"
    exit 1
fi

ADMIN_KEY=$(cat "$ADMIN_KEY_FILE")
PKG_SIZE=$(stat -f%z "$UPDATE_PKG" 2>/dev/null || stat -c%s "$UPDATE_PKG")
PKG_SHA256=$(sha256sum "$UPDATE_PKG" | awk '{print $1}')
VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")

echo "Julius OS OTA Push Tool"
echo "======================"
echo "Device  : $DEVICE_IP"
echo "Package : $UPDATE_PKG"
echo "Version : $VERSION"
echo "Size    : $PKG_SIZE bytes"
echo "SHA256  : $PKG_SHA256"
echo ""

read -p "Push update? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted"
    exit 0
fi

echo "Connecting to $DEVICE_IP:$OTA_PORT..."

python3 - << PYEOF
import socket
import struct
import hashlib
import os

device_ip  = "$DEVICE_IP"
ota_port   = $OTA_PORT
admin_key  = "$ADMIN_KEY"
update_pkg = "$UPDATE_PKG"
version    = "$VERSION"

with open(update_pkg, "rb") as f:
    pkg_data = f.read()

sha256 = hashlib.sha256(pkg_data).digest()

# Build header
magic      = b"JULIUS_OTA_V1\x00\x00"
ver_bytes  = version.encode().ljust(32, b"\x00")
key_bytes  = admin_key.encode().ljust(256, b"\x00")
size_bytes = struct.pack(">I", len(pkg_data))

header = magic + ver_bytes + key_bytes + size_bytes + sha256

print(f"Sending header ({len(header)} bytes)...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(30)
s.connect((device_ip, ota_port))
s.sendall(header)

print(f"Sending package ({len(pkg_data)} bytes)...")
chunk = 4096
sent  = 0
while sent < len(pkg_data):
    end   = min(sent+chunk, len(pkg_data))
    n     = s.send(pkg_data[sent:end])
    sent += n
    print(f"Progress: {sent}/{len(pkg_data)} bytes ({int(sent/len(pkg_data)*100)}%)", end="\r")

s.close()
print(f"\nOTA package sent successfully!")
print("Device will verify and apply update automatically.")
PYEOF

echo ""
echo "OTA push complete!"
echo "Device will reboot after successful update."
```

---

## 🔧 File 9 — `buildroot/configs/julius_defconfig`

Complete Buildroot config:
```
BR2_arm=y
BR2_cortex_a55=y
BR2_ARM_FPU_NEON_FP_ARMV8=y
BR2_TOOLCHAIN_BUILDROOT_GLIBC=y
BR2_TOOLCHAIN_BUILDROOT_CXX=y
BR2_TARGET_GENERIC_HOSTNAME="julius"
BR2_TARGET_GENERIC_ISSUE="Julius OS v1.0"
BR2_INIT_SYSTEMD=y
BR2_TARGET_LOCALTIME="Asia/Kolkata"
BR2_TARGET_GENERIC_ROOT_PASSWD="julius_secure_2024"
BR2_LINUX_KERNEL=y
BR2_LINUX_KERNEL_LATEST_VERSION=y
BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="board/julius/kernel.config"
BR2_TARGET_ROOTFS_EXT2=y
BR2_TARGET_ROOTFS_EXT2_4=y
BR2_TARGET_ROOTFS_EXT2_SIZE="1G"
BR2_TARGET_UBOOT=y
BR2_TARGET_UBOOT_BOARD_DEFCONFIG="julius"
BR2_TARGET_UBOOT_CONFIG_FRAGMENT_FILES="board/julius/uboot.fragment"
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PY_PYC=y
BR2_PACKAGE_PYTHON_PYGAME=y
BR2_PACKAGE_OPENSSL=y
BR2_PACKAGE_BUSYBOX=y
BR2_PACKAGE_BASH=y
BR2_PACKAGE_NANO=y
BR2_PACKAGE_HTOP=y
BR2_PACKAGE_GIT=y
BR2_PACKAGE_NMAP=y
BR2_PACKAGE_WIRELESS_TOOLS=y
BR2_PACKAGE_WPA_SUPPLICANT=y
BR2_PACKAGE_BLUEZ5_UTILS=y
BR2_PACKAGE_NETWORK_MANAGER=y
BR2_PACKAGE_IPTABLES=y
BR2_PACKAGE_OPENSSH=y
BR2_PACKAGE_USBUTILS=y
BR2_ROOTFS_OVERLAY="board/julius/rootfs-overlay"
BR2_ROOTFS_POST_BUILD_SCRIPT="board/julius/post-build.sh"
BR2_ROOTFS_POST_IMAGE_SCRIPT="board/julius/post-image.sh"
