#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <pthread.h>
#include "ipc.h"

#define JULIUS_VERSION "1.0.0"
#define JULIUS_PID_FILE "/var/run/julius_core.pid"

static volatile int running = 1;
static pthread_t service_threads[8];
static int thread_count = 0;

typedef struct {
    const char *name;
    void *(*func)(void *);
} JuliusService;

void julius_log(const char *level, const char *msg) {
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", localtime(&now));
    printf("[%s] [%s] %s\n", ts, level, msg);
    fflush(stdout);
}

void signal_handler(int sig) {
    if (sig == SIGTERM || sig == SIGINT) {
        julius_log("INFO", "Julius Core shutting down...");
        running = 0;
    }
}

void *service_power(void *arg) {
    julius_log("INFO", "Power manager started");
    while (running) {
        // Read battery level
        FILE *f = fopen("/sys/class/power_supply/battery/capacity", "r");
        if (f) {
            int level = 0;
            fscanf(f, "%d", &level);
            fclose(f);
            ipc_broadcast("BATTERY", &level, sizeof(int));
        }
        sleep(30);
    }
    return NULL;
}

void *service_watchdog(void *arg) {
    julius_log("INFO", "Watchdog started");
    while (running) {
        // Check all services alive
        ipc_send("STATUS", "ping", 4);
        sleep(10);
    }
    return NULL;
}

void *service_ota_watch(void *arg) {
    julius_log("INFO", "OTA watcher started");
    while (running) {
        // Check for OTA signal every 60s
        char buf[256];
        if (ipc_receive("OTA", buf, sizeof(buf)) > 0) {
            julius_log("INFO", "OTA update signal received");
            system("/usr/bin/julius_ota_client");
        }
        sleep(60);
    }
    return NULL;
}

void start_service(const char *name, void *(*func)(void *)) {
    pthread_t tid;
    if (pthread_create(&tid, NULL, func, NULL) == 0) {
        service_threads[thread_count++] = tid;
        char msg[128];
        snprintf(msg, sizeof(msg), "Service started: %s", name);
        julius_log("INFO", msg);
    } else {
        char msg[128];
        snprintf(msg, sizeof(msg), "Failed to start: %s", name);
        julius_log("ERROR", msg);
    }
}

int main(int argc, char *argv[]) {
    printf("\n");
    printf("  ____       _ _            ___  ____  \n");
    printf(" |_  /__ _  | (_)_  _ ___  / _ \\/ ___| \n");
    printf("  / // _` | | | | || (_-< | (_) \\__ \\ \n");
    printf(" /___\\__,_| |_|_|\\_,_/__/  \\___/|___/ \n");
    printf("                          v%s\n\n", JULIUS_VERSION);

    signal(SIGTERM, signal_handler);
    signal(SIGINT,  signal_handler);

    julius_log("INFO", "Julius Core initializing...");

    // Write PID file
    FILE *pf = fopen(JULIUS_PID_FILE, "w");
    if (pf) {
        fprintf(pf, "%d\n", getpid());
        fclose(pf);
    }

    // Initialize IPC
    if (ipc_init() != 0) {
        julius_log("ERROR", "IPC init failed");
        return 1;
    }

    // Start all services
    start_service("power",    service_power);
    start_service("watchdog", service_watchdog);
    start_service("ota",      service_ota_watch);

    julius_log("INFO", "Julius Core running");

    // Main loop
    while (running) {
        // Handle IPC messages
        char   buf[512];
        char   topic[64];
        int    len = ipc_receive_any(topic, buf, sizeof(buf));
        if (len > 0) {
            char msg[128];
            snprintf(msg, sizeof(msg), "IPC: %s", topic);
            julius_log("DEBUG", msg);
        }
        usleep(100000);
    }

    // Cleanup
    for (int i = 0; i < thread_count; i++) {
        pthread_cancel(service_threads[i]);
        pthread_join(service_threads[i], NULL);
    }

    ipc_destroy();
    remove(JULIUS_PID_FILE);
    julius_log("INFO", "Julius Core stopped");
    return 0;
}
