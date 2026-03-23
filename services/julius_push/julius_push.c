#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <json-c/json.h>

#define PUSH_SOCKET  "/var/run/julius_push.sock"
#define PUSH_LOG     "/var/log/julius_push.log"
#define PUSH_VERSION "1.0"
#define MAX_NOTIFS   256

typedef enum {
    PUSH_SEND    = 1,
    PUSH_CANCEL  = 2,
    PUSH_LIST    = 3,
    PUSH_CLEAR   = 4,
    PUSH_BADGE   = 5,
} PushOp;

typedef struct {
    PushOp  op;
    char    app[64];
    char    title[128];
    char    body[256];
    char    action[64];
    int     badge;
    int     sound;
    int     priority;
    uint32_t notif_id;
} PushRequest;

typedef struct {
    uint32_t id;
    char     app[64];
    char     title[128];
    char     body[256];
    char     action[64];
    int      badge;
    int      sound;
    int      priority;
    time_t   timestamp;
    int      delivered;
    int      read;
} PushNotification;

static PushNotification notifs[MAX_NOTIFS];
static int              notif_count = 0;
static uint32_t         next_id     = 1;
static pthread_mutex_t  push_lock   = PTHREAD_MUTEX_INITIALIZER;

void push_log(const char *msg) {
    FILE *f = fopen(PUSH_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts,sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [PUSH] %s\n", ts, msg);
    fclose(f);
    printf("[PUSH] %s\n", msg);
}

void write_notif_file(void) {
    FILE *f = fopen("/var/run/julius_notifications.json","w");
    if (!f) return;
    fprintf(f, "[\n");
    pthread_mutex_lock(&push_lock);
    for (int i = 0; i < notif_count; i++) {
        PushNotification *n = &notifs[i];
        char ts[32];
        struct tm *tm = localtime(&n->timestamp);
        strftime(ts, sizeof(ts), "%H:%M", tm);
        fprintf(f,
            "  {\"app\":\"%s\",\"title\":\"%s\","
            "\"body\":\"%s\",\"time\":\"%s\","
            "\"color\":[10,132,255],\"read\":%s}%s\n",
            n->app, n->title, n->body, ts,
            n->read ? "true" : "false",
            i < notif_count-1 ? "," : "");
    }
    pthread_mutex_unlock(&push_lock);
    fprintf(f, "]\n");
    fclose(f);
}

uint32_t push_send(PushRequest *req) {
    pthread_mutex_lock(&push_lock);
    if (notif_count >= MAX_NOTIFS) {
        memmove(&notifs[0], &notifs[1],
            (MAX_NOTIFS-1)*sizeof(PushNotification));
        notif_count--;
    }
    PushNotification *n = &notifs[notif_count++];
    n->id        = next_id++;
    n->timestamp = time(NULL);
    n->delivered = 1;
    n->read      = 0;
    strncpy(n->app,    req->app,    63);
    strncpy(n->title,  req->title,  127);
    strncpy(n->body,   req->body,   255);
    strncpy(n->action, req->action, 63);
    n->badge     = req->badge;
    n->sound     = req->sound;
    n->priority  = req->priority;
    pthread_mutex_unlock(&push_lock);
    write_notif_file();
    char msg[256];
    snprintf(msg, sizeof(msg),
        "Notification: [%s] %s", req->app, req->title);
    push_log(msg);
    return n->id;
}

void handle_push_client(int fd) {
    PushRequest req;
    while (read(fd, &req, sizeof(req)) == sizeof(req)) {
        switch (req.op) {
        case PUSH_SEND: {
            uint32_t id = push_send(&req);
            write(fd, &id, sizeof(id));
            break;
        }
        case PUSH_CLEAR:
            pthread_mutex_lock(&push_lock);
            notif_count = 0;
            pthread_mutex_unlock(&push_lock);
            write_notif_file();
            break;
        case PUSH_LIST: {
            char buf[4096] = {0};
            int  pos = 0;
            pthread_mutex_lock(&push_lock);
            for (int i = 0; i < notif_count; i++)
                pos += snprintf(buf+pos, sizeof(buf)-pos,
                    "%s: %s\n",
                    notifs[i].app, notifs[i].title);
            pthread_mutex_unlock(&push_lock);
            write(fd, buf, sizeof(buf));
            break;
        }
        }
    }
    close(fd);
}

void *push_thread(void *arg) {
    int fd = *(int*)arg;
    free(arg);
    handle_push_client(fd);
    return NULL;
}

// Built-in notifications on startup
void push_startup_notifs(void) {
    PushRequest r = {
        .op       = PUSH_SEND,
        .priority = 1,
        .sound    = 0,
    };
    strcpy(r.app,   "Julius OS");
    strcpy(r.title, "System Ready");
    strcpy(r.body,  "All services running");
    push_send(&r);
}

int main(void) {
    printf("[PUSH] Julius Push Service v%s\n", PUSH_VERSION);
    push_startup_notifs();

    int srv = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) return 1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, PUSH_SOCKET,sizeof(addr.sun_path)-1);
    unlink(PUSH_SOCKET);
    bind(srv, (struct sockaddr*)&addr, sizeof(addr));
    chmod(PUSH_SOCKET, 0666);
    listen(srv, 16);

    push_log("Push Service ready");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(srv, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, push_thread, cfd);
        pthread_detach(tid);
    }
    return 0;
}
