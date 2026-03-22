#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/spi/spi.h>
#include <linux/gpio.h>
#include <linux/delay.h>
#include <linux/fb.h>
#include <linux/dma-mapping.h>

#define JULIUS_DISPLAY_WIDTH    320
#define JULIUS_DISPLAY_HEIGHT   480
#define JULIUS_DISPLAY_BPP      16
#define JULIUS_DISPLAY_NAME     "julius_fb"

#define CMD_SWRESET 0x01
#define CMD_SLPOUT  0x11
#define CMD_DISPON  0x29
#define CMD_CASET   0x2A
#define CMD_RASET   0x2B
#define CMD_RAMWR   0x2C
#define CMD_MADCTL  0x36
#define CMD_COLMOD  0x3A

struct julius_display {
    struct spi_device *spi;
    struct fb_info    *info;
    int                gpio_dc;
    int                gpio_rst;
    int                gpio_bl;
    u16               *vmem;
    dma_addr_t         vmem_dma;
};

static int julius_write_cmd(struct julius_display *disp, u8 cmd) {
    gpio_set_value(disp->gpio_dc, 0);
    return spi_write(disp->spi, &cmd, 1);
}

static int julius_write_data(struct julius_display *disp, u8 *data, int len) {
    gpio_set_value(disp->gpio_dc, 1);
    return spi_write(disp->spi, data, len);
}

static void julius_set_window(struct julius_display *disp,
    int x0, int y0, int x1, int y1) {
    u8 buf[4];
    julius_write_cmd(disp, CMD_CASET);
    buf[0]=(x0>>8)&0xFF; buf[1]=x0&0xFF;
    buf[2]=(x1>>8)&0xFF; buf[3]=x1&0xFF;
    julius_write_data(disp, buf, 4);
    julius_write_cmd(disp, CMD_RASET);
    buf[0]=(y0>>8)&0xFF; buf[1]=y0&0xFF;
    buf[2]=(y1>>8)&0xFF; buf[3]=y1&0xFF;
    julius_write_data(disp, buf, 4);
    julius_write_cmd(disp, CMD_RAMWR);
}

static void julius_init_display(struct julius_display *disp) {
    // Hardware reset
    gpio_set_value(disp->gpio_rst, 0);
    msleep(10);
    gpio_set_value(disp->gpio_rst, 1);
    msleep(120);

    julius_write_cmd(disp, CMD_SWRESET);
    msleep(150);
    julius_write_cmd(disp, CMD_SLPOUT);
    msleep(500);

    // Color mode 16bit
    julius_write_cmd(disp, CMD_COLMOD);
    u8 colmod = 0x55;
    julius_write_data(disp, &colmod, 1);

    // Memory access control
    julius_write_cmd(disp, CMD_MADCTL);
    u8 madctl = 0x00;
    julius_write_data(disp, &madctl, 1);

    // Display on
    julius_write_cmd(disp, CMD_DISPON);
    msleep(100);

    // Backlight on
    gpio_set_value(disp->gpio_bl, 1);

    pr_info("Julius Display: initialized %dx%d\n",
        JULIUS_DISPLAY_WIDTH, JULIUS_DISPLAY_HEIGHT);
}

static void julius_update_display(struct julius_display *disp) {
    julius_set_window(disp, 0, 0,
        JULIUS_DISPLAY_WIDTH-1, JULIUS_DISPLAY_HEIGHT-1);
    gpio_set_value(disp->gpio_dc, 1);
    spi_write(disp->spi, disp->vmem,
        JULIUS_DISPLAY_WIDTH * JULIUS_DISPLAY_HEIGHT * 2);
}

static ssize_t julius_fb_write(struct fb_info *info,
    const char __user *buf, size_t count, loff_t *ppos) {
    struct julius_display *disp = info->par;
    ssize_t res = fb_sys_write(info, buf, count, ppos);
    julius_update_display(disp);
    return res;
}

static struct fb_ops julius_fb_ops = {
    .owner        = THIS_MODULE,
    .fb_read      = fb_sys_read,
    .fb_write     = julius_fb_write,
    .fb_fillrect  = sys_fillrect,
    .fb_copyarea  = sys_copyarea,
    .fb_imageblit = sys_imageblit,
};

static int julius_display_probe(struct spi_device *spi) {
    struct julius_display *disp;
    struct fb_info        *info;
    int ret;

    disp = devm_kzalloc(&spi->dev, sizeof(*disp), GFP_KERNEL);
    if (!disp) return -ENOMEM;

    disp->spi      = spi;
    disp->gpio_dc  = 24;
    disp->gpio_rst = 25;
    disp->gpio_bl  = 18;

    // Request GPIOs
    devm_gpio_request_one(&spi->dev, disp->gpio_dc,
        GPIOF_OUT_INIT_LOW, "julius_dc");
    devm_gpio_request_one(&spi->dev, disp->gpio_rst,
        GPIOF_OUT_INIT_HIGH, "julius_rst");
    devm_gpio_request_one(&spi->dev, disp->gpio_bl,
        GPIOF_OUT_INIT_LOW, "julius_bl");

    // Allocate framebuffer
    int vmem_size = JULIUS_DISPLAY_WIDTH *
                    JULIUS_DISPLAY_HEIGHT * 2;
    disp->vmem = dma_alloc_coherent(&spi->dev, vmem_size,
                    &disp->vmem_dma, GFP_KERNEL);
    if (!disp->vmem) return -ENOMEM;

    info = framebuffer_alloc(0, &spi->dev);
    info->screen_base  = (char __iomem *)disp->vmem;
    info->screen_size  = vmem_size;
    info->fbops        = &julius_fb_ops;
    info->fix.smem_len = vmem_size;
    info->var.xres          = JULIUS_DISPLAY_WIDTH;
    info->var.yres          = JULIUS_DISPLAY_HEIGHT;
    info->var.xres_virtual  = JULIUS_DISPLAY_WIDTH;
    info->var.yres_virtual  = JULIUS_DISPLAY_HEIGHT;
    info->var.bits_per_pixel= JULIUS_DISPLAY_BPP;
    info->par = disp;
    disp->info = info;

    ret = register_framebuffer(info);
    if (ret < 0) return ret;

    julius_init_display(disp);
    spi_set_drvdata(spi, disp);

    pr_info("Julius Display: registered as /dev/fb0\n");
    return 0;
}

static int julius_display_remove(struct spi_device *spi) {
    struct julius_display *disp = spi_get_drvdata(spi);
    gpio_set_value(disp->gpio_bl, 0);
    unregister_framebuffer(disp->info);
    framebuffer_release(disp->info);
    pr_info("Julius Display: removed\n");
    return 0;
}

static struct spi_driver julius_display_driver = {
    .driver = {
        .name  = JULIUS_DISPLAY_NAME,
        .owner = THIS_MODULE,
    },
    .probe  = julius_display_probe,
    .remove = julius_display_remove,
};

module_spi_driver(julius_display_driver);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Julius OS");
MODULE_DESCRIPTION("Julius OS Display Driver");
