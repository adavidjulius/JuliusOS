#!/bin/bash
# Julius OS - RTL8723DS WiFi + Bluetooth init
# Called by julius_init during boot: Network phase

set -e

JULIUS_LOG="/var/log/julius_net.log"
RTL_MODULE="rtl8723ds"
RTL_FW_PATH="/lib/firmware/rtlwifi"
BT_UART="/dev/ttyS1"
BT_SPEED="1500000"

log()    { echo "[julius_wifi] $*" | tee -a "$JULIUS_LOG"; }
log_ok() { echo "[julius_wifi] OK $*" | tee -a "$JULIUS_LOG"; }
log_err(){ echo "[julius_wifi] ERR $*" | tee -a "$JULIUS_LOG" >&2; }

check_firmware() {
    [ -f "$RTL_FW_PATH/rtl8723ds_nic.bin" ] || { log_err "WiFi firmware missing"; exit 1; }
    [ -f "$RTL_FW_PATH/rtl8723ds_mp.bin"  ] || { log_err "BT firmware missing";   exit 1; }
    log_ok "Firmware present"
}

load_wifi_module() {
    log "Loading $RTL_MODULE..."
    lsmod | grep -q "$RTL_MODULE" && { log_ok "Already loaded"; return 0; }
    modprobe "$RTL_MODULE" ifname=wlan0 debug=0 rtw_power_mgnt=1 rtw_ips_mode=1
    local tries=0
    while [ $tries -lt 20 ]; do
        ip link show wlan0 &>/dev/null && { log_ok "wlan0 ready"; return 0; }
        sleep 0.5; tries=$((tries+1))
    done
    log_err "wlan0 did not appear"; return 1
}

configure_wlan() {
    ip link set wlan0 up
    local wpa_conf="/etc/julius/wpa_supplicant.conf"
    if [ -f "$wpa_conf" ]; then
        wpa_supplicant -B -i wlan0 -c "$wpa_conf" -P /var/run/wpa_supplicant.pid
        udhcpc -b -i wlan0 -p /var/run/udhcpc.wlan0.pid &
        log_ok "WiFi connecting"
    else
        log "No saved WiFi config — use Julius Settings to connect"
    fi
}

attach_bluetooth() {
    log "Attaching BT on $BT_UART @ $BT_SPEED..."
    if command -v rtk_hciattach &>/dev/null; then
        rtk_hciattach -n -s "$BT_SPEED" "$BT_UART" rtk_h5 &
    else
        hciattach "$BT_UART" rtk_h5 "$BT_SPEED" flow &
    fi
    echo $! > /var/run/julius_bt.pid
    local tries=0
    while [ $tries -lt 20 ]; do
        hciconfig hci0 &>/dev/null 2>&1 && {
            hciconfig hci0 up
            log_ok "hci0 Bluetooth ready"
            return 0
        }
        sleep 0.5; tries=$((tries+1))
    done
    log_err "hci0 did not appear"; return 1
}

report_status() {
    local wifi_ip
    wifi_ip=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    local bt_ok
    bt_ok=$(hciconfig hci0 &>/dev/null 2>&1 && echo "ready" || echo "error")
    echo "{\"wifi_ip\":\"${wifi_ip:-disconnected}\",\"bt\":\"$bt_ok\"}" \
        > /var/run/julius_net_status.json
    log_ok "Status written"
}

main() {
    log "Julius RTL8723DS init starting..."
    mkdir -p /var/run /var/log "$RTL_FW_PATH"
    check_firmware
    load_wifi_module
    configure_wlan
    attach_bluetooth
    report_status
    log_ok "Network init complete"
}

main "$@"
```

---

## `buildroot/configs/julius_h3_defconfig`
```
# Julius OS - Buildroot defconfig for Allwinner H3
# This is the NEW H3 config. Your old julius_defconfig stays as-is for x86 QEMU.

BR2_arm=y
BR2_cortex_a7=y
BR2_ARM_EABI=y
BR2_ARM_FPU_VFPV4=y
BR2_ARM_INSTRUCTIONS_THUMB2=y

BR2_TOOLCHAIN_BUILDROOT_UCLIBC=y
BR2_TOOLCHAIN_BUILDROOT_WCHAR=y
BR2_TOOLCHAIN_BUILDROOT_LOCALE=y
BR2_TOOLCHAIN_GCC_AT_LEAST_8=y

BR2_ENABLE_LTO=y
BR2_OPTIMIZE_2=y
BR2_STRIP_strip=y

BR2_LINUX_KERNEL=y
BR2_LINUX_KERNEL_CUSTOM_VERSION=y
BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.6"
BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG=y
BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE="$(JULIUS_BASE)/kernel/julius_h3_defconfig"
BR2_LINUX_KERNEL_IMAGE_TARGET_NAME="zImage"
BR2_LINUX_KERNEL_DTS_SUPPORT=y
BR2_LINUX_KERNEL_CUSTOM_DTS_PATH="$(JULIUS_BASE)/kernel/sun8i-h3-julius.dts"

BR2_TARGET_UBOOT=y
BR2_TARGET_UBOOT_BUILD_SYSTEM_KCONFIG=y
BR2_TARGET_UBOOT_CUSTOM_VERSION=y
BR2_TARGET_UBOOT_CUSTOM_VERSION_VALUE="2024.01"
BR2_TARGET_UBOOT_BOARD_DEFCONFIG="julius_h3"
BR2_TARGET_UBOOT_FORMAT_CUSTOM=y
BR2_TARGET_UBOOT_FORMAT_CUSTOM_NAME="u-boot-sunxi-with-spl.bin"

BR2_INIT_NONE=y

BR2_TARGET_GENERIC_HOSTNAME="JuliusOS"
BR2_TARGET_GENERIC_ISSUE="Julius OS v1.4"
BR2_TARGET_GENERIC_ROOT_PASSWD=""
BR2_TARGET_GENERIC_GETTY=n
BR2_ROOTFS_POST_BUILD_SCRIPT="$(JULIUS_BASE)/buildroot/board/julius/post-build.sh"
BR2_ROOTFS_POST_IMAGE_SCRIPT="$(JULIUS_BASE)/buildroot/board/julius/post-image.sh"

BR2_TARGET_ROOTFS_EXT2=y
BR2_TARGET_ROOTFS_EXT2_4=y
BR2_TARGET_ROOTFS_EXT2_SIZE="512M"
BR2_TARGET_ROOTFS_EXT2_LABEL="julius_root"

BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PY_PYC=y
BR2_PACKAGE_PYTHON_PYGAME=y
BR2_PACKAGE_PYTHON_REQUESTS=y
BR2_PACKAGE_PYTHON_CRYPTOGRAPHY=y
BR2_PACKAGE_PYTHON_PARAMIKO=y
BR2_PACKAGE_PYTHON_PYSERIAL=y
BR2_PACKAGE_PYTHON_NETIFACES=y

BR2_PACKAGE_LIBSDL2=y
BR2_PACKAGE_LIBSDL2_IMAGE=y
BR2_PACKAGE_LIBSDL2_TTF=y
BR2_PACKAGE_LIBPNG=y
BR2_PACKAGE_LIBJPEG_TURBO=y
BR2_PACKAGE_FREETYPE=y
BR2_PACKAGE_FONTCONFIG=y

BR2_PACKAGE_OPENSSL=y
BR2_PACKAGE_LIBSSL=y
BR2_PACKAGE_CA_CERTIFICATES=y

BR2_PACKAGE_WPA_SUPPLICANT=y
BR2_PACKAGE_WPA_SUPPLICANT_AP_SUPPORT=y
BR2_PACKAGE_WPA_SUPPLICANT_CTRL_IFACE=y
BR2_PACKAGE_DHCP=y
BR2_PACKAGE_BUSYBOX=y
BR2_PACKAGE_IPTABLES=y
BR2_PACKAGE_NFTABLES=y
BR2_PACKAGE_IPROUTE2=y
BR2_PACKAGE_WIRELESS_TOOLS=y
BR2_PACKAGE_IW=y
BR2_PACKAGE_HOSTAPD=y
BR2_PACKAGE_TCPDUMP=y
BR2_PACKAGE_NMAP=y
BR2_PACKAGE_OPENSSH=y

BR2_PACKAGE_BLUEZ5_UTILS=y
BR2_PACKAGE_BLUEZ5_UTILS_CLIENT=y
BR2_PACKAGE_LIBBLUETOOTH=y

BR2_PACKAGE_I2C_TOOLS=y
BR2_PACKAGE_E2FSPROGS=y
BR2_PACKAGE_UTIL_LINUX=y
BR2_PACKAGE_DOSFSTOOLS=y
BR2_PACKAGE_CHRONY=y
