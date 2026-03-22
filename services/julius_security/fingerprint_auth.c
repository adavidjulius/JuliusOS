#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <openssl/sha.h>

#define FP_DEVICE    "/dev/spidev0.0"
#define FP_TEMPLATE  "/etc/julius/fingerprint.template"
#define FP_SPI_SPEED 1000000
#define FP_TIMEOUT   10

typedef struct {
    uint8_t  data[512];
    uint32_t size;
    uint8_t  hash[32];
} FPTemplate;

static int fp_fd = -1;

int fp_init(void) {
    fp_fd = open(FP_DEVICE, O_RDWR);
    if (fp_fd < 0) {
        perror("[FP] open");
        return -1;
    }
    uint32_t speed = FP_SPI_SPEED;
    ioctl(fp_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
    printf("[FP] Fingerprint sensor initialized\n");
    return 0;
}

int fp_read_raw(uint8_t *buf, int len) {
    if (fp_fd < 0) return -1;
    return read(fp_fd, buf, len);
}

void fp_hash(const uint8_t *data, int len, uint8_t *out) {
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, data, len);
    SHA256_Final(out, &ctx);
}

int fp_enroll(void) {
    printf("[FP] Place finger on sensor...\n");
    uint8_t    raw[512];
    FPTemplate tpl;
    memset(&tpl, 0, sizeof(tpl));

    // Read 3 samples for accuracy
    for (int i = 0; i < 3; i++) {
        int n = fp_read_raw(raw, sizeof(raw));
        if (n <= 0) {
            printf("[FP] Read failed\n");
            return -1;
        }
        for (int j = 0; j < n; j++)
            tpl.data[j] += raw[j] / 3;
        printf("[FP] Sample %d/3 captured\n", i+1);
        sleep(1);
    }

    tpl.size = sizeof(tpl.data);
    fp_hash(tpl.data, tpl.size, tpl.hash);

    FILE *f = fopen(FP_TEMPLATE, "wb");
    if (!f) {
        perror("[FP] template write");
        return -1;
    }
    fwrite(&tpl, sizeof(tpl), 1, f);
    fclose(f);

    printf("[FP] Fingerprint enrolled successfully\n");
    return 0;
}

int fp_verify(void) {
    // Load stored template
    FILE *f = fopen(FP_TEMPLATE, "rb");
    if (!f) {
        printf("[FP] No template enrolled\n");
        return 0;
    }
    FPTemplate stored;
    fread(&stored, sizeof(stored), 1, f);
    fclose(f);

    printf("[FP] Place finger on sensor...\n");

    int     tries = 0;
    uint8_t raw[512];
    while (tries < FP_TIMEOUT) {
        int n = fp_read_raw(raw, sizeof(raw));
        if (n > 0) {
            uint8_t hash[32];
            fp_hash(raw, n, hash);

            // Compare with tolerance
            int match = 0;
            int diff  = 0;
            for (int i = 0; i < 32; i++)
                diff += abs(hash[i] - stored.hash[i]);

            // Allow 15% tolerance
            if (diff < 32 * 38) {
                printf("[FP] Match! Access granted\n");
                return 1;
            }
        }
        tries++;
        sleep(1);
    }

    printf("[FP] No match. Access denied\n");
    return 0;
}

void fp_close(void) {
    if (fp_fd >= 0) {
        close(fp_fd);
        fp_fd = -1;
    }
}
