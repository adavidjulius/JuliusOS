#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <openssl/sha.h>

#define AUDIT_SOCKET  "/var/run/julius_audit.sock"
#define AUDIT_LOG     "/var/log/julius_audit.log"
#define AUDIT_VERSION "1.0"

typedef enum {
    AUDIT_AUTH_SUCCESS  = 1,
    AUDIT_AUTH_FAIL     = 2,
    AUDIT_APP_START     = 3,
    AUDIT_APP_STOP      = 4,
    AUDIT_FILE_ACCESS   = 5,
    AUDIT_NET_CONNECT   = 6,
    AUDIT_SETTINGS_CHANGE=7,
    AUDIT_OTA_UPDATE    = 8,
    AUDIT_ENCLAVE_USE   = 9,
    AUDIT_PERMISSION    = 10,
    AUDIT_KEYCHAIN      = 11,
    AUDIT_SECURITY_ALERT= 12,
} AuditEventType;

typedef struct {
    AuditEventType type;
    char           source[64];
    char           action[128];
    char           detail[256];
    pid_t          pid;
    time_t         timestamp;
    int            severity;
} AuditEvent;

static pthread_mutex_t audit_lock = PTHREAD_MUTEX_INITIALIZER;
static FILE           *audit_file = NULL;
static uint64_t        event_count = 0;

const char *audit_type_str(AuditEventType t) {
    switch(t) {
    case AUDIT_AUTH_SUCCESS:   return "AUTH_SUCCESS";
    case AUDIT_AUTH_FAIL:      return "AUTH_FAIL";
    case AUDIT_APP_START:      return "APP_START";
    case AUDIT_APP_STOP:       return "APP_STOP";
    case AUDIT_FILE_ACCESS:    return "FILE_ACCESS";
    case AUDIT_NET_CONNECT:    return "NET_CONNECT";
    case AUDIT_SETTINGS_CHANGE:return "SETTINGS_CHANGE";
    case AUDIT_OTA_UPDATE:     return "OTA_UPDATE";
    case AUDIT_ENCLAVE_USE:    return "ENCLAVE_USE";
    case AUDIT_PERMISSION:     return "PERMISSION";
    case AUDIT_KEYCHAIN:       return "KEYCHAIN";
    case AUDIT_SECURITY_ALERT: return "SECURITY_ALERT";
    default:                   return "UNKNOWN";
    }
}

const char *severity_str(int s) {
    if (s >= 4) return "CRITICAL";
    if (s >= 3) return "HIGH";
    if (s >= 2) return "MEDIUM";
    if (s >= 1) return "LOW";
    return "INFO";
}

void audit_compute_hash(const AuditEvent *e, char *hash_out) {
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, e, sizeof(AuditEvent));
    uint8_t hash[32];
    SHA256_Final(hash, &ctx);
    for (int i = 0; i < 8; i++)
        sprintf(hash_out+i*2, "%02x", hash[i]);
    hash_out[16] = 0;
}

void audit_write(const AuditEvent *e) {
    pthread_mutex_lock(&audit_lock);

    if (!audit_file)
        audit_file = fopen(AUDIT_LOG, "a");
    if (!audit_file) {
        pthread_mutex_unlock(&audit_lock);
        return;
    }

    char   ts[32];
    char   hash[17];
    struct tm *tm = localtime(&e->timestamp);
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", tm);
    audit_compute_hash(e, hash);

    fprintf(audit_file,
        "[%s] [%s] [%s] [PID:%d] [HASH:%s] "
        "SOURCE:%s ACTION:%s DETAIL:%s\n",
        ts,
        audit_type_str(e->type),
        severity_str(e->severity),
        e->pid,
        hash,
        e->source,
        e->action,
        e->detail);
    fflush(audit_file);
    event_count++;

    // Alert on security events
    if (e->severity >= 3) {
        fprintf(stderr,
            "[AUDIT ALERT] %s: %s — %s\n",
            audit_type_str(e->type),
            e->source, e->action);
    }

    pthread_mutex_unlock(&audit_lock);
}

void handle_audit_client(int fd) {
    AuditEvent event;
    while (read(fd, &event, sizeof(event)) == sizeof(event)) {
        event.timestamp = time(NULL);
        audit_write(&event);
    }
    close(fd);
}

void *audit_thread(void *arg) {
    int fd = *(int*)arg;
    free(arg);
    handle_audit_client(fd);
    return NULL;
}

int main(void) {
    printf("[AUDIT] Julius Audit Log v%s\n", AUDIT_VERSION);

    int srv = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) return 1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, AUDIT_SOCKET, sizeof(addr.sun_path)-1);
    unlink(AUDIT_SOCKET);
    bind(srv, (struct sockaddr*)&addr, sizeof(addr));
    chmod(AUDIT_SOCKET, 0666);
    listen(srv, 32);

    // Write startup event
    AuditEvent startup = {
        .type      = AUDIT_APP_START,
        .pid       = getpid(),
        .severity  = 0,
        .timestamp = time(NULL),
    };
    strcpy(startup.source, "julius_audit");
    strcpy(startup.action, "STARTED");
    snprintf(startup.detail, sizeof(startup.detail),
        "Julius Audit Log v%s started", AUDIT_VERSION);
    audit_write(&startup);

    printf("[AUDIT] Accepting audit events\n");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(srv, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, audit_thread, cfd);
        pthread_detach(tid);
    }
    return 0;
}
