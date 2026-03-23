#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <dirent.h>
#include <sys/types.h>
#include <pthread.h>
#include <time.h>

#define MM_LOG          "/var/log/julius_mm.log"
#define MM_VERSION      "1.0"
#define LOW_MEM_MB      32
#define CRITICAL_MEM_MB 16
#define CHECK_INTERVAL  10

typedef struct {
    pid_t   pid;
    char    name[64];
    size_t  mem_kb;
    int     oom_score;
    int     priority;
    time_t  last_active;
} ProcessInfo;

void mm_log(const char *level, const char *msg) {
    FILE *f = fopen(MM_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [MM/%s] %s\n", ts, level, msg);
    fclose(f);
    printf("[MM] [%s] %s\n", level, msg);
}

long get_available_mem_mb(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return -1;
    char   line[256];
    long   avail = -1;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "MemAvailable:", 13) == 0) {
            sscanf(line, "MemAvailable: %ld", &avail);
            break;
        }
    }
    fclose(f);
    return avail / 1024;
}

long get_process_mem_kb(pid_t pid) {
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/status", pid);
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    char line[256];
    long mem = -1;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "VmRSS:", 6) == 0) {
            sscanf(line, "VmRSS: %ld", &mem);
            break;
        }
    }
    fclose(f);
    return mem;
}

int get_oom_score(pid_t pid) {
    char path[64];
    snprintf(path, sizeof(path), "/proc/%d/oom_score", pid);
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    int score = 0;
    fscanf(f, "%d", &score);
    fclose(f);
    return score;
}

void set_oom_adj(pid_t pid, int adj) {
    char path[64];
    snprintf(path, sizeof(path),
        "/proc/%d/oom_score_adj", pid);
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f, "%d\n", adj);
    fclose(f);
}

int collect_processes(ProcessInfo *procs, int max) {
    DIR    *d = opendir("/proc");
    if (!d) return 0;
    struct dirent *e;
    int count = 0;

    while ((e = readdir(d)) && count < max) {
        pid_t pid = atoi(e->d_name);
        if (pid <= 0) continue;

        char path[64];
        snprintf(path, sizeof(path), "/proc/%d/comm", pid);
        FILE *f = fopen(path, "r");
        if (!f) continue;

        ProcessInfo *p = &procs[count];
        p->pid    = pid;
        fgets(p->name, sizeof(p->name), f);
        fclose(f);
        p->name[strcspn(p->name,"\n")] = 0;
        p->mem_kb    = get_process_mem_kb(pid);
        p->oom_score = get_oom_score(pid);

        // Protect Julius core services
        if (strstr(p->name, "julius_core") ||
            strstr(p->name, "julius_enclave") ||
            strstr(p->name, "julius_pm")) {
            set_oom_adj(pid, -1000);
            p->priority = 0;
        } else if (strstr(p->name, "julius_")) {
            set_oom_adj(pid, -500);
            p->priority = 1;
        } else {
            p->priority = 2;
        }
        count++;
    }
    closedir(d);
    return count;
}

void sort_by_mem(ProcessInfo *procs, int count) {
    for (int i = 0; i < count-1; i++)
        for (int j = i+1; j < count; j++)
            if (procs[j].mem_kb > procs[i].mem_kb) {
                ProcessInfo tmp = procs[i];
                procs[i] = procs[j];
                procs[j] = tmp;
            }
}

int reclaim_memory(long target_mb) {
    ProcessInfo procs[512];
    int count = collect_processes(procs, 512);
    sort_by_mem(procs, count);

    long reclaimed = 0;
    int  killed    = 0;

    for (int i = 0; i < count && reclaimed < target_mb*1024; i++) {
        if (procs[i].priority < 2) continue;
        if (procs[i].mem_kb < 1024) continue;

        char msg[128];
        snprintf(msg, sizeof(msg),
            "Terminating %s (PID %d, %ldMB)",
            procs[i].name, procs[i].pid,
            procs[i].mem_kb/1024);
        mm_log("WARN", msg);

        kill(procs[i].pid, SIGTERM);
        reclaimed += procs[i].mem_kb;
        killed++;
    }
    return killed;
}

void print_mem_stats(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return;
    char  line[256];
    long  total=0, free2=0, avail=0, cached=0;
    while (fgets(line, sizeof(line), f)) {
        if      (strncmp(line,"MemTotal:",9)==0)
            sscanf(line,"MemTotal: %ld",&total);
        else if (strncmp(line,"MemFree:",8)==0)
            sscanf(line,"MemFree: %ld",&free2);
        else if (strncmp(line,"MemAvailable:",13)==0)
            sscanf(line,"MemAvailable: %ld",&avail);
        else if (strncmp(line,"Cached:",7)==0)
            sscanf(line,"Cached: %ld",&cached);
    }
    fclose(f);
    char msg[128];
    snprintf(msg,sizeof(msg),
        "Total:%ldMB Free:%ldMB Avail:%ldMB Cached:%ldMB",
        total/1024, free2/1024, avail/1024, cached/1024);
    mm_log("INFO", msg);
}

int main(void) {
    printf("[MM] Julius Memory Manager v%s\n", MM_VERSION);

    while (1) {
        long avail = get_available_mem_mb();
        char msg[128];

        if (avail < 0) {
            mm_log("ERROR", "Cannot read memory info");
        } else if (avail < CRITICAL_MEM_MB) {
            snprintf(msg, sizeof(msg),
                "CRITICAL: %ldMB available — killing processes",
                avail);
            mm_log("CRIT", msg);
            reclaim_memory(CRITICAL_MEM_MB * 2);
        } else if (avail < LOW_MEM_MB) {
            snprintf(msg, sizeof(msg),
                "LOW: %ldMB available — reclaiming memory",
                avail);
            mm_log("WARN", msg);
            reclaim_memory(LOW_MEM_MB);
        } else {
            snprintf(msg, sizeof(msg),
                "OK: %ldMB available", avail);
            mm_log("INFO", msg);
        }

        print_mem_stats();
        sleep(CHECK_INTERVAL);
    }
    return 0;
}
