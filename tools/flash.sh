#!/bin/bash
# Julius OS - tools/flash.sh
# Flash Julius OS to device eMMC from macOS M4

set -e
JULIUS_BASE="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_OUT="$JULIUS_BASE/buildroot/buildroot-src/output/images"
JULIUS_IMG="$BUILD_OUT/julius_emmc.img"
JULIUS_VERSION="1.4.0"

log()     { echo "[flash] $*"; }
log_warn(){ echo "[flash] WARN $*"; }
log_err() { echo "[flash] ERR $*" >&2; }

check_img() {
    if [ ! -f "$JULIUS_IMG" ]; then
        log_err "Image not found: $JULIUS_IMG"
        log_err "Run: make image"
        exit 1
    fi
    log "Image: $JULIUS_IMG ($(du -h "$JULIUS_IMG" | cut -f1))"
}

flash_via_fel() {
    command -v sunxi-fel &>/dev/null || { log_warn "sunxi-fel not found: brew install sunxi-tools"; return 1; }
    sunxi-fel version 2>/dev/null || { log_warn "No device in FEL mode"; return 1; }
    SPL="$BUILD_OUT/u-boot-sunxi-with-spl.bin"
    sunxi-fel -d spiflash-write 0 "$SPL"
    log "Writing image..."
    sunxi-fel -d write 0x40000000 "$JULIUS_IMG"
    sunxi-fel -d exe 0x40000000
    log "Done — device will flash eMMC and reboot"
}

flash_via_sd() {
    diskutil list | grep -E "external|disk[0-9]" | head -20
    echo "Enter SD card disk (e.g. disk2):"
    read -r DISK
    [ -z "$DISK" ] && { log_err "No disk specified"; return 1; }
    log_warn "THIS WILL ERASE /dev/$DISK — type 'yes' to confirm:"
    read -r CONFIRM
    [ "$CONFIRM" != "yes" ] && { log "Aborted"; return 1; }
    diskutil unmountDisk "/dev/$DISK"
    sudo dd if="$JULIUS_IMG" of="/dev/r$DISK" bs=4m status=progress
    sync
    diskutil eject "/dev/$DISK"
    log "SD ready — insert into Julius, it will auto-flash eMMC on first boot"
}

flash_kernel_only() {
    log "Kernel-only update via USB gadget..."
    SPL="$BUILD_OUT/u-boot-sunxi-with-spl.bin"
    EMMC_DEV=$(ls /dev/disk* 2>/dev/null | head -1)
    [ -z "$EMMC_DEV" ] && { log_err "Device not found"; return 1; }
    sudo dd if="$SPL" of="$EMMC_DEV" bs=1024 seek=8 conv=notrunc
    MOUNT=$(mktemp -d)
    sudo mount "${EMMC_DEV}s1" "$MOUNT"
    sudo cp "$BUILD_OUT/zImage"              "$MOUNT/"
    sudo cp "$BUILD_OUT/sun8i-h3-julius.dtb" "$MOUNT/"
    sudo umount "$MOUNT" && rmdir "$MOUNT"
    log "Kernel updated — reboot device"
}

flash_via_ota() {
    ADMIN_KEY="$HOME/.julius/admin.key"
    [ -f "$ADMIN_KEY" ] || { log_err "Admin key not found: $ADMIN_KEY"; return 1; }
    echo "Julius device IP:"
    read -r DEVICE_IP
    [ -z "$DEVICE_IP" ] && { log_err "No IP"; return 1; }
    OTA_PKG="/tmp/julius_ota_$JULIUS_VERSION.tar.gz"
    tar -czf "$OTA_PKG" -C "$BUILD_OUT" zImage sun8i-h3-julius.dtb
    HASH=$(sha256sum "$OTA_PKG" | awk '{print $1}')
    SIG=$(echo "$HASH" | openssl dgst -sha256 -sign "$ADMIN_KEY" | base64)
    curl -X POST "http://$DEVICE_IP:9876/ota/upload" \
        -H "X-Julius-Admin-Sig: $SIG" \
        -H "X-Julius-Version: $JULIUS_VERSION" \
        -F "package=@$OTA_PKG" \
        --connect-timeout 10 --max-time 120
    log "OTA delivered — device will verify, apply, reboot"
}

main() {
    check_img
    echo ""
    echo "Julius OS v$JULIUS_VERSION - Flash Tool"
    echo "1) sunxi-fel    (FEL mode, USB cable)"
    echo "2) SD card      (burn SD, device flashes eMMC on boot)"
    echo "3) Kernel only  (USB gadget, kernel update only)"
    echo "4) OTA wireless (admin key + WiFi)"
    echo "q) Quit"
    echo -n "Choice: "
    read -r CHOICE
    case "$CHOICE" in
        1) flash_via_fel ;;
        2) flash_via_sd ;;
        3) flash_kernel_only ;;
        4) flash_via_ota ;;
        q) exit 0 ;;
        *) log_err "Invalid"; exit 1 ;;
    esac
}

main "$@"
