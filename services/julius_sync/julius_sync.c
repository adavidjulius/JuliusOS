#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/inotify.h>
#include <dirent.h>
#include <openssl/sha.h>
#include <time.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define SYNC_PORT     9978
#define SYNC_DIR      "/var/julius/sync/"
#define SYNC_LOG      "/var/log/julius_sync.log"
#define SYNC_STATE    "/var/run/julius_sync.state"
#define SYNC_VERSION  "1.0"
#define SYNC_INTERVAL 300

typedef struct {
    char    name[256];
    size_t  size;
    time_t  mtime;
    uint8_t sha256[32];
    int     synced;
} SyncFile;

static char    server_ip[64]  = "";
static int     syncing        = 0;
static time_t  last_sync      = 0;
static int     files_synced   = 0;
static pthread_mutex_t sync_lock = PTHREAD_MUTEX_INITIALIZER;

void sync_log(const char *msg) {
    FILE *f = fopen(SYNC_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts,sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [SYNC] %s\n", ts, msg);
    fclose(f);
    printf("[SYNC] %s\n", msg);
}

void compute_sha256(const char *path, uint8_t *out) {
    FILE *f = fopen(path, "rb");
    if (!f) { memset(out, 0, 32); return; }
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    uint8_t buf[4096];
    int n;
    while ((n=fread(buf,1,sizeof(buf),f)) > 0)
        SHA256_Update(&ctx, buf, n);
    fclose(f);
    SHA256_Final(out, &ctx);
}

int collect_sync_files(SyncFile *files, int max) {
    DIR *d = opendir(SYNC_DIR);
    if (!d) return 0;
    struct dirent *e;
    int count = 0;
    while ((e=readdir(d)) && count < max) {
        if (e->d_name[0] == '.') continue;
        SyncFile *f2 = &files[count];
        strncpy(f2->name, e->d_name, 255);
        char path[512];
        snprintf(path, sizeof(path),
            "%s%s", SYNC_DIR, e->d_name);
        struct stat st;
        if (stat(path, &st) == 0) {
            f2->size  = st.st_size;
            f2->mtime = st.st_mtime;
            compute_sha256(path, f2->sha256);
            f2->synced = 0;
            count++;
        }
    }
    closedir(d);
    return count;
}

int send_file(int sock, const char *path,
    const char *name, size_t size) {
    char header[512];
    snprintf(header, sizeof(header),
        "{\"name\":\"%s\",\"size\":%zu}\n", name, size);
    send(sock, header, strlen(header), 0);

    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    uint8_t buf[4096];
    int n;
    while ((n=fread(buf,1,sizeof(buf),f)) > 0)
        send(sock, buf, n, 0);
    fclose(f);
    return 0;
}

void *sync_thread(void *arg) {
    if (!server_ip[0]) {
        sync_log("No server configured");
        return NULL;
    }

    pthread_mutex_lock(&sync_lock);
    syncing = 1;
    pthread_mutex_unlock(&sync_lock);

    sync_log("Starting sync...");
    mkdir(SYNC_DIR, 0755);

    SyncFile files[256];
    int count = collect_sync_files(files, 256);

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        sync_log("Socket error");
        goto done;
    }

    struct sockaddr_in addr;
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(SYNC_PORT);
    addr.sin_addr.s_addr = inet_addr(server_ip);

    struct timeval tv = {10, 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    if (connect(sock,
            (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        sync_log("Cannot connect to server");
        close(sock);
        goto done;
    }

    // Send manifest
    char manifest[8192] = "{\"action\":\"sync\",\"files\":[";
    for (int i = 0; i < count; i++) {
        char entry[512];
        char hex[65];
        for (int j = 0; j < 32; j++)
            sprintf(hex+j*2,"%02x",files[i].sha256[j]);
        hex[64] = 0;
        snprintf(entry, sizeof(entry),
            "{\"name\":\"%s\",\"size\":%zu,\"hash\":\"%s\"}%s",
            files[i].name, files[i].size, hex,
            i < count-1 ? "," : "");
        strncat(manifest, entry,
            sizeof(manifest)-strlen(manifest)-1);
    }
    strncat(manifest, "]}\n",
        sizeof(manifest)-strlen(manifest)-1);
    send(sock, manifest, strlen(manifest), 0);

    // Receive server response
    char resp[4096] = {0};
    int  n = recv(sock, resp, sizeof(resp)-1, 0);
    if (n > 0) {
        char msg[128];
        snprintf(msg, sizeof(msg),
            "Server response: %d bytes", n);
        sync_log(msg);
    }

    close(sock);
    files_synced = count;
    last_sync    = time(NULL);

    char summary[128];
    snprintf(summary, sizeof(summary),
        "Sync complete: %d files", count);
    sync_log(summary);

done:
    pthread_mutex_lock(&sync_lock);
    syncing = 0;
    pthread_mutex_unlock(&sync_lock);

    // Save state
    FILE *sf = fopen(SYNC_STATE, "w");
    if (sf) {
        fprintf(sf, "last_sync=%ld\n",  (long)last_sync);
        fprintf(sf, "files=%d\n",       files_synced);
        fprintf(sf, "server=%s\n",      server_ip);
        fprintf(sf, "syncing=%d\n",     syncing);
        fclose(sf);
    }
    return NULL;
}

void trigger_sync(void) {
    if (syncing) return;
    pthread_t tid;
    pthread_create(&tid, NULL, sync_thread, NULL);
    pthread_detach(tid);
}

void load_config(void) {
    FILE *f = fopen("/etc/julius/cloud_sync.conf", "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line,"server=",7)==0) {
            strncpy(server_ip, line+7, 63);
            server_ip[strcspn(server_ip,"\n")] = 0;
        }
    }
    fclose(f);
    if (server_ip[0]) {
        char msg[128];
        snprintf(msg,sizeof(msg),"Server: %s",server_ip);
        sync_log(msg);
    }
}

void *watch_thread(void *arg) {
    int ifd = inotify_init();
    if (ifd < 0) return NULL;
    mkdir(SYNC_DIR, 0755);
    inotify_add_watch(ifd, SYNC_DIR,
        IN_CREATE|IN_MODIFY|IN_DELETE);
    char buf[4096];
    while (1) {
        int n = read(ifd, buf, sizeof(buf));
        if (n > 0) {
            sync_log("File change detected — triggering sync");
            sleep(2);
            trigger_sync();
        }
    }
    return NULL;
}

int main(void) {
    printf("[SYNC] Julius Sync Engine v%s\n", SYNC_VERSION);
    mkdir(SYNC_DIR, 0755);
    load_config();

    pthread_t wt;
    pthread_create(&wt, NULL, watch_thread, NULL);
    pthread_detach(wt);

    sync_log("Sync Engine started");

    // Initial sync
    trigger_sync();

    while (1) {
        sleep(SYNC_INTERVAL);
        sync_log("Periodic sync triggered");
        trigger_sync();
    }
    return 0;
}
