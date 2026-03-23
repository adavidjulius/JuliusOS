#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <pthread.h>
#include <time.h>
#include <errno.h>

#define PM_MAX_SERVICES  64
#define PM_SOCKET        "/var/run/julius_pm.sock"
#define PM_LOG           "/var/log/julius_pm.log"
#define PM_VERSION       "1.0"

typedef enum {
    SVC_STOPPED  = 0,
    SVC_STARTING = 1,
    SVC_RUNNING  = 2,
    SVC_STOPPING = 3,
    SVC_FAILED   = 4,
    SVC_DISABLED = 5,
} ServiceState;

typedef struct {
    char         name[64];
    char         exec[256];
    char         args[512];
    ServiceState state;
    pid_t        pid;
    int          restart_count;
    int          max_restarts;
    int          auto_restart;
    int          priority;
    time_t       start_time;
    time_t       last_restart;
    uint64_t     cpu_time;
    size_t       mem_usage;
} Service;

static Service   services[PM_MAX_SERVICES];
static int       svc_count = 0;
static pthread_mutex_t pm_lock = PTHREAD_MUTEX_INITIALIZER;
static volatile int running = 1;

void pm_log(const char *level, const char *msg) {
    FILE *f = fopen(PM_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(f, "[%s] [%s] %s\n", ts, level, msg);
    fclose(f);
    printf("[PM] [%s] %s\n", level, msg);
}

Service *find_service(const char *name) {
    for (int i = 0; i < svc_count; i++)
        if (strcmp(services[i].name, name) == 0)
            return &services[i];
    return NULL;
}

int pm_register(const char *name, const char *exec,
    int auto_restart, int priority) {
    pthread_mutex_lock(&pm_lock);
    if (svc_count >= PM_MAX_SERVICES) {
        pthread_mutex_unlock(&pm_lock);
        return -1;
    }
    Service *s = &services[svc_count++];
    strncpy(s->name, name, sizeof(s->name)-1);
    strncpy(s->exec, exec, sizeof(s->exec)-1);
    s->state        = SVC_STOPPED;
    s->pid          = -1;
    s->restart_count= 0;
    s->max_restarts = 5;
    s->auto_restart = auto_restart;
    s->priority     = priority;
    pthread_mutex_unlock(&pm_lock);
    char msg[128];
    snprintf(msg, sizeof(msg), "Registered: %s", name);
    pm_log("INFO", msg);
    return 0;
}

int pm_start(const char *name) {
    Service *s = find_service(name);
    if (!s) return -1;
    if (s->state == SVC_RUNNING) return 0;

    s->state = SVC_STARTING;
    pid_t pid = fork();
    if (pid < 0) {
        s->state = SVC_FAILED;
        return -1;
    }
    if (pid == 0) {
        // Child process
        setsid();
        char *argv[] = { s->exec, NULL };
        execv(s->exec, argv);
        exit(1);
    }
    s->pid        = pid;
    s->state      = SVC_RUNNING;
    s->start_time = time(NULL);

    char msg[128];
    snprintf(msg, sizeof(msg), "Started: %s (PID %d)", name, pid);
    pm_log("INFO", msg);
    return 0;
}

int pm_stop(const char *name) {
    Service *s = find_service(name);
    if (!s || s->state != SVC_RUNNING) return -1;
    s->state = SVC_STOPPING;
    kill(s->pid, SIGTERM);
    int status;
    int ret = waitpid(s->pid, &status, WNOHANG);
    if (ret == 0) {
        sleep(2);
        kill(s->pid, SIGKILL);
        waitpid(s->pid, &status, 0);
    }
    s->state = SVC_STOPPED;
    s->pid   = -1;
    char msg[128];
    snprintf(msg, sizeof(msg), "Stopped: %s", name);
    pm_log("INFO", msg);
    return 0;
}

int pm_restart(const char *name) {
    pm_stop(name);
    sleep(1);
    return pm_start(name);
}

void pm_status_all(void) {
    printf("\n=== Julius Process Manager Status ===\n");
    printf("%-20s %-10s %-8s %-8s %s\n",
        "NAME","STATE","PID","RESTART","UPTIME");
    printf("%.60s\n", "------------------------------------------------------------");
    for (int i = 0; i < svc_count; i++) {
        Service *s = &services[i];
        const char *state_str[] = {
            "stopped","starting","running",
            "stopping","failed","disabled"
        };
        int uptime = s->state == SVC_RUNNING ?
            (int)(time(NULL) - s->start_time) : 0;
        printf("%-20s %-10s %-8d %-8d %ds\n",
            s->name, state_str[s->state],
            s->pid, s->restart_count, uptime);
    }
    printf("\n");
}

void *watchdog_thread(void *arg) {
    while (running) {
        pthread_mutex_lock(&pm_lock);
        for (int i = 0; i < svc_count; i++) {
            Service *s = &services[i];
            if (s->state != SVC_RUNNING) continue;
            int status;
            int ret = waitpid(s->pid, &status, WNOHANG);
            if (ret > 0) {
                char msg[128];
                snprintf(msg, sizeof(msg),
                    "Service crashed: %s (exit %d)",
                    s->name, WEXITSTATUS(status));
                pm_log("WARN", msg);
                s->state = SVC_FAILED;
                s->pid   = -1;
                if (s->auto_restart &&
                        s->restart_count < s->max_restarts) {
                    s->restart_count++;
                    s->last_restart = time(NULL);
                    pthread_mutex_unlock(&pm_lock);
                    sleep(2);
                    pm_start(s->name);
                    pthread_mutex_lock(&pm_lock);
                }
            }
        }
        pthread_mutex_unlock(&pm_lock);
        sleep(5);
    }
    return NULL;
}

void signal_handler(int sig) {
    if (sig == SIGTERM || sig == SIGINT) {
        running = 0;
        pm_log("INFO", "Process Manager shutting down");
        for (int i = 0; i < svc_count; i++)
            if (services[i].state == SVC_RUNNING)
                pm_stop(services[i].name);
    }
}

int main(void) {
    printf("[PM] Julius Process Manager v%s\n", PM_VERSION);
    signal(SIGTERM, signal_handler);
    signal(SIGINT,  signal_handler);
    signal(SIGCHLD, SIG_DFL);

    // Register all Julius OS services
    pm_register("julius_core",     "/usr/bin/julius_core",     1, 1);
    pm_register("julius_enclave",  "/usr/bin/julius_enclave",  1, 1);
    pm_register("julius_wifi",     "/usr/bin/julius_wifi",     1, 2);
    pm_register("julius_bt",       "/usr/bin/julius_bt",       1, 2);
    pm_register("julius_power",    "/usr/bin/julius_power",    1, 1);
    pm_register("julius_keychain", "/usr/bin/julius_keychain", 1, 1);
    pm_register("julius_health",   "/usr/bin/julius_health",   1, 1);
    pm_register("julius_push",     "/usr/bin/julius_push",     1, 3);
    pm_register("julius_sync",     "/usr/bin/julius_sync",     1, 3);
    pm_register("julius_audit",    "/usr/bin/julius_audit",    1, 2);
    pm_register("julius_ui",
        "/usr/bin/python3 /usr/julius/src/julius_ui.py", 1, 4);

    // Start all services in priority order
    for (int p = 1; p <= 4; p++)
        for (int i = 0; i < svc_count; i++)
            if (services[i].priority == p)
                pm_start(services[i].name);

    // Start watchdog
    pthread_t wt;
    pthread_create(&wt, NULL, watchdog_thread, NULL);

    pm_log("INFO", "All services started");
    pm_status_all();

    while (running) {
        sleep(30);
        pm_status_all();
    }

    pthread_cancel(wt);
    return 0;
}
