#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <openssl/aes.h>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>

#define ENCLAVE_SOCKET  "/var/run/julius_enclave.sock"
#define ENCLAVE_KEY_FILE "/etc/julius/enclave.key"
#define ENCLAVE_VERSION  "1.0"
#define KEY_SIZE         32
#define IV_SIZE          16
#define TAG_SIZE         16
#define MAX_DATA_SIZE    4096

typedef enum {
    ENCLAVE_ENCRYPT   = 1,
    ENCLAVE_DECRYPT   = 2,
    ENCLAVE_HASH      = 3,
    ENCLAVE_VERIFY    = 4,
    ENCLAVE_KEYGEN    = 5,
    ENCLAVE_SIGN      = 6,
} EnclaveOp;

typedef struct {
    EnclaveOp op;
    uint32_t  data_len;
    uint8_t   data[MAX_DATA_SIZE];
    uint8_t   key_id[32];
    uint8_t   iv[IV_SIZE];
    uint8_t   tag[TAG_SIZE];
} EnclaveRequest;

typedef struct {
    int      status;
    uint32_t data_len;
    uint8_t  data[MAX_DATA_SIZE];
    uint8_t  tag[TAG_SIZE];
    char     error[128];
} EnclaveResponse;

typedef struct {
    uint8_t  id[32];
    uint8_t  key[KEY_SIZE];
    char     label[64];
    time_t   created;
    int      usage_count;
} EnclaveKey;

static uint8_t master_key[KEY_SIZE];
static EnclaveKey keys[256];
static int key_count = 0;
static pthread_mutex_t enclave_lock = PTHREAD_MUTEX_INITIALIZER;

void julius_log_enclave(const char *msg) {
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", localtime(&now));
    printf("[%s] [ENCLAVE] %s\n", ts, msg);
    fflush(stdout);
}

int enclave_init_master_key(void) {
    if (access(ENCLAVE_KEY_FILE, F_OK) == 0) {
        FILE *f = fopen(ENCLAVE_KEY_FILE, "rb");
        if (!f) return -1;
        fread(master_key, 1, KEY_SIZE, f);
        fclose(f);
        julius_log_enclave("Master key loaded");
        return 0;
    }
    if (RAND_bytes(master_key, KEY_SIZE) != 1) return -1;
    FILE *f = fopen(ENCLAVE_KEY_FILE, "wb");
    if (!f) return -1;
    fwrite(master_key, 1, KEY_SIZE, f);
    fclose(f);
    chmod(ENCLAVE_KEY_FILE, 0600);
    julius_log_enclave("Master key generated");
    return 0;
}

int enclave_generate_key(const char *label, uint8_t *id_out) {
    pthread_mutex_lock(&enclave_lock);
    if (key_count >= 256) {
        pthread_mutex_unlock(&enclave_lock);
        return -1;
    }
    EnclaveKey *k = &keys[key_count];
    RAND_bytes(k->key, KEY_SIZE);
    RAND_bytes(k->id,  32);
    strncpy(k->label, label, sizeof(k->label)-1);
    k->created     = time(NULL);
    k->usage_count = 0;
    memcpy(id_out, k->id, 32);
    key_count++;
    pthread_mutex_unlock(&enclave_lock);
    char msg[128];
    snprintf(msg, sizeof(msg), "Key generated: %s", label);
    julius_log_enclave(msg);
    return 0;
}

EnclaveKey *find_key(const uint8_t *id) {
    for (int i = 0; i < key_count; i++)
        if (memcmp(keys[i].id, id, 32) == 0)
            return &keys[i];
    return NULL;
}

int enclave_encrypt(const uint8_t *key, const uint8_t *plain,
    int plain_len, uint8_t *cipher, uint8_t *iv, uint8_t *tag) {
    RAND_bytes(iv, IV_SIZE);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    int len = 0, cipher_len = 0;
    EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL);
    EVP_EncryptInit_ex(ctx, NULL, NULL, key, iv);
    EVP_EncryptUpdate(ctx, cipher, &len, plain, plain_len);
    cipher_len = len;
    EVP_EncryptFinal_ex(ctx, cipher+len, &len);
    cipher_len += len;
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, TAG_SIZE, tag);
    EVP_CIPHER_CTX_free(ctx);
    return cipher_len;
}

int enclave_decrypt(const uint8_t *key, const uint8_t *cipher,
    int cipher_len, uint8_t *plain, const uint8_t *iv,
    const uint8_t *tag) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;
    int len = 0, plain_len = 0;
    EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL);
    EVP_DecryptInit_ex(ctx, NULL, NULL, key, iv);
    EVP_DecryptUpdate(ctx, plain, &len, cipher, cipher_len);
    plain_len = len;
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, TAG_SIZE,
        (void*)tag);
    int ret = EVP_DecryptFinal_ex(ctx, plain+len, &len);
    EVP_CIPHER_CTX_free(ctx);
    if (ret <= 0) return -1;
    plain_len += len;
    return plain_len;
}

void handle_request(int fd) {
    EnclaveRequest  req;
    EnclaveResponse resp;
    memset(&resp, 0, sizeof(resp));

    if (read(fd, &req, sizeof(req)) != sizeof(req)) {
        resp.status = -1;
        strcpy(resp.error, "Invalid request");
        write(fd, &resp, sizeof(resp));
        return;
    }

    switch (req.op) {
    case ENCLAVE_ENCRYPT: {
        EnclaveKey *k = find_key(req.key_id);
        if (!k) {
            resp.status = -1;
            strcpy(resp.error, "Key not found");
            break;
        }
        int len = enclave_encrypt(k->key, req.data, req.data_len,
            resp.data, resp.data + MAX_DATA_SIZE - IV_SIZE, resp.tag);
        if (len < 0) {
            resp.status = -1;
            strcpy(resp.error, "Encryption failed");
        } else {
            resp.data_len = len;
            resp.status   = 0;
            k->usage_count++;
        }
        break;
    }
    case ENCLAVE_DECRYPT: {
        EnclaveKey *k = find_key(req.key_id);
        if (!k) {
            resp.status = -1;
            strcpy(resp.error, "Key not found");
            break;
        }
        int len = enclave_decrypt(k->key, req.data, req.data_len,
            resp.data, req.iv, req.tag);
        if (len < 0) {
            resp.status = -1;
            strcpy(resp.error, "Decryption failed");
        } else {
            resp.data_len = len;
            resp.status   = 0;
            k->usage_count++;
        }
        break;
    }
    case ENCLAVE_HASH: {
        SHA256_CTX ctx;
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, req.data, req.data_len);
        SHA256_Final(resp.data, &ctx);
        resp.data_len = 32;
        resp.status   = 0;
        break;
    }
    case ENCLAVE_KEYGEN: {
        int ret = enclave_generate_key(
            (char*)req.data, resp.data);
        resp.data_len = ret == 0 ? 32 : 0;
        resp.status   = ret;
        break;
    }
    default:
        resp.status = -1;
        strcpy(resp.error, "Unknown operation");
    }
    write(fd, &resp, sizeof(resp));
}

void *client_thread(void *arg) {
    int fd = *(int*)arg;
    free(arg);
    handle_request(fd);
    close(fd);
    return NULL;
}

int main(void) {
    printf("[ENCLAVE] Julius Security Enclave v%s starting\n",
        ENCLAVE_VERSION);

    if (enclave_init_master_key() != 0) {
        fprintf(stderr, "[ENCLAVE] Failed to init master key\n");
        return 1;
    }

    int srv = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) { perror("socket"); return 1; }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, ENCLAVE_SOCKET, sizeof(addr.sun_path)-1);
    unlink(ENCLAVE_SOCKET);

    if (bind(srv, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }
    chmod(ENCLAVE_SOCKET, 0600);
    listen(srv, 16);

    julius_log_enclave("Enclave ready — accepting requests");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(srv, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, client_thread, cfd);
        pthread_detach(tid);
    }
    return 0;
}
