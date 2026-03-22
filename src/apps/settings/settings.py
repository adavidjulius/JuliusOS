import pygame
import json
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (150, 150, 150)
ON_COL = (0, 255, 100)

SETTINGS_FILE = "julius_settings.json"

DEFAULT = {
    "brightness": 100,
    "wifi"      : True,
    "bluetooth" : True,
    "version"   : "Julius OS v0.1",
    "device"    : "Julius Gadget"
}

class Settings:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.config   = self.load()
        self.selected = 0
        self.items    = list(self.config.items())

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        return DEFAULT.copy()

    def save(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.config, f)

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Settings", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        self.items = list(self.config.items())
        y = 32
        for i, (key, val) in enumerate(self.items):
            color   = ON_COL if i == self.selected else TEXT
            display = f"{key:<12} {'ON' if val else 'OFF'}" if isinstance(val, bool) else f"{key:<12} {val}"
            label   = self.font.render(display, True, color)
            self.screen.blit(label, (8, y))
            y += 18
        hint = self.font.render("↑↓ navigate  ENTER toggle", True, ACCENT)
        self.screen.blit(hint, (8, 225))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key == pygame.K_RETURN:
                key, val = self.items[self.selected]
                if isinstance(val, bool):
                    self.config[key] = not val
                    self.save()
```

---

### `buildroot/configs/julius_defconfig`
```
BR2_arm=y
BR2_cortex_a55=y
BR2_ARM_FPU_NEON_FP_ARMV8=y
BR2_TOOLCHAIN_BUILDROOT_GLIBC=y
BR2_TOOLCHAIN_BUILDROOT_CXX=y
BR2_TARGET_GENERIC_HOSTNAME="julius"
BR2_TARGET_GENERIC_ISSUE="Julius OS v0.1"
BR2_INIT_SYSTEMD=y
BR2_TARGET_LOCALTIME="Asia/Kolkata"
BR2_TARGET_GENERIC_ROOT_PASSWD="julius"
BR2_LINUX_KERNEL=y
BR2_LINUX_KERNEL_LATEST_VERSION=y
BR2_LINUX_KERNEL_USE_ARCH_DEFAULT_CONFIG=y
BR2_TARGET_ROOTFS_EXT2=y
BR2_TARGET_ROOTFS_EXT2_4=y
BR2_TARGET_ROOTFS_EXT2_SIZE="512M"
BR2_TARGET_UBOOT=y
BR2_TARGET_UBOOT_BOARD_DEFCONFIG="julius"
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_FBDEV=y
BR2_PACKAGE_PYGAME=y
BR2_PACKAGE_PYTHON3=y
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
BR2_ROOTFS_OVERLAY="board/julius/rootfs-overlay"
BR2_ROOTFS_POST_BUILD_SCRIPT="board/julius/post-build.sh"
