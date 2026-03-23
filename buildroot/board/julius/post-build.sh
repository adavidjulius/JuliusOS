#!/bin/bash
# Julius OS Post-Build Script
# Runs after buildroot builds the rootfs

set -e
ROOTFS="$1"
JULIUS_VERSION="1.3"

echo "[Julius Build] Post-build starting..."

# Create Julius OS directory structure
mkdir -p $ROOTFS/usr/julius/src
mkdir -p $ROOTFS/usr/julius/apps
mkdir -p $ROOTFS/etc/julius
mkdir -p $ROOTFS/var/julius
mkdir -p $ROOTFS/var/log
mkdir -p $ROOTFS/var/run

# Copy Julius OS Python UI
cp -r $BR2_EXTERNAL_JULIUS_PATH/src/* \
    $ROOTFS/usr/julius/src/

# Copy compiled services
for svc in \
    julius_init julius_enclave julius_pm julius_mm \
    julius_ipc julius_keychain julius_audit julius_health \
    julius_push julius_sync julius_net julius_sandbox \
    julius_permissions julius_wifi julius_bt julius_power; do
    if [ -f "$BR2_EXTERNAL_JULIUS_PATH/services/$svc/$svc" ]; then
        install -m 755 \
            "$BR2_EXTERNAL_JULIUS_PATH/services/$svc/$svc" \
            "$ROOTFS/usr/bin/$svc"
        echo "[Julius Build] Installed $svc"
    fi
done

# Set julius_init as PID 1
ln -sf /usr/bin/julius_init $ROOTFS/sbin/init

# Create default config files
cat > $ROOTFS/etc/julius/julius.conf << EOF
version=$JULIUS_VERSION
device_name=Julius
ota_enabled=1
fingerprint=1
EOF
chmod 600 $ROOTFS/etc/julius/julius.conf

# Create inittab for fallback
cat > $ROOTFS/etc/inittab << EOF
::sysinit:/usr/bin/julius_init
::respawn:/bin/sh
EOF

# Set hostname
echo "julius" > $ROOTFS/etc/hostname

# Create motd
cat > $ROOTFS/etc/motd << EOF

  Julius OS v$JULIUS_VERSION
  Built for control.

EOF

# Set permissions
chmod 755 $ROOTFS/usr/julius
chmod 755 $ROOTFS/usr/julius/src
find $ROOTFS/usr/julius/src -name "*.py" \
    -exec chmod 644 {} \;

echo "[Julius Build] Post-build complete!"
echo "[Julius Build] Julius OS v$JULIUS_VERSION ready"
