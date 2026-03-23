#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>

#define PERMS_SOCKET  "/var/run/julius_perms.sock"
#define PERMS_DB      "/etc/julius/permissions.db"
#define PERMS_LOG     "/var/log/julius_perms.log"
#define PERMS_VERSION "1.0"
#define MAX_PERMS     512

typedef enum {
    PERM_NETWORK   = 1,
    PERM_CAMERA    = 2,
    PERM_MIC       = 3,
    PERM_LOCATION  = 4,
    PERM_CONTACTS  = 5,
    PERM_STORAGE   = 6,
    PERM_BLUETOOTH = 7,
    PERM_WIFI      = 8,
    PERM_GPIO      = 9,
    PERM_ROOT      = 10,
} PermissionType;

typedef enum {
    PERM_STATUS_UNKNOWN  = 0,
    PERM_STATUS_GRANTED  = 1,
    PERM_STATUS_DENIED   = 2,
    PERM_STATUS_ASK      = 3,
} PermissionStatus;

typedef struct {
    char            app[64];
    PermissionType  type;
    PermissionStatus status;
    time_t          granted_at;
    int             usage_count;
} Permission;

typedef struct {
    int            op;
    char           app[64];
    PermissionType type;
} PermRequest;

typedef struct {
    PermissionStatus status;
    int              granted;
} PermResponse;

static Permission  perms[MAX_PERMS];
static int         perm_count = 0;
static pthread_mutex_t perms_lock = PTHREAD_MUTEX_INITIALIZER;

void perms_log(const char *msg) {
    FILE *f = fopen(PERMS_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts,sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [PERMS] %s\n", ts, msg);
    fclose(f);
}

const char *perm_type_str(PermissionType t) {
    switch(t) {
    case PERM_NETWORK:   return "Network";
    case PERM_CAMERA:    return "Camera";
    case PERM_MIC:       return "Microphone";
    case PERM_LOCATION:  return "Location";
    case PERM_CONTACTS:  return "Contacts";
    case PERM_STORAGE:   return "Storage";
    case PERM_BLUETOOTH: return "Bluetooth";
    case PERM_WIFI:      return "WiFi";
    case PERM_GPIO:      return "GPIO";
    case PERM_ROOT:      return "Root";
    default:             return "Unknown";
    }
}

void load_defaults(void) {
    // Network apps
    const char *net_apps[] = {
        "WiFi","Scanner","NetTools","SSH",
        "Packets","NetMon","NetMapper","SpeedTest",
        "WakeOnLAN","Transfer","Drop","Cloud",NULL
    };
    for (int i = 0; net_apps[i]; i++) {
        Permission *p   = &perms[perm_count++];
        strncpy(p->app, net_apps[i], 63);
        p->type         = PERM_NETWORK;
        p->status       = PERM_STATUS_GRANTED;
        p->granted_at   = time(NULL);
    }
    // GPIO apps
    Permission *p = &perms[perm_count++];
    strncpy(p->app, "GPIO", 63);
    p->type   = PERM_GPIO;
    p->status = PERM_STATUS_GRANTED;
    // Bluetooth apps
    p = &perms[perm_count++];
    strncpy(p->app, "Bluetooth", 63);
    p->type   = PERM_BLUETOOTH;
    p->status = PERM_STATUS_GRANTED;
}

PermissionStatus check_permission(
    const char *app, PermissionType type) {
    for (int i = 0; i < perm_count; i++) {
        if (strcmp(perms[i].app, app)==0 &&
            perms[i].type == type) {
            perms[i].usage_count++;
            return perms[i].status;
        }
    }
    return PERM_STATUS_UNKNOWN;
}

void grant_permission(const char *app, PermissionType type) {
    Permission *p = NULL;
    for (int i = 0; i < perm_count; i++) {
        if (strcmp(perms[i].app,app)==0 &&
            perms[i].type==type) {
            p = &perms[i];
            break;
        }
    }
    if (!p && perm_count < MAX_PERMS) {
        p = &perms[perm_count++];
        strncpy(p->app, app, 63);
        p->type = type;
    }
    if (p) {
        p->status     = PERM_STATUS_GRANTED;
        p->granted_at = time(NULL);
        char msg[128];
        snprintf(msg, sizeof(msg),
            "Granted %s to %s", perm_type_str(type), app);
        perms_log(msg);
    }
}

void deny_permission(const char *app, PermissionType type) {
    for (int i = 0; i < perm_count; i++) {
        if (strcmp(perms[i].app,app)==0 &&
            perms[i].type==type) {
            perms[i].status = PERM_STATUS_DENIED;
            char msg[128];
            snprintf(msg, sizeof(msg),
                "Denied %s to %s",
                perm_type_str(type), app);
            perms_log(msg);
            return;
        }
    }
}

void handle_perms_client(int fd) {
    PermRequest  req;
    PermResponse resp;

    while (read(fd, &req, sizeof(req)) == sizeof(req)) {
        memset(&resp, 0, sizeof(resp));
        pthread_mutex_lock(&perms_lock);

        if (req.op == 1) { // CHECK
            resp.status  = check_permission(req.app, req.type);
            resp.granted = resp.status == PERM_STATUS_GRANTED;
        } else if (req.op == 2) { // GRANT
            grant_permission(req.app, req.type);
            resp.granted = 1;
        } else if (req.op == 3) { // DENY
            deny_permission(req.app, req.type);
            resp.granted = 0;
        }

        pthread_mutex_unlock(&perms_lock);
        write(fd, &resp, sizeof(resp));
    }
    close(fd);
}

void *perms_thread(void *arg) {
    int fd = *(int*)arg;
    free(arg);
    handle_perms_client(fd);
    return NULL;
}

int main(void) {
    printf("[PERMS] Julius Permissions v%s\n", PERMS_VERSION);
    load_defaults();

    int srv = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) return 1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, PERMS_SOCKET,
        sizeof(addr.sun_path)-1);
    unlink(PERMS_SOCKET);
    bind(srv, (struct sockaddr*)&addr, sizeof(addr));
    chmod(PERMS_SOCKET, 0666);
    listen(srv, 16);

    perms_log("Permissions daemon ready");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(srv, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, perms_thread, cfd);
        pthread_detach(tid);
    }
    return 0;
}
