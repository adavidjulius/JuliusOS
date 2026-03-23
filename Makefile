# Julius OS v1.4 - Master Makefile
# Run from: ~/Desktop/JuliusOS/

JULIUS_VERSION := 1.4.0
JULIUS_BASE    := $(shell pwd)
JOBS           := $(shell nproc 2>/dev/null || sysctl -n hw.logicalcpu)

export JULIUS_BASE

.PHONY: all kernel uboot drivers buildroot image flash qemu qemu-arm run-ui clean help

all: kernel drivers buildroot image
	@echo "Julius OS v$(JULIUS_VERSION) build complete"
	@echo "Flash: make flash"

kernel:
	$(MAKE) -f kernel/Makefile.h3 all -j$(JOBS)

kernel-menu:
	$(MAKE) -f kernel/Makefile.h3 menuconfig

uboot:
	$(MAKE) -f uboot/Makefile.uboot all -j$(JOBS)

drivers: kernel
	$(MAKE) -C drivers/st7796 \
		KERNEL_DIR=$(JULIUS_BASE)/kernel/linux-6.6 \
		CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm modules
	$(MAKE) -C drivers/fpc1020 \
		KERNEL_DIR=$(JULIUS_BASE)/kernel/linux-6.6 \
		CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm modules

buildroot:
	@if [ ! -d "buildroot/buildroot-src" ]; then \
		curl -L https://buildroot.org/downloads/buildroot-2024.02.tar.gz \
			-o /tmp/buildroot.tar.gz; \
		mkdir -p buildroot/buildroot-src; \
		tar -xf /tmp/buildroot.tar.gz -C buildroot/buildroot-src --strip-components=1; \
	fi
	cp buildroot/configs/julius_h3_defconfig buildroot/buildroot-src/configs/
	$(MAKE) -C buildroot/buildroot-src julius_h3_defconfig
	$(MAKE) -C buildroot/buildroot-src -j$(JOBS)

image:
	bash buildroot/board/julius/post-image.sh buildroot/buildroot-src/output/images/

flash:
	bash tools/flash.sh

qemu:
	qemu-system-x86_64 \
		-kernel $(HOME)/Desktop/JuliusOS/bzImage \
		-initrd $(HOME)/Desktop/JuliusOS/julius_initramfs_new.cpio.gz \
		-append "console=ttyS0 root=/dev/ram0 rw init=/init quiet" \
		-nographic -m 256M -no-reboot

qemu-arm:
	qemu-system-arm \
		-M orangepi-pc \
		-kernel buildroot/buildroot-src/output/images/zImage \
		-dtb buildroot/buildroot-src/output/images/sun8i-h3-julius.dtb \
		-drive file=buildroot/buildroot-src/output/images/julius_emmc.img,if=sd \
		-append "console=ttyS0,115200 root=/dev/mmcblk0p2 rootfstype=ext4 rw rootwait" \
		-nographic -m 512M

run-ui:
	cd src && python3 julius_ui.py

clean:
	$(MAKE) -f kernel/Makefile.h3 clean
	$(MAKE) -C services clean

help:
	@echo "Julius OS v$(JULIUS_VERSION)"
	@echo "  make all        Build kernel + drivers + rootfs + image"
	@echo "  make kernel     Cross-compile Linux 6.6 for H3"
	@echo "  make uboot      Build U-Boot"
	@echo "  make drivers    Build ST7796 + FPC1020 modules"
	@echo "  make buildroot  Build full rootfs"
	@echo "  make image      Create julius_emmc.img"
	@echo "  make flash      Flash to device"
	@echo "  make qemu       Boot in QEMU (x86)"
	@echo "  make qemu-arm   Boot in QEMU ARM"
	@echo "  make run-ui     Run UI on macOS"
