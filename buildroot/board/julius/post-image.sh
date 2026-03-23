#!/bin/bash
# Julius OS - Buildroot post-image.sh
# Creates flashable julius_emmc.img for 8GB eMMC

set -e
BINARIES="$1"
JULIUS_BASE="$(cd "$(dirname "$0")/../../.." && pwd)"
IMG="$BINARIES/julius_emmc.img"
IMG_SIZE_MB=7800

log()    { echo "[julius-post-image] $*"; }
log_ok() { echo "[julius-post-image] OK $*"; }
log_err(){ echo "[julius-post-image] ERR $*" >&2; }

log "Creating Julius eMMC image: $IMG"

dd if=/dev/zero of="$IMG" bs=1M count="$IMG_SIZE_MB" status=progress

if command -v sgdisk &>/dev/null; then
    sgdisk -Z "$IMG"
    sgdisk \
        -n 1:64M:128M   -t 1:0700 -c 1:"julius-boot" \
        -n 2:128M:640M  -t 2:8300 -c 2:"julius-root" \
        -n 3:640M:1152M -t 3:8300 -c 3:"julius-apps" \
        -n 4:1152M:0    -t 4:8300 -c 4:"julius-data" \
        "$IMG"
    log_ok "GPT partitions created"
elif command -v parted &>/dev/null; then
    parted -s "$IMG" mklabel gpt
    parted -s "$IMG" mkpart julius-boot fat32  64MiB  128MiB
    parted -s "$IMG" mkpart julius-root ext4   128MiB 640MiB
    parted -s "$IMG" mkpart julius-apps ext4   640MiB 1152MiB
    parted -s "$IMG" mkpart julius-data ext4   1152MiB 100%
    log_ok "GPT partitions created"
else
    log_err "Install sgdisk or parted to create partition table"; exit 1
fi

SPL="$BINARIES/u-boot-sunxi-with-spl.bin"
if [ -f "$SPL" ]; then
    dd if="$SPL" of="$IMG" bs=1024 seek=8 conv=notrunc
    log_ok "U-Boot SPL written at offset 8KB"
fi

if command -v kpartx &>/dev/null; then
    LOOP=$(losetup -f --show "$IMG")
    kpartx -av "$LOOP"
    LOOP_BASE=$(basename "$LOOP")

    mkfs.fat -F 32 -n "JUL-BOOT" "/dev/mapper/${LOOP_BASE}p1"
    mkfs.ext4 -L "julius-root"   "/dev/mapper/${LOOP_BASE}p2"
    mkfs.ext4 -L "julius-apps"   "/dev/mapper/${LOOP_BASE}p3"
    mkfs.ext4 -L "julius-data"   "/dev/mapper/${LOOP_BASE}p4"

    MOUNT_BOOT=$(mktemp -d)
    mount "/dev/mapper/${LOOP_BASE}p1" "$MOUNT_BOOT"
    cp "$BINARIES/zImage"                        "$MOUNT_BOOT/" 2>/dev/null || true
    cp "$BINARIES/sun8i-h3-julius.dtb"           "$MOUNT_BOOT/" 2>/dev/null || true
    cp "$BINARIES/julius_initramfs_h3.cpio.gz"   "$MOUNT_BOOT/" 2>/dev/null || true
    umount "$MOUNT_BOOT" && rmdir "$MOUNT_BOOT"

    MOUNT_ROOT=$(mktemp -d)
    mount "/dev/mapper/${LOOP_BASE}p2" "$MOUNT_ROOT"
    rsync -a "$BINARIES/target/" "$MOUNT_ROOT/" 2>/dev/null || true
    umount "$MOUNT_ROOT" && rmdir "$MOUNT_ROOT"

    kpartx -dv "$LOOP"
    losetup -d "$LOOP"
    log_ok "Partitions populated"
fi

log_ok "Julius eMMC image ready: $IMG"
ls -lh "$IMG"
