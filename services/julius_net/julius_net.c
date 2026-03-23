#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <ifaddrs.h>
#include <netdb.h>
#include <time.h>
#include <errno.h>

#define NET_SOCKET   "/var/run/julius_net.sock"
#define NET_LOG      "/var/log/julius_net.log"
#define NET_STATE    "/var/run/julius_net.state"
#define NET_VERSION  "1.0"
#define DNS_CACHE_SIZE 256
#define CONN_TRACK_SIZE 512

typedef struct {
    char    hostname[256];
    char    ip[16];
    time_t  cached_at;
    int     ttl;
} DNSCacheEntry;

typedef struct {
    char    local_ip[16];
    int     local_port;
    char    remote_ip[16];
    int     remote_port;
    char    state[16];
    char    process[64];
    time_t  established;
    uint64_t bytes_sent;
    uint64_t bytes_recv;
} ConnTrackEntry;

typedef struct {
    char    name[32];
    char    ip[16];
    char    gateway[16];
    char    dns1[16];
    char    dns2[16];
    int     active;
    uint64_t rx_bytes;
    uint64_t tx_bytes;
    int     signal;
} NetInterface;

static DNSCacheEntry   dns_cache[DNS_CACHE_SIZE];
static int             dns_count = 0;
static ConnTrackEntry  conn_track[CONN_TRACK_SIZE];
static int             conn_count = 0;
static NetInterface    interfaces[8];
static int             iface_count = 0;
static pthread_mutex_t net_lock = PTHREAD_MUTEX_INITIALIZER;

void net_log(const char *msg) {
    FILE *f = fopen(NET_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts,sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f,"[%s] [NET] %s\n", ts, msg);
    fclose(f);
    printf("[NET] %s\n", msg);
}

const char *dns_lookup(const char *hostname) {
    // Check cache first
    for (int i = 0; i < dns_count; i++) {
        DNSCacheEntry *e = &dns_cache[i];
        if (strcmp(e->hostname, hostname)==0) {
            if (time(NULL)-e->cached_at < e->ttl)
                return e->ip;
        }
    }

    // Real DNS lookup
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family   = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(hostname, NULL, &hints, &res) != 0)
        return NULL;

    char ip[16];
    struct sockaddr_in *addr =
        (struct sockaddr_in*)res->ai_addr;
    inet_ntop(AF_INET, &addr->sin_addr, ip, sizeof(ip));
    freeaddrinfo(res);

    // Cache result
    if (dns_count < DNS_CACHE_SIZE) {
        DNSCacheEntry *e = &dns_cache[dns_count++];
        strncpy(e->hostname, hostname, 255);
        strncpy(e->ip,       ip,       15);
        e->cached_at = time(NULL);
        e->ttl       = 300;
    }

    char msg[128];
    snprintf(msg, sizeof(msg),
        "DNS: %s -> %s", hostname, ip);
    net_log(msg);
    return dns_cache[dns_count-1].ip;
}

void collect_interfaces(void) {
    iface_count = 0;
    struct ifaddrs *ifa, *it;
    if (getifaddrs(&ifa) != 0) return;

    for (it = ifa; it && iface_count<8; it=it->ifa_next) {
        if (!it->ifa_addr) continue;
        if (it->ifa_addr->sa_family != AF_INET) continue;
        if (strcmp(it->ifa_name, "lo") == 0) continue;

        NetInterface *ni = &interfaces[iface_count++];
        strncpy(ni->name, it->ifa_name, 31);
        struct sockaddr_in *sa =
            (struct sockaddr_in*)it->ifa_addr;
        inet_ntop(AF_INET, &sa->sin_addr, ni->ip, 15);
        ni->active = (it->ifa_flags & IFF_UP) ? 1 : 0;

        // Get RX/TX bytes
        char path[128];
        snprintf(path, sizeof(path),
            "/sys/class/net/%s/statistics/rx_bytes",
            ni->name);
        FILE *f = fopen(path, "r");
        if (f) { fscanf(f,"%llu",&ni->rx_bytes); fclose(f); }
        snprintf(path, sizeof(path),
            "/sys/class/net/%s/statistics/tx_bytes",
            ni->name);
        f = fopen(path, "r");
        if (f) { fscanf(f,"%llu",&ni->tx_bytes); fclose(f); }
    }
    freeifaddrs(ifa);
}

void collect_connections(void) {
    conn_count = 0;
    FILE *f = fopen("/proc/net/tcp", "r");
    if (!f) return;
    char line[512];
    fgets(line, sizeof(line), f); // skip header
    while (fgets(line, sizeof(line), f) &&
           conn_count < CONN_TRACK_SIZE) {
        ConnTrackEntry *c = &conn_track[conn_count];
        unsigned int la, lp, ra, rp, st;
        sscanf(line, " %*d: %x:%x %x:%x %x",
            &la, &lp, &ra, &rp, &st);
        struct in_addr local_addr  = {la};
        struct in_addr remote_addr = {ra};
        inet_ntop(AF_INET, &local_addr,  c->local_ip,  15);
        inet_ntop(AF_INET, &remote_addr, c->remote_ip, 15);
        c->local_port  = ntohs(lp);
        c->remote_port = ntohs(rp);
        const char *states[] = {
            "UNKNOWN","ESTABLISHED","SYN_SENT","SYN_RECV",
            "FIN_WAIT1","FIN_WAIT2","TIME_WAIT","CLOSE",
            "CLOSE_WAIT","LAST_ACK","LISTEN","CLOSING"
        };
        strncpy(c->state,
            st<12?states[st]:"UNKNOWN", 15);
        conn_count++;
    }
    fclose(f);
}

void save_net_state(void) {
    FILE *f = fopen(NET_STATE, "w");
    if (!f) return;
    for (int i = 0; i < iface_count; i++) {
        NetInterface *ni = &interfaces[i];
        fprintf(f, "iface_%s_ip=%s\n",   ni->name, ni->ip);
        fprintf(f, "iface_%s_up=%d\n",   ni->name, ni->active);
        fprintf(f, "iface_%s_rx=%llu\n", ni->name, ni->rx_bytes);
        fprintf(f, "iface_%s_tx=%llu\n", ni->name, ni->tx_bytes);
    }
    fprintf(f, "connections=%d\n", conn_count);
    fprintf(f, "dns_cache=%d\n",   dns_count);
    fclose(f);
}

int main(void) {
    printf("[NET] Julius Network Stack v%s\n", NET_VERSION);

    while (1) {
        pthread_mutex_lock(&net_lock);
        collect_interfaces();
        collect_connections();
        save_net_state();
        pthread_mutex_unlock(&net_lock);

        char msg[256] = "Interfaces: ";
        for (int i = 0; i < iface_count; i++) {
            char tmp[64];
            snprintf(tmp, sizeof(tmp),
                "%s(%s) ",
                interfaces[i].name, interfaces[i].ip);
            strncat(msg, tmp, sizeof(msg)-strlen(msg)-1);
        }
        net_log(msg);

        sleep(30);
    }
    return 0;
}
