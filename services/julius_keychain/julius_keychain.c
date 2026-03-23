#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <openssl/aes.h>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <openssl/evp.h>
#include <time.h>

#define KC_SOCKET   "/var/run/julius_keychain.sock"
#define KC_DB_FILE  "/etc/julius/keychain.db"
#define KC_VERSION  "1.0"
#define KC_MAX_ITEMS 1024
#define KC_KEY_SIZE  32
#define KC_IV_SIZE   16

typedef enum {
    KC_ADD    = 1,
    KC_GET    = 2,
    KC_DELETE = 3,
    KC_LIST   = 4,
    KC_UPDATE = 5,
} KeychainOp;

typedef struct {
    KeychainOp op;
    char       service[64];
    char       account[64];
    uint8_t    data[512];
    int        data_len;
    char       label[128];
} KeychainRequest;

typedef struct {
    int     status;
    uint8_t data[512];
    int     data_len;
    char    error[128];
    char    items[4096];
} KeychainResponse;

typedef struct {
    char    service[64];
    char    account[64];
    char    label[128];
    uint8_t encrypted[512];
    int     enc_len;
    uint8_t iv[KC_IV_SIZE];
    uint8_t tag[16];
    time_t  created;
    time_t  modified;
} KeychainItem;

static KeychainItem  items[KC_MAX_ITEMS];
static int           item_count = 0;
static uint8_t       kc_key[KC_KEY_SIZE];
static pthread_mutex_t kc_lock = PTHREAD_MUTEX_INITIALIZER;

void kc_log(const char *msg) {
    printf("[KC] %s\n", msg);
    fflush(stdout);
}

int kc_init_key(void) {
    const char *key_file = "/etc/julius/keychain.key";
    if (access(key_file, F_OK) == 0) {
        FILE *f = fopen(key_file, "rb");
        if (!f) return -1;
        fread(kc_key, 1, KC_KEY_SIZE, f);
        fclose(f);
        return 0;
    }
    RAND_bytes(kc_key, KC_KEY_SIZE);
    FILE *f = fopen(key_file, "wb");
    if (!f) return -1;
    fwrite(kc_key, 1, KC_KEY_SIZE, f);
    fclose(f);
    chmod(key_file, 0600);
    kc_log("Keychain key generated");
    return 0;
}

int kc_encrypt(const uint8_t *plain, int plain_len,
    uint8_t *cipher, uint8_t *iv, uint8_t *tag) {
    RAND_bytes(iv, KC_IV_SIZE);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    int len=0, total=0;
    EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL);
    EVP_EncryptInit_ex(ctx, NULL, NULL, kc_key, iv);
    EVP_EncryptUpdate(ctx, cipher, &len, plain, plain_len);
    total = len;
    EVP_EncryptFinal_ex(ctx, cipher+len, &len);
    total += len;
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag);
    EVP_CIPHER_CTX_free(ctx);
    return total;
}

int kc_decrypt(const uint8_t *cipher, int cipher_len,
    uint8_t *plain, const uint8_t *iv, const uint8_t *tag) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    int len=0, total=0;
    EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL);
    EVP_DecryptInit_ex(ctx, NULL, NULL, kc_key, iv);
    EVP_DecryptUpdate(ctx, plain, &len, cipher, cipher_len);
    total = len;
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, (void*)tag);
    int ret = EVP_DecryptFinal_ex(ctx, plain+len, &len);
    EVP_CIPHER_CTX_free(ctx);
    if (ret <= 0) return -1;
    total += len;
    return total;
}

void kc_save(void) {
    FILE *f = fopen(KC_DB_FILE, "wb");
    if (!f) return;
    fwrite(&item_count, sizeof(int), 1, f);
    fwrite(items, sizeof(KeychainItem), item_count, f);
    fclose(f);
    chmod(KC_DB_FILE, 0600);
}

void kc_load(void) {
    FILE *f = fopen(KC_DB_FILE, "rb");
    if (!f) return;
    fread(&item_count, sizeof(int), 1, f);
    if (item_count > KC_MAX_ITEMS) item_count = 0;
    else fread(items, sizeof(KeychainItem), item_count, f);
    fclose(f);
    char msg[64];
    snprintf(msg, sizeof(msg), "Loaded %d items", item_count);
    kc_log(msg);
}

KeychainItem *kc_find(const char *svc, const char *acc) {
    for (int i = 0; i < item_count; i++)
        if (strcmp(items[i].service, svc)==0 &&
            strcmp(items[i].account, acc)==0)
            return &items[i];
    return NULL;
}

void handle_kc_request(int fd) {
    KeychainRequest  req;
    KeychainResponse resp;
    memset(&resp, 0, sizeof(resp));

    if (read(fd, &req, sizeof(req)) != sizeof(req)) {
        resp.status = -1;
        write(fd, &resp, sizeof(resp));
        return;
    }

    pthread_mutex_lock(&kc_lock);

    switch (req.op) {
    case KC_ADD: {
        if (item_count >= KC_MAX_ITEMS) {
            resp.status = -1;
            strcpy(resp.error, "Keychain full");
            break;
        }
        KeychainItem *it = kc_find(req.service, req.account);
        if (!it) {
            it = &items[item_count++];
            strncpy(it->service, req.service, 63);
            strncpy(it->account, req.account, 63);
            strncpy(it->label,   req.label,   127);
            it->created = time(NULL);
        }
        it->enc_len = kc_encrypt(req.data, req.data_len,
            it->encrypted, it->iv, it->tag);
        it->modified = time(NULL);
        kc_save();
        resp.status = 0;
        char msg[128];
        snprintf(msg,sizeof(msg),"Added: %s/%s",
            req.service,req.account);
        kc_log(msg);
        break;
    }
    case KC_GET: {
        KeychainItem *it = kc_find(req.service, req.account);
        if (!it) {
            resp.status = -1;
            strcpy(resp.error, "Item not found");
            break;
        }
        resp.data_len = kc_decrypt(it->encrypted, it->enc_len,
            resp.data, it->iv, it->tag);
        resp.status = resp.data_len > 0 ? 0 : -1;
        break;
    }
    case KC_DELETE: {
        for (int i = 0; i < item_count; i++) {
            if (strcmp(items[i].service, req.service)==0 &&
                strcmp(items[i].account, req.account)==0) {
                memmove(&items[i], &items[i+1],
                    (item_count-i-1)*sizeof(KeychainItem));
                item_count--;
                kc_save();
                resp.status = 0;
                break;
            }
        }
        if (resp.status != 0) {
            resp.status = -1;
            strcpy(resp.error, "Item not found");
        }
        break;
    }
    case KC_LIST: {
        int pos = 0;
        for (int i = 0; i < item_count; i++) {
            pos += snprintf(resp.items+pos,
                sizeof(resp.items)-pos,
                "%s/%s\n",
                items[i].service, items[i].account);
        }
        resp.status = 0;
        break;
    }
    }

    pthread_mutex_unlock(&kc_lock);
    write(fd, &resp, sizeof(resp));
}

void *kc_thread(void *arg) {
    int fd = *(int*)arg;
    free(arg);
    handle_kc_request(fd);
    close(fd);
    return NULL;
}

int main(void) {
    printf("[KC] Julius Keychain v%s\n", KC_VERSION);
    if (kc_init_key() != 0) return 1;
    kc_load();

    int srv = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) return 1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, KC_SOCKET, sizeof(addr.sun_path)-1);
    unlink(KC_SOCKET);
    bind(srv, (struct sockaddr*)&addr, sizeof(addr));
    chmod(KC_SOCKET, 0600);
    listen(srv, 16);

    kc_log("Keychain ready");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(srv, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, kc_thread, cfd);
        pthread_detach(tid);
    }
    return 0;
}
