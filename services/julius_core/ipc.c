#include "ipc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <pthread.h>
#include <errno.h>

#define IPC_SOCKET_PATH "/var/run/julius_ipc.sock"
#define IPC_MAX_CLIENTS 16
#define IPC_BUF_SIZE    4096

static int      server_fd = -1;
static int      clients[IPC_MAX_CLIENTS];
static int      client_count = 0;
static pthread_mutex_t ipc_lock = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
    char topic[64];
    char data[IPC_BUF_SIZE];
    int  data_len;
} IPCMessage;

int ipc_init(void) {
    server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) return -1;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, IPC_SOCKET_PATH, sizeof(addr.sun_path)-1);

    unlink(IPC_SOCKET_PATH);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0)
        return -1;

    if (listen(server_fd, IPC_MAX_CLIENTS) < 0)
        return -1;

    memset(clients, -1, sizeof(clients));
    return 0;
}

int ipc_send(const char *topic, const void *data, int len) {
    IPCMessage msg;
    memset(&msg, 0, sizeof(msg));
    strncpy(msg.topic, topic, sizeof(msg.topic)-1);
    if (data && len > 0) {
        memcpy(msg.data, data, len < IPC_BUF_SIZE ? len : IPC_BUF_SIZE);
        msg.data_len = len;
    }

    pthread_mutex_lock(&ipc_lock);
    int sent = 0;
    for (int i = 0; i < IPC_MAX_CLIENTS; i++) {
        if (clients[i] >= 0) {
            write(clients[i], &msg, sizeof(msg));
            sent++;
        }
    }
    pthread_mutex_unlock(&ipc_lock);
    return sent;
}

int ipc_broadcast(const char *topic, const void *data, int len) {
    return ipc_send(topic, data, len);
}

int ipc_receive(const char *topic, char *buf, int buflen) {
    IPCMessage msg;
    int        fd = accept(server_fd, NULL, NULL);
    if (fd < 0) return -1;

    int n = read(fd, &msg, sizeof(msg));
    if (n > 0 && strcmp(msg.topic, topic) == 0) {
        int copy = msg.data_len < buflen ? msg.data_len : buflen;
        memcpy(buf, msg.data, copy);
        close(fd);
        return copy;
    }
    close(fd);
    return -1;
}

int ipc_receive_any(char *topic_out, char *buf, int buflen) {
    IPCMessage msg;
    struct timeval tv = {0, 100000};
    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(server_fd, &fds);

    if (select(server_fd+1, &fds, NULL, NULL, &tv) <= 0)
        return -1;

    int fd = accept(server_fd, NULL, NULL);
    if (fd < 0) return -1;

    int n = read(fd, &msg, sizeof(msg));
    if (n > 0) {
        strncpy(topic_out, msg.topic, 63);
        int copy = msg.data_len < buflen ? msg.data_len : buflen;
        memcpy(buf, msg.data, copy);
        close(fd);
        return copy;
    }
    close(fd);
    return -1;
}

void ipc_destroy(void) {
    pthread_mutex_lock(&ipc_lock);
    for (int i = 0; i < IPC_MAX_CLIENTS; i++) {
        if (clients[i] >= 0) {
            close(clients[i]);
            clients[i] = -1;
        }
    }
    pthread_mutex_unlock(&ipc_lock);
    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }
    unlink(IPC_SOCKET_PATH);
}
