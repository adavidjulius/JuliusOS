// Julius OS - ST7796 SPI TFT Framebuffer Driver
// Display: 320x480 IPS, 16bpp, 60fps
// Interface: SPI0 @ 50MHz

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/spi/spi.h>
#include <linux/gpio/consumer.h>
#include <linux/delay.h>
#include <linux/fb.h>
#include <linux/dma-mapping.h>
#include <linux/of.h>
#include <linux/workqueue.h>
#include <linux/spinlock.h>

#define DRIVER_NAME      "julius_st7796"
#define JULIUS_FB_WIDTH  320
#define JULIUS_FB_HEIGHT 480
#define JULIUS_BPP       16
#define JULIUS_SPI_SPEED 50000000

#define ST7796_SWRESET  0x01
#define ST7796_SLPOUT   0x11
#define ST7796_NORON    0x13
#define ST7796_DISPON   0x29
#define ST7796_DISPOFF  0x28
#define ST7796_SLPIN    0x10
#define ST7796_CASET    0x2A
#define ST7796_RASET    0x2B
#define ST7796_RAMWR    0x2C
#define ST7796_MADCTL   0x36
#define ST7796_COLMOD   0x3A
#define ST7796_PGAMCTRL 0xE0
#define ST7796_NGAMCTRL 0xE1
#define ST7796_PCS1     0xC0
#define ST7796_PCS2     0xC1
#define ST7796_VCOM1    0xC5
#define ST7796_FRMCTR1  0xB1
#define ST7796_DFC      0xB6
#define ST7796_EM       0xB7

#define MADCTL_MX  0x40
#define MADCTL_BGR 0x08

struct julius_fb {
    struct spi_device      *spi;
    struct fb_info         *info;
    struct gpio_desc       *dc_gpio;
    struct gpio_desc       *rst_gpio;
    u8                     *vmem;
    dma_addr_t              vmem_dma;
    struct work_struct      work;
    spinlock_t              lock;
    bool                    enabled;
};

static inline void julius_dc_cmd(struct julius_fb *fb)
{
    gpiod_set_value_cansleep(fb->dc_gpio, 0);
}

static inline void julius_dc_data(struct julius_fb *fb)
{
    gpiod_set_value_cansleep(fb->dc_gpio, 1);
}

static int julius_write_cmd(struct julius_fb *fb, u8 cmd)
{
    julius_dc_cmd(fb);
    return spi_write(fb->spi, &cmd, 1);
}

static int julius_write_data(struct julius_fb *fb, const u8 *data, size_t len)
{
    julius_dc_data(fb);
    return spi_write(fb->spi, data, len);
}

static int julius_write_byte(struct julius_fb *fb, u8 data)
{
    return julius_write_data(fb, &data, 1);
}

static void julius_hw_reset(struct julius_fb *fb)
{
    gpiod_set_value_cansleep(fb->rst_gpio, 1);
    msleep(10);
    gpiod_set_value_cansleep(fb->rst_gpio, 0);
    msleep(20);
    gpiod_set_value_cansleep(fb->rst_gpio, 1);
    msleep(150);
}

static int julius_init_display(struct julius_fb *fb)
{
    julius_hw_reset(fb);

    julius_write_cmd(fb, ST7796_SWRESET);
    msleep(120);
    julius_write_cmd(fb, ST7796_SLPOUT);
    msleep(120);

    julius_write_cmd(fb, ST7796_COLMOD);
    julius_write_byte(fb, 0x55);

    julius_write_cmd(fb, ST7796_MADCTL);
    julius_write_byte(fb, MADCTL_MX | MADCTL_BGR);

    julius_write_cmd(fb, ST7796_FRMCTR1);
    julius_write_byte(fb, 0xA0);
    julius_write_byte(fb, 0x11);

    julius_write_cmd(fb, ST7796_DFC);
    julius_write_byte(fb, 0x02);
    julius_write_byte(fb, 0x02);

    julius_write_cmd(fb, ST7796_EM);
    julius_write_byte(fb, 0xC6);

    julius_write_cmd(fb, ST7796_PCS1);
    julius_write_byte(fb, 0x17);
    julius_write_byte(fb, 0x15);

    julius_write_cmd(fb, ST7796_PCS2);
    julius_write_byte(fb, 0x41);

    julius_write_cmd(fb, ST7796_VCOM1);
    julius_write_byte(fb, 0x00);
    julius_write_byte(fb, 0x12);
    julius_write_byte(fb, 0x80);

    julius_write_cmd(fb, ST7796_PGAMCTRL);
    {
        u8 g[] = {0xF0,0x00,0x07,0x10,0x09,0x17,0x26,0x4B,0x65,0x43,0x07,0x19,0x19,0x27,0x33};
        julius_write_data(fb, g, sizeof(g));
    }

    julius_write_cmd(fb, ST7796_NGAMCTRL);
    {
        u8 g[] = {0xF0,0x06,0x0F,0x03,0x10,0x0E,0x30,0x47,0x43,0x03,0x0E,0x0E,0x22,0x27};
        julius_write_data(fb, g, sizeof(g));
    }

    julius_write_cmd(fb, ST7796_NORON);
    msleep(10);
    julius_write_cmd(fb, ST7796_DISPON);
    msleep(25);

    dev_info(&fb->spi->dev, "Julius ST7796 320x480 initialized\n");
    return 0;
}

static void julius_set_window(struct julius_fb *fb,
                               u16 x0, u16 y0, u16 x1, u16 y1)
{
    u8 caset[] = {x0>>8, x0&0xFF, x1>>8, x1&0xFF};
    u8 raset[] = {y0>>8, y0&0xFF, y1>>8, y1&0xFF};
    julius_write_cmd(fb, ST7796_CASET);
    julius_write_data(fb, caset, 4);
    julius_write_cmd(fb, ST7796_RASET);
    julius_write_data(fb, raset, 4);
    julius_write_cmd(fb, ST7796_RAMWR);
}

static void julius_flush(struct julius_fb *fb)
{
    struct spi_transfer xfer = {
        .tx_buf   = fb->vmem,
        .len      = JULIUS_FB_WIDTH * JULIUS_FB_HEIGHT * 2,
        .speed_hz = JULIUS_SPI_SPEED,
    };
    struct spi_message msg;

    julius_set_window(fb, 0, 0, JULIUS_FB_WIDTH-1, JULIUS_FB_HEIGHT-1);
    julius_dc_data(fb);
    spi_message_init(&msg);
    spi_message_add_tail(&xfer, &msg);
    spi_sync(fb->spi, &msg);
}

static void julius_deferred_work(struct work_struct *work)
{
    struct julius_fb *fb = container_of(work, struct julius_fb, work);
    julius_flush(fb);
}

static void julius_fb_fillrect(struct fb_info *info, const struct fb_fillrect *rect)
{
    struct julius_fb *fb = info->par;
    sys_fillrect(info, rect);
    schedule_work(&fb->work);
}

static void julius_fb_copyarea(struct fb_info *info, const struct fb_copyarea *area)
{
    struct julius_fb *fb = info->par;
    sys_copyarea(info, area);
    schedule_work(&fb->work);
}

static void julius_fb_imageblit(struct fb_info *info, const struct fb_image *image)
{
    struct julius_fb *fb = info->par;
    sys_imageblit(info, image);
    schedule_work(&fb->work);
}

static ssize_t julius_fb_write(struct fb_info *info, const char __user *buf,
                                size_t count, loff_t *ppos)
{
    struct julius_fb *fb = info->par;
    ssize_t ret = fb_sys_write(info, buf, count, ppos);
    if (ret > 0)
        schedule_work(&fb->work);
    return ret;
}

static struct fb_ops julius_fb_ops = {
    .owner        = THIS_MODULE,
    .fb_read      = fb_sys_read,
    .fb_write     = julius_fb_write,
    .fb_fillrect  = julius_fb_fillrect,
    .fb_copyarea  = julius_fb_copyarea,
    .fb_imageblit = julius_fb_imageblit,
};

static int julius_st7796_probe(struct spi_device *spi)
{
    struct julius_fb *jfb;
    struct fb_info *info;
    int ret;
    u32 vmem_size = JULIUS_FB_WIDTH * JULIUS_FB_HEIGHT * (JULIUS_BPP / 8);

    jfb = devm_kzalloc(&spi->dev, sizeof(*jfb), GFP_KERNEL);
    if (!jfb)
        return -ENOMEM;

    jfb->spi = spi;
    spin_lock_init(&jfb->lock);
    INIT_WORK(&jfb->work, julius_deferred_work);

    jfb->dc_gpio = devm_gpiod_get(&spi->dev, "dc", GPIOD_OUT_LOW);
    if (IS_ERR(jfb->dc_gpio))
        return PTR_ERR(jfb->dc_gpio);

    jfb->rst_gpio = devm_gpiod_get(&spi->dev, "reset", GPIOD_OUT_HIGH);
    if (IS_ERR(jfb->rst_gpio))
        return PTR_ERR(jfb->rst_gpio);

    jfb->vmem = dma_alloc_coherent(&spi->dev, vmem_size, &jfb->vmem_dma, GFP_KERNEL);
    if (!jfb->vmem)
        return -ENOMEM;
    memset(jfb->vmem, 0, vmem_size);

    info = framebuffer_alloc(0, &spi->dev);
    if (!info) { ret = -ENOMEM; goto err_free_vmem; }

    jfb->info = info;
    info->par = jfb;
    info->fbops = &julius_fb_ops;
    info->flags = FBINFO_DEFAULT | FBINFO_VIRTFB;

    strscpy(info->fix.id, "julius_st7796", sizeof(info->fix.id));
    info->fix.type       = FB_TYPE_PACKED_PIXELS;
    info->fix.visual     = FB_VISUAL_TRUECOLOR;
    info->fix.line_length = JULIUS_FB_WIDTH * (JULIUS_BPP / 8);
    info->fix.smem_start = jfb->vmem_dma;
    info->fix.smem_len   = vmem_size;

    info->var.xres = info->var.xres_virtual = JULIUS_FB_WIDTH;
    info->var.yres = info->var.yres_virtual = JULIUS_FB_HEIGHT;
    info->var.bits_per_pixel = JULIUS_BPP;
    info->var.red.offset   = 11; info->var.red.length   = 5;
    info->var.green.offset =  5; info->var.green.length = 6;
    info->var.blue.offset  =  0; info->var.blue.length  = 5;
    info->var.activate = FB_ACTIVATE_NOW;
    info->var.width    = 40;
    info->var.height   = 60;

    info->screen_base = (char __iomem *)jfb->vmem;
    info->screen_size = vmem_size;

    ret = fb_alloc_cmap(&info->cmap, 256, 0);
    if (ret) goto err_free_fb;

    spi->max_speed_hz = JULIUS_SPI_SPEED;
    spi->bits_per_word = 8;
    spi->mode = SPI_MODE_0;
    ret = spi_setup(spi);
    if (ret) goto err_free_cmap;

    ret = julius_init_display(jfb);
    if (ret) goto err_free_cmap;

    ret = register_framebuffer(info);
    if (ret) goto err_free_cmap;

    spi_set_drvdata(spi, jfb);
    jfb->enabled = true;
    dev_info(&spi->dev, "Julius display: fb%d %dx%d@%dbpp\n",
             info->node, JULIUS_FB_WIDTH, JULIUS_FB_HEIGHT, JULIUS_BPP);
    return 0;

err_free_cmap:
    fb_dealloc_cmap(&info->cmap);
err_free_fb:
    framebuffer_release(info);
err_free_vmem:
    dma_free_coherent(&spi->dev, vmem_size, jfb->vmem, jfb->vmem_dma);
    return ret;
}

static void julius_st7796_remove(struct spi_device *spi)
{
    struct julius_fb *jfb = spi_get_drvdata(spi);
    u32 vmem_size = JULIUS_FB_WIDTH * JULIUS_FB_HEIGHT * (JULIUS_BPP / 8);
    cancel_work_sync(&jfb->work);
    julius_write_cmd(jfb, ST7796_DISPOFF);
    julius_write_cmd(jfb, ST7796_SLPIN);
    unregister_framebuffer(jfb->info);
    fb_dealloc_cmap(&jfb->info->cmap);
    framebuffer_release(jfb->info);
    dma_free_coherent(&spi->dev, vmem_size, jfb->vmem, jfb->vmem_dma);
}

static int julius_st7796_suspend(struct device *dev)
{
    struct julius_fb *jfb = spi_get_drvdata(to_spi_device(dev));
    cancel_work_sync(&jfb->work);
    julius_write_cmd(jfb, ST7796_DISPOFF);
    julius_write_cmd(jfb, ST7796_SLPIN);
    return 0;
}

static int julius_st7796_resume(struct device *dev)
{
    struct julius_fb *jfb = spi_get_drvdata(to_spi_device(dev));
    julius_write_cmd(jfb, ST7796_SLPOUT);
    msleep(120);
    julius_write_cmd(jfb, ST7796_DISPON);
    julius_flush(jfb);
    return 0;
}

static DEFINE_SIMPLE_DEV_PM_OPS(julius_pm_ops,
    julius_st7796_suspend, julius_st7796_resume);

static const struct of_device_id julius_st7796_of_match[] = {
    { .compatible = "julius,st7796" },
    { .compatible = "sitronix,st7796" },
    { }
};
MODULE_DEVICE_TABLE(of, julius_st7796_of_match);

static struct spi_driver julius_st7796_driver = {
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = julius_st7796_of_match,
        .pm             = &julius_pm_ops,
    },
    .probe  = julius_st7796_probe,
    .remove = julius_st7796_remove,
};

module_spi_driver(julius_st7796_driver);

MODULE_DESCRIPTION("Julius OS ST7796 320x480 SPI framebuffer driver");
MODULE_LICENSE("GPL v2");
MODULE_VERSION("1.4.0");
