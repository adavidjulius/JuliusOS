#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>

#define IPC_SOCKET      "/var/run/julius_ipc.sock"
#define IPC_MAX_CLIENTS 64
#define IPC_MAX_TOPICS  128
#define IPC_BUF_SIZE    8192
#define IPC_VERSION     "1.0"

typedef struct {
    char    topic[64];
    uint8_t data[IPC_BUF_SIZE];
    int     data_len;
    pid_t   sender;
    time_t  timestamp;
    int     flags;
} IPCMessage;

typedef struct {
    int    fd;
    pid_t  pid;
    char   name[64];
    char   subscriptions[IPC_MAX_TOPICS][64];
    int    sub_count;
    time_t connected_at;
} IPCClient;

typedef struct {
    char     topic[64];
    IPCMessage last_msg;
    int      has_last;
} IPCTopic;

static IPCClient clients[IPC_MAX_CLIENTS];
static int       client_count = 0;
static IPCTopic  topics[IPC_MAX_TOPICS];
static int       topic_count  = 0;
static pthread_mutex_t ipc_lock = PTHREAD_MUTEX_INITIALIZER;
static int       server_fd = -1;

void ipc_log(const char *msg) {
    printf("[IPC] %s\n", msg);
    fflush(stdout);
}

IPCClient *find_client(int fd) {
    for (int i = 0; i < client_count; i++)
        if (clients[i].fd == fd)
            return &clients[i];
    return NULL;
}

IPCTopic *find_or_create_topic(const char *topic) {
    for (int i = 0; i < topic_count; i++)
        if (strcmp(topics[i].topic, topic) == 0)
            return &topics[i];
    if (topic_count >= IPC_MAX_TOPICS) return NULL;
    IPCTopic *t = &topics[topic_count++];
    strncpy(t->topic, topic, sizeof(t->topic)-1);
    t->has_last = 0;
    return t;
}

void ipc_publish(const IPCMessage *msg) {
    pthread_mutex_lock(&ipc_lock);

    IPCTopic *t = find_or_create_topic(msg->topic);
    if (t) {
        t->last_msg = *msg;
        t->has_last = 1;
    }

    int delivered = 0;
    for (int i = 0; i < client_count; i++) {
        IPCClient *c = &clients[i];
        for (int j = 0; j < c->sub_count; j++) {
            if (strcmp(c->subscriptions[j], msg->topic) == 0) {
                write(c->fd, msg, sizeof(IPCMessage));
                delivered++;
                break;
            }
        }
    }

    char log_msg[128];
    snprintf(log_msg, sizeof(log_msg),
        "Published: %s -> %d clients", msg->topic, delivered);
    pthread_mutex_unlock(&ipc_lock);
}

void ipc_subscribe(int fd, const char *topic) {
    pthread_mutex_lock(&ipc_lock);
    IPCClient *c = find_client(fd);
    if (c && c->sub_count < IPC_MAX_TOPICS) {
        strncpy(c->subscriptions[c->sub_count++],
            topic, 63);
        // Send last retained message
        IPCTopic *t = find_or_create_topic(topic);
        if (t && t->has_last)
            write(fd, &t->last_msg, sizeof(IPCMessage));
    }
    pthread_mutex_unlock(&ipc_lock);
}

void ipc_unsubscribe(int fd, const char *topic) {
    pthread_mutex_lock(&ipc_lock);
    IPCClient *c = find_client(fd);
    if (c) {
        for (int i = 0; i < c->sub_count; i++) {
            if (strcmp(c->subscriptions[i], topic) == 0) {
                memmove(&c->subscriptions[i],
                    &c->subscriptions[i+1],
                    (c->sub_count-i-1)*64);
                c->sub_count--;
                break;
            }
        }
    }
    pthread_mutex_unlock(&ipc_lock);
}

void remove_client(int fd) {
    pthread_mutex_lock(&ipc_lock);
    for (int i = 0; i < client_count; i++) {
        if (clients[i].fd == fd) {
            close(fd);
            memmove(&clients[i], &clients[i+1],
                (client_count-i-1)*sizeof(IPCClient));
            client_count--;
            break;
        }
    }
    pthread_mutex_unlock(&ipc_lock);
}

void *client_handler(void *arg) {
    int fd = *(int*)arg;
    free(arg);

    pthread_mutex_lock(&ipc_lock);
    if (client_count < IPC_MAX_CLIENTS) {
        IPCClient *c     = &clients[client_count++];
        c->fd            = fd;
        c->sub_count     = 0;
        c->connected_at  = time(NULL);
        snprintf(c->name, sizeof(c->name),
            "client_%d", fd);
    }
    pthread_mutex_unlock(&ipc_lock);

    IPCMessage msg;
    while (1) {
        int n = read(fd, &msg, sizeof(msg));
        if (n <= 0) break;
        if (n != sizeof(msg)) continue;

        if (strcmp(msg.topic, "__subscribe__") == 0)
            ipc_subscribe(fd, (char*)msg.data);
        else if (strcmp(msg.topic, "__unsubscribe__") == 0)
            ipc_unsubscribe(fd, (char*)msg.data);
        else
            ipc_publish(&msg);
    }

    remove_client(fd);
    return NULL;
}

void *stats_thread(void *arg) {
    while (1) {
        sleep(60);
        pthread_mutex_lock(&ipc_lock);
        char msg[128];
        snprintf(msg, sizeof(msg),
            "Clients: %d  Topics: %d",
            client_count, topic_count);
        pthread_mutex_unlock(&ipc_lock);
        ipc_log(msg);
    }
    return NULL;
}

int main(void) {
    printf("[IPC] Julius IPC System v%s\n", IPC_VERSION);

    server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); return 1; }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, IPC_SOCKET, sizeof(addr.sun_path)-1);
    unlink(IPC_SOCKET);

    if (bind(server_fd,
            (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind"); return 1;
    }
    chmod(IPC_SOCKET, 0666);
    listen(server_fd, 32);

    pthread_t st;
    pthread_create(&st, NULL, stats_thread, NULL);
    pthread_detach(st);

    ipc_log("IPC System ready");

    while (1) {
        int *cfd = malloc(sizeof(int));
        *cfd = accept(server_fd, NULL, NULL);
        if (*cfd < 0) { free(cfd); continue; }
        pthread_t tid;
        pthread_create(&tid, NULL, client_handler, cfd);
        pthread_detach(tid);
    }
    return 0;
}
