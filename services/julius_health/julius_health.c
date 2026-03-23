#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <signal.h>

#define HEALTH_SOCKET  "/var/run/julius_health.sock"
#define HEALTH_LOG     "/var/log/julius_health.log"
#define HEALTH_STATE   "/var/run/julius_health.state"
#define HEALTH_VERSION "1.0"
#define CHECK_INTERVAL 15

typedef struct {
    char    name[64];
    char    socket_path[128];
    int     healthy;
    int     fail_count;
    time_t  last_check;
    time_t  last_healthy;
} HealthCheck;

static HealthCheck checks[] = {
    {"julius_core",     "/var/run/julius_ipc.sock",      0,0,0,0},
    {"julius_enclave",  "/var/run/julius_enclave.sock",  0,0,0,0},
    {"julius_keychain", "/var/run/julius_keychain.sock", 0,0,0,0},
    {"julius_wifi",     "/var/run/julius_wifi.state",    0,0,0,0},
    {"julius_bt",       "/var/run/julius_bt.state",      0,0,0,0},
    {"julius_power",    "/var/run/julius_power.state",   0,0,0,0},
    {"julius_audit",    "/var/run/julius_audit.sock",    0,0,0,0},
};

static int check_count =
    sizeof(checks)/sizeof(HealthCheck);

void health_log(const char *level, const char *msg) {
    FILE *f = fopen(HEALTH_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [%s] %s\n", ts, level, msg);
    fclose(f);
    printf("[HEALTH] [%s] %s\n", level, msg);
}

int check_service(HealthCheck *h) {
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return 0;
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, h->socket_path,
        sizeof(addr.sun_path)-1);
    struct timeval tv = {1, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    int ret = connect(fd,
        (struct sockaddr*)&addr, sizeof(addr));
    close(fd);
    return ret == 0;
}

int check_file(HealthCheck *h) {
    return access(h->socket_path, F_OK) == 0;
}

void save_health_state(void) {
    FILE *f = fopen(HEALTH_STATE, "w");
    if (!f) return;
    int healthy = 0;
    for (int i = 0; i < check_count; i++)
        if (checks[i].healthy) healthy++;
    fprintf(f, "total=%d\n",   check_count);
    fprintf(f, "healthy=%d\n", healthy);
    fprintf(f, "score=%d\n",
        (int)(healthy*100/check_count));
    for (int i = 0; i < check_count; i++)
        fprintf(f, "%s=%s\n",
            checks[i].name,
            checks[i].healthy ? "up" : "down");
    fclose(f);
}

void restart_service(const char *name) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd),
        "julius_pm restart %s", name);
    system(cmd);
    char msg[128];
    snprintf(msg, sizeof(msg), "Restarted: %s", name);
    health_log("WARN", msg);
}

int main(void) {
    printf("[HEALTH] Julius Health Monitor v%s\n",
        HEALTH_VERSION);

    while (1) {
        int total_healthy = 0;

        for (int i = 0; i < check_count; i++) {
            HealthCheck *h = &checks[i];
            int was_healthy = h->healthy;

            // Check socket or file
            if (strstr(h->socket_path, ".sock"))
                h->healthy = check_service(h);
            else
                h->healthy = check_file(h);

            h->last_check = time(NULL);
            if (h->healthy) {
                h->last_healthy = time(NULL);
                h->fail_count   = 0;
                total_healthy++;
            } else {
                h->fail_count++;
                char msg[128];
                snprintf(msg, sizeof(msg),
                    "Service down: %s (fails: %d)",
                    h->name, h->fail_count);
                health_log("WARN", msg);

                if (h->fail_count >= 3) {
                    restart_service(h->name);
                    h->fail_count = 0;
                }
            }

            if (was_healthy != h->healthy) {
                char msg[128];
                snprintf(msg, sizeof(msg),
                    "%s -> %s",
                    h->name,
                    h->healthy ? "UP" : "DOWN");
                health_log(h->healthy ? "INFO" : "ERROR", msg);
            }
        }

        save_health_state();

        char summary[128];
        snprintf(summary, sizeof(summary),
            "Health: %d/%d services up (%d%%)",
            total_healthy, check_count,
            total_healthy*100/check_count);
        health_log("INFO", summary);

        sleep(CHECK_INTERVAL);
    }
    return 0;
}
