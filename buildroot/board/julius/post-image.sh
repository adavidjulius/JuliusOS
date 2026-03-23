#!/bin/bash
# Julius OS Post-Image Script
# Creates final bootable image

set -e
BINARIES_DIR="$1"
JULIUS_VERSION="1.3"

echo "[Julius Image] Creating bootable image..."

# Create boot partition layout
cat > $BINARIES_DIR/boot.cmd << EOF
setenv bootargs console=ttyS0,115200 root=/dev/mmcblk0p2 rootfstype=ext4 rw init=/usr/bin/julius_init quiet splash
load mmc 0:1 \${kernel_addr_r} zImage
load mmc 0:1 \${fdt_addr_r} julius.dtb
load mmc 0:1 \${ramdisk_addr_r} initramfs.cpio.gz
bootz \${kernel_addr_r} \${ramdisk_addr_r}:\${filesize} \${fdt_addr_r}
EOF

# Compile boot script
if command -v mkimage &>/dev/null; then
    mkimage -C none -A arm -T script \
        -d $BINARIES_DIR/boot.cmd \
        $BINARIES_DIR/boot.scr
    echo "[Julius Image] Boot script compiled"
fi

# Create SD card image
if command -v dd &>/dev/null; then
    echo "[Julius Image] Creating SD image..."
    dd if=/dev/zero \
       of=$BINARIES_DIR/julius_os.img \
       bs=1M count=2048 status=progress

    # Partition table
    cat > /tmp/julius_parts.sfdisk << EOF
label: dos
device: $BINARIES_DIR/julius_os.img
unit: sectors
1 : start=2048, size=131072, type=c, bootable
2 : start=133120, size=3964928, type=83
EOF
    sfdisk $BINARIES_DIR/julius_os.img \
        < /tmp/julius_parts.sfdisk
    echo "[Julius Image] SD image created"
fi

echo "[Julius Image] Julius OS v$JULIUS_VERSION image ready!"
echo "[Julius Image] Flash with:"
echo "  sudo dd if=julius_os.img of=/dev/sdX bs=4M"
