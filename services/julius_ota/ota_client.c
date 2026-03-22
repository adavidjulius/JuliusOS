#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/sha.h>
#include <openssl/rsa.h>

#define OTA_PORT        9876
#define OTA_CHUNK_SIZE  4096
#define OTA_MAGIC       "JULIUS_OTA_V1"
#define UPDATE_PATH     "/tmp/julius_update.pkg"
#define VERIFIED_PATH   "/usr/julius/update.pkg"

typedef struct {
    char    magic[16];
    char    version[32];
    char    admin_key[256];
    uint32_t size;
    uint8_t  sha256[32];
} OTAHeader;

int verify_admin(const char *key) {
    // Load stored admin key
    FILE *f = fopen("/etc/julius/admin.key", "r");
    if (!f) return 0;
    char stored[256];
    fgets(stored, sizeof(stored), f);
    fclose(f);
    stored[strcspn(stored, "\n")] = 0;
    return strcmp(key, stored) == 0;
}

int verify_checksum(const char *path, uint8_t *expected) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    uint8_t buf[4096];
    int     n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0)
        SHA256_Update(&ctx, buf, n);
    fclose(f);
    uint8_t hash[32];
    SHA256_Final(hash, &ctx);
    return memcmp(hash, expected, 32) == 0;
}

void apply_update(void) {
    printf("[OTA] Applying update...\n");
    // Backup current version
    system("cp -r /usr/julius /usr/julius.bak");
    // Extract and apply
    system("tar -xzf " VERIFIED_PATH " -C /usr/julius/");
    // Verify installation
    if (system("julius_verify_install") == 0) {
        printf("[OTA] Update applied successfully\n");
        system("rm -rf /usr/julius.bak");
        system("reboot");
    } else {
        printf("[OTA] Update failed, rolling back\n");
        system("rm -rf /usr/julius");
        system("mv /usr/julius.bak /usr/julius");
    }
}

int main(void) {
    printf("[OTA] Julius OTA Client starting...\n");

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    struct sockaddr_in addr;
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(OTA_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    int opt = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    listen(sockfd, 1);
    printf("[OTA] Listening on port %d\n", OTA_PORT);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t          clen = sizeof(client_addr);
        int                cfd  = accept(sockfd, (struct sockaddr *)&client_addr, &clen);
        if (cfd < 0) continue;

        printf("[OTA] Connection from %s\n", inet_ntoa(client_addr.sin_addr));

        OTAHeader hdr;
        if (read(cfd, &hdr, sizeof(hdr)) != sizeof(hdr)) {
            close(cfd);
            continue;
        }

        // Verify magic
        if (strcmp(hdr.magic, OTA_MAGIC) != 0) {
            printf("[OTA] Invalid magic, rejecting\n");
            close(cfd);
            continue;
        }

        // Verify admin key
        if (!verify_admin(hdr.admin_key)) {
            printf("[OTA] Invalid admin key, rejecting\n");
            close(cfd);
            continue;
        }

        printf("[OTA] Admin verified, receiving v%s\n", hdr.version);

        // Receive update package
        FILE   *f   = fopen(UPDATE_PATH, "wb");
        uint32_t received = 0;
        uint8_t  buf[OTA_CHUNK_SIZE];
        while (received < hdr.size) {
            int n = read(cfd, buf, sizeof(buf));
            if (n <= 0) break;
            fwrite(buf, 1, n, f);
            received += n;
            printf("[OTA] Progress: %u/%u bytes\r", received, hdr.size);
        }
        fclose(f);
        close(cfd);

        printf("\n[OTA] Received %u bytes\n", received);

        // Verify checksum
        if (!verify_checksum(UPDATE_PATH, hdr.sha256)) {
            printf("[OTA] Checksum failed, aborting\n");
            unlink(UPDATE_PATH);
            continue;
        }

        printf("[OTA] Checksum verified\n");
        rename(UPDATE_PATH, VERIFIED_PATH);
        apply_update();
    }

    close(sockfd);
    return 0;
}
