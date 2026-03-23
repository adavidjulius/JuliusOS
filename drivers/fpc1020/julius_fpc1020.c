// Julius OS - FPC1020 Fingerprint Sensor Driver
// Interface: SPI1 @ 4.8MHz, IRQ PA14, RST PA15
// Exposes /dev/julius_fp for julius_enclave

#include <linux/module.h>
#include <linux/spi/spi.h>
#include <linux/gpio/consumer.h>
#include <linux/interrupt.h>
#include <linux/wait.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/delay.h>
#include <linux/workqueue.h>
#include <linux/mutex.h>

#define DRIVER_NAME       "julius_fpc1020"
#define FPC1020_DEVICE    "julius_fp"
#define FPC1020_SPI_SPEED 4800000

#define FPC1020_REG_HWID       0xFC
#define FPC1020_REG_INT_STATUS 0x18
#define FPC1020_REG_INT_ENABLE 0x1C
#define FPC1020_REG_CAPTURE_SEQ 0x20
#define FPC1020_REG_IMG_RD     0x20
#define FPC1020_REG_SLEEP      0x28

#define FPC1020_INT_FINGER_DOWN 0x01
#define FPC1020_INT_FINGER_UP   0x02
#define FPC1020_INT_IMAGE_RDY   0x04

#define FPC1020_IMG_WIDTH  192
#define FPC1020_IMG_HEIGHT 192
#define FPC1020_IMG_SIZE   (FPC1020_IMG_WIDTH * FPC1020_IMG_HEIGHT)

#define FPC_IOC_MAGIC       'f'
#define FPC_IOC_WAIT_FINGER _IO(FPC_IOC_MAGIC, 1)
#define FPC_IOC_CAPTURE_IMG _IOR(FPC_IOC_MAGIC, 2, u8[FPC1020_IMG_SIZE])
#define FPC_IOC_ENROLL      _IO(FPC_IOC_MAGIC, 3)
#define FPC_IOC_IDENTIFY    _IOR(FPC_IOC_MAGIC, 4, int)
#define FPC_IOC_DELETE_ALL  _IO(FPC_IOC_MAGIC, 5)
#define FPC_IOC_GET_STATUS  _IOR(FPC_IOC_MAGIC, 6, u32)
#define FPC_IOC_SLEEP       _IO(FPC_IOC_MAGIC, 7)
#define FPC_IOC_WAKEUP      _IO(FPC_IOC_MAGIC, 8)

struct julius_fpc {
    struct spi_device   *spi;
    struct miscdevice    misc;
    struct gpio_desc    *irq_gpio;
    struct gpio_desc    *rst_gpio;
    int                  irq;
    struct mutex         lock;
    wait_queue_head_t    wait_q;
    bool                 finger_present;
    bool                 image_ready;
    u8                  *img_buf;
    struct work_struct   irq_work;
};

static int fpc_read_reg(struct julius_fpc *fpc, u8 reg, u8 *val)
{
    u8 tx[2] = {reg | 0x80, 0x00};
    u8 rx[2] = {0, 0};
    struct spi_transfer xfer = {.tx_buf=tx, .rx_buf=rx, .len=2};
    struct spi_message msg;
    int ret;
    spi_message_init(&msg);
    spi_message_add_tail(&xfer, &msg);
    ret = spi_sync(fpc->spi, &msg);
    if (!ret) *val = rx[1];
    return ret;
}

static int fpc_write_reg(struct julius_fpc *fpc, u8 reg, u8 val)
{
    u8 tx[2] = {reg & 0x7F, val};
    return spi_write(fpc->spi, tx, 2);
}

static int fpc_read_hwid(struct julius_fpc *fpc, u16 *hwid)
{
    u8 tx[3] = {FPC1020_REG_HWID | 0x80, 0, 0};
    u8 rx[3] = {0, 0, 0};
    struct spi_transfer xfer = {.tx_buf=tx, .rx_buf=rx, .len=3};
    struct spi_message msg;
    int ret;
    spi_message_init(&msg);
    spi_message_add_tail(&xfer, &msg);
    ret = spi_sync(fpc->spi, &msg);
    if (!ret) *hwid = (rx[1] << 8) | rx[2];
    return ret;
}

static void fpc_hw_reset(struct julius_fpc *fpc)
{
    gpiod_set_value_cansleep(fpc->rst_gpio, 0);
    usleep_range(1000, 2000);
    gpiod_set_value_cansleep(fpc->rst_gpio, 1);
    usleep_range(5000, 6000);
}

static void fpc_irq_work_handler(struct work_struct *work)
{
    struct julius_fpc *fpc = container_of(work, struct julius_fpc, irq_work);
    u8 int_status = 0;
    mutex_lock(&fpc->lock);
    fpc_read_reg(fpc, FPC1020_REG_INT_STATUS, &int_status);
    if (int_status & FPC1020_INT_FINGER_DOWN) fpc->finger_present = true;
    if (int_status & FPC1020_INT_FINGER_UP)   fpc->finger_present = false;
    if (int_status & FPC1020_INT_IMAGE_RDY)   fpc->image_ready = true;
    fpc_write_reg(fpc, FPC1020_REG_INT_STATUS, 0xFF);
    mutex_unlock(&fpc->lock);
    wake_up_interruptible(&fpc->wait_q);
}

static irqreturn_t fpc_irq_handler(int irq, void *data)
{
    struct julius_fpc *fpc = data;
    schedule_work(&fpc->irq_work);
    return IRQ_HANDLED;
}

static int fpc_capture_image(struct julius_fpc *fpc)
{
    int ret;
    u8 tx_cmd = FPC1020_REG_IMG_RD | 0x80;
    struct spi_transfer xfers[2] = {
        {.tx_buf = &tx_cmd, .len = 1},
        {.rx_buf = fpc->img_buf, .len = FPC1020_IMG_SIZE},
    };
    struct spi_message msg;

    ret = fpc_write_reg(fpc, FPC1020_REG_CAPTURE_SEQ, 0x01);
    if (ret) return ret;

    fpc->image_ready = false;
    ret = wait_event_interruptible_timeout(fpc->wait_q,
        fpc->image_ready, msecs_to_jiffies(3000));
    if (ret == 0) return -ETIMEDOUT;
    if (ret < 0)  return ret;

    spi_message_init(&msg);
    spi_message_add_tail(&xfers[0], &msg);
    spi_message_add_tail(&xfers[1], &msg);
    return spi_sync(fpc->spi, &msg);
}

static int fpc_open(struct inode *inode, struct file *file)
{
    struct julius_fpc *fpc = container_of(file->private_data,
                                           struct julius_fpc, misc);
    file->private_data = fpc;
    return 0;
}

static long fpc_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct julius_fpc *fpc = file->private_data;
    int ret = 0;

    switch (cmd) {
    case FPC_IOC_WAIT_FINGER:
        fpc->finger_present = false;
        fpc_write_reg(fpc, FPC1020_REG_INT_ENABLE, FPC1020_INT_FINGER_DOWN);
        ret = wait_event_interruptible(fpc->wait_q, fpc->finger_present);
        break;
    case FPC_IOC_CAPTURE_IMG:
        mutex_lock(&fpc->lock);
        ret = fpc_capture_image(fpc);
        if (!ret && copy_to_user((void __user *)arg, fpc->img_buf, FPC1020_IMG_SIZE))
            ret = -EFAULT;
        mutex_unlock(&fpc->lock);
        break;
    case FPC_IOC_SLEEP:
        fpc_write_reg(fpc, FPC1020_REG_SLEEP, 0x01);
        break;
    case FPC_IOC_WAKEUP:
        fpc_hw_reset(fpc);
        break;
    case FPC_IOC_GET_STATUS: {
        u32 s = fpc->finger_present ? 1 : 0;
        if (copy_to_user((void __user *)arg, &s, sizeof(s))) ret = -EFAULT;
        break;
    }
    default:
        ret = -ENOTTY;
    }
    return ret;
}

static const struct file_operations fpc_fops = {
    .owner          = THIS_MODULE,
    .open           = fpc_open,
    .unlocked_ioctl = fpc_ioctl,
    .llseek         = no_llseek,
};

static int julius_fpc1020_probe(struct spi_device *spi)
{
    struct julius_fpc *fpc;
    u16 hwid = 0;
    int ret;

    fpc = devm_kzalloc(&spi->dev, sizeof(*fpc), GFP_KERNEL);
    if (!fpc) return -ENOMEM;

    fpc->spi = spi;
    mutex_init(&fpc->lock);
    init_waitqueue_head(&fpc->wait_q);
    INIT_WORK(&fpc->irq_work, fpc_irq_work_handler);

    fpc->irq_gpio = devm_gpiod_get(&spi->dev, "irq", GPIOD_IN);
    if (IS_ERR(fpc->irq_gpio)) return PTR_ERR(fpc->irq_gpio);

    fpc->rst_gpio = devm_gpiod_get(&spi->dev, "reset", GPIOD_OUT_HIGH);
    if (IS_ERR(fpc->rst_gpio)) return PTR_ERR(fpc->rst_gpio);

    fpc->img_buf = devm_kzalloc(&spi->dev, FPC1020_IMG_SIZE, GFP_KERNEL);
    if (!fpc->img_buf) return -ENOMEM;

    spi->max_speed_hz = FPC1020_SPI_SPEED;
    spi->bits_per_word = 8;
    spi->mode = SPI_MODE_0;
    ret = spi_setup(spi);
    if (ret) return ret;

    fpc_hw_reset(fpc);

    ret = fpc_read_hwid(fpc, &hwid);
    if (ret) return ret;
    if (hwid != 0x020A && hwid != 0x021A) {
        dev_err(&spi->dev, "Bad FPC1020 HWID: 0x%04X\n", hwid);
        return -ENODEV;
    }
    dev_info(&spi->dev, "FPC1020 HWID: 0x%04X confirmed\n", hwid);

    fpc->irq = gpiod_to_irq(fpc->irq_gpio);
    ret = devm_request_irq(&spi->dev, fpc->irq, fpc_irq_handler,
                            IRQF_TRIGGER_RISING, DRIVER_NAME, fpc);
    if (ret) return ret;

    fpc->misc.minor = MISC_DYNAMIC_MINOR;
    fpc->misc.name  = FPC1020_DEVICE;
    fpc->misc.fops  = &fpc_fops;
    ret = misc_register(&fpc->misc);
    if (ret) return ret;

    spi_set_drvdata(spi, fpc);
    dev_info(&spi->dev, "Julius FP: /dev/%s ready\n", FPC1020_DEVICE);
    return 0;
}

static void julius_fpc1020_remove(struct spi_device *spi)
{
    struct julius_fpc *fpc = spi_get_drvdata(spi);
    cancel_work_sync(&fpc->irq_work);
    misc_deregister(&fpc->misc);
}

static const struct of_device_id julius_fpc1020_of_match[] = {
    { .compatible = "fpc,fpc1020" },
    { }
};
MODULE_DEVICE_TABLE(of, julius_fpc1020_of_match);

static struct spi_driver julius_fpc1020_driver = {
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = julius_fpc1020_of_match,
    },
    .probe  = julius_fpc1020_probe,
    .remove = julius_fpc1020_remove,
};

module_spi_driver(julius_fpc1020_driver);

MODULE_DESCRIPTION("Julius OS FPC1020 fingerprint driver");
MODULE_LICENSE("GPL v2");
MODULE_VERSION("1.4.0");
