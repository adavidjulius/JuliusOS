#!/bin/bash
# Julius OS - Buildroot post-build.sh
# Replaces your existing post-build.sh — keeps all old logic, adds H3 hardware setup

set -e
TARGET="$1"
JULIUS_BASE="$(cd "$(dirname "$0")/../../.." && pwd)"

log()    { echo "[julius-post-build] $*"; }
log_ok() { echo "[julius-post-build] OK $*"; }

log "Julius post-build starting... TARGET=$TARGET"

# 1. Build and install julius_init PID 1
log "Building julius_init..."
make -C "$JULIUS_BASE/kernel/julius_init" \
    CROSS_COMPILE=arm-linux-gnueabihf- \
    CC=arm-linux-gnueabihf-gcc
install -m 755 "$JULIUS_BASE/kernel/julius_init/julius_init" "$TARGET/sbin/julius_init"
ln -sf /sbin/julius_init "$TARGET/sbin/init" 2>/dev/null || true
log_ok "julius_init installed"

# 2. Build and install C backend services
log "Building C services..."
make -C "$JULIUS_BASE/services" \
    CROSS_COMPILE=arm-linux-gnueabihf- \
    CC=arm-linux-gnueabihf-gcc \
    DESTDIR="$TARGET" install
log_ok "C services installed"

# 3. Install Python UI
log "Installing Python UI..."
mkdir -p "$TARGET/opt/julius"
rsync -a "$JULIUS_BASE/src/" "$TARGET/opt/julius/src/"
log_ok "Python UI installed"

# 4. Install driver scripts
mkdir -p "$TARGET/etc/julius"
install -m 755 "$JULIUS_BASE/drivers/rtl8723ds/julius_rtl8723ds_init.sh" \
    "$TARGET/etc/julius/rtl8723ds_init.sh"
log_ok "Driver scripts installed"

# 5. RTL8723DS firmware
mkdir -p "$TARGET/lib/firmware/rtlwifi"
FIRMWARE_SRC="$JULIUS_BASE/firmware/rtl8723ds"
if [ -d "$FIRMWARE_SRC" ]; then
    cp "$FIRMWARE_SRC"/*.bin "$TARGET/lib/firmware/rtlwifi/"
    log_ok "RTL8723DS firmware installed"
else
    log "WARNING: firmware/rtl8723ds/ not found"
    log "  Download from: https://github.com/lwfinger/rtl8723ds/tree/master/firmware"
fi

# 6. Directory structure
mkdir -p "$TARGET/var/run" "$TARGET/var/log" "$TARGET/tmp" "$TARGET/data"

# 7. Default settings
cat > "$TARGET/etc/julius/julius_settings.json" << 'SETTINGS'
{
  "wifi": false,
  "bluetooth": false,
  "brightness": 75,
  "volume": 50,
  "airplane": false,
  "dark_mode": true,
  "notifications": true,
  "fingerprint": true,
  "ota_enabled": true,
  "hotspot": false,
  "admin_device": false,
  "device_name": "Julius",
  "version": "1.4.0"
}
SETTINGS
log_ok "Default settings written"

# 8. Startup script
cat > "$TARGET/etc/julius/julius_start.sh" << 'STARTUP'
#!/bin/sh
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0
export DISPLAY=""
cd /opt/julius/src
exec python3 julius_ui.py
STARTUP
chmod 755 "$TARGET/etc/julius/julius_start.sh"
log_ok "Startup script written"

# 9. fstab
cat > "$TARGET/etc/fstab" << 'FSTAB'
/dev/root          /           ext4   ro,relatime          0 1
/dev/mmcblk2p3     /opt/julius ext4   rw,relatime,noatime  0 2
/dev/mmcblk2p4     /data       ext4   rw,relatime,noatime  0 3
tmpfs              /tmp        tmpfs  defaults,size=64M    0 0
tmpfs              /var/run    tmpfs  defaults,size=8M     0 0
proc               /proc       proc   defaults             0 0
sysfs              /sys        sysfs  defaults             0 0
devtmpfs           /dev        devtmpfs defaults           0 0
FSTAB
log_ok "fstab written"

log_ok "Julius post-build complete"
