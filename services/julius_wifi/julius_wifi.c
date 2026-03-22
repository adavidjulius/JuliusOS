#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/wireless.h>
#include <sys/ioctl.h>
#include <pthread.h>

#define WIFI_INTERFACE  "wlan0"
#define WIFI_CONFIG     "/etc/julius/wifi.conf"
#define WIFI_STATE_FILE "/var/run/julius_wifi.state"
#define WIFI_LOG        "/var/log/julius_wifi.log"

typedef struct {
    char ssid[64];
    char bssid[18];
    int  signal;
    int  freq;
    char security[32];
} WifiNetwork;

typedef struct {
    int         connected;
    char        ssid[64];
    char        ip[16];
    int         signal;
    int         enabled;
} WifiState;

static WifiState state = {0};
static pthread_mutex_t wifi_lock = PTHREAD_MUTEX_INITIALIZER;

void wifi_log(const char *msg) {
    FILE *f = fopen(WIFI_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(f, "[%s] %s\n", ts, msg);
    fclose(f);
}

int wifi_enable(void) {
    wifi_log("Enabling WiFi...");
    int ret = system("ip link set " WIFI_INTERFACE " up");
    if (ret == 0) {
        pthread_mutex_lock(&wifi_lock);
        state.enabled = 1;
        pthread_mutex_unlock(&wifi_lock);
        wifi_log("WiFi enabled");
        return 0;
    }
    wifi_log("WiFi enable failed");
    return -1;
}

int wifi_disable(void) {
    wifi_log("Disabling WiFi...");
    system("wpa_cli -i " WIFI_INTERFACE " disconnect");
    int ret = system("ip link set " WIFI_INTERFACE " down");
    if (ret == 0) {
        pthread_mutex_lock(&wifi_lock);
        state.enabled    = 0;
        state.connected  = 0;
        memset(state.ssid, 0, sizeof(state.ssid));
        memset(state.ip,   0, sizeof(state.ip));
        pthread_mutex_unlock(&wifi_lock);
        wifi_log("WiFi disabled");
        return 0;
    }
    return -1;
}

int wifi_scan(WifiNetwork *networks, int max) {
    wifi_log("Scanning for networks...");
    system("wpa_cli -i " WIFI_INTERFACE " scan > /dev/null 2>&1");
    sleep(2);

    FILE *f = popen("wpa_cli -i " WIFI_INTERFACE " scan_results", "r");
    if (!f) return 0;

    char line[256];
    int  count = 0;
    fgets(line, sizeof(line), f); // skip header

    while (fgets(line, sizeof(line), f) && count < max) {
        WifiNetwork *net = &networks[count];
        char bssid[18], freq[8], signal[8], flags[128], ssid[64];
        if (sscanf(line, "%17s %7s %7s %127s %63[^\n]",
                bssid, freq, signal, flags, ssid) >= 4) {
            strncpy(net->bssid,    bssid,  sizeof(net->bssid)-1);
            strncpy(net->ssid,     ssid,   sizeof(net->ssid)-1);
            net->freq   = atoi(freq);
            net->signal = atoi(signal);
            if (strstr(flags, "WPA2")) strncpy(net->security,"WPA2",sizeof(net->security)-1);
            else if (strstr(flags, "WPA")) strncpy(net->security,"WPA",sizeof(net->security)-1);
            else strncpy(net->security,"Open",sizeof(net->security)-1);
            count++;
        }
    }
    pclose(f);
    char msg[64];
    snprintf(msg, sizeof(msg), "Found %d networks", count);
    wifi_log(msg);
    return count;
}

int wifi_connect(const char *ssid, const char *password) {
    char msg[128];
    snprintf(msg, sizeof(msg), "Connecting to: %s", ssid);
    wifi_log(msg);

    // Write wpa_supplicant config
    FILE *f = fopen("/tmp/julius_wpa.conf", "w");
    if (!f) return -1;
    fprintf(f, "ctrl_interface=/var/run/wpa_supplicant\n");
    fprintf(f, "network={\n");
    fprintf(f, "    ssid=\"%s\"\n", ssid);
    if (password && strlen(password) > 0)
        fprintf(f, "    psk=\"%s\"\n", password);
    else
        fprintf(f, "    key_mgmt=NONE\n");
    fprintf(f, "}\n");
    fclose(f);

    system("killall wpa_supplicant 2>/dev/null");
    sleep(1);
    int ret = system("wpa_supplicant -B -i " WIFI_INTERFACE
                     " -c /tmp/julius_wpa.conf");
    if (ret != 0) return -1;

    sleep(3);
    ret = system("udhcpc -i " WIFI_INTERFACE " -q");
    if (ret != 0) return -1;

    // Get IP
    FILE *ip_f = popen("ip addr show " WIFI_INTERFACE
                       " | grep 'inet ' | awk '{print $2}'"
                       " | cut -d/ -f1", "r");
    if (ip_f) {
        pthread_mutex_lock(&wifi_lock);
        fgets(state.ip, sizeof(state.ip), ip_f);
        state.ip[strcspn(state.ip, "\n")] = 0;
        strncpy(state.ssid, ssid, sizeof(state.ssid)-1);
        state.connected = 1;
        pthread_mutex_unlock(&wifi_lock);
        pclose(ip_f);
    }

    snprintf(msg, sizeof(msg), "Connected to %s, IP: %s", ssid, state.ip);
    wifi_log(msg);
    return 0;
}

void wifi_disconnect(void) {
    wifi_log("Disconnecting...");
    system("wpa_cli -i " WIFI_INTERFACE " disconnect");
    system("killall wpa_supplicant 2>/dev/null");
    system("ip addr flush dev " WIFI_INTERFACE);
    pthread_mutex_lock(&wifi_lock);
    state.connected = 0;
    memset(state.ssid, 0, sizeof(state.ssid));
    memset(state.ip,   0, sizeof(state.ip));
    pthread_mutex_unlock(&wifi_lock);
}

WifiState wifi_get_state(void) {
    pthread_mutex_lock(&wifi_lock);
    WifiState s = state;
    pthread_mutex_unlock(&wifi_lock);

    // Get signal strength
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd >= 0) {
        struct iwreq req;
        struct iw_statistics stats;
        req.u.data.pointer = &stats;
        req.u.data.length  = sizeof(stats);
        req.u.data.flags   = 1;
        strncpy(req.ifr_name, WIFI_INTERFACE, IFNAMSIZ);
        if (ioctl(fd, SIOCGIWSTATS, &req) >= 0)
            s.signal = stats.qual.level - 256;
        close(fd);
    }
    return s;
}

void wifi_save_config(const char *ssid, const char *password) {
    FILE *f = fopen(WIFI_CONFIG, "w");
    if (!f) return;
    fprintf(f, "ssid=%s\n", ssid);
    fprintf(f, "password=%s\n", password);
    fclose(f);
}

int wifi_auto_connect(void) {
    FILE *f = fopen(WIFI_CONFIG, "r");
    if (!f) return -1;
    char ssid[64]="", password[64]="", line[128];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line,"ssid=",5)==0)
            ssid[0] && strncpy(ssid,line+5,sizeof(ssid)-1);
        else if (strncmp(line,"password=",9)==0)
            strncpy(password,line+9,sizeof(password)-1);
    }
    fclose(f);
    ssid[strcspn(ssid,"\n")]         = 0;
    password[strcspn(password,"\n")] = 0;
    if (strlen(ssid) > 0)
        return wifi_connect(ssid, password);
    return -1;
}

int main(void) {
    printf("[WiFi] Julius WiFi daemon starting...\n");
    wifi_enable();
    wifi_auto_connect();

    while (1) {
        WifiState s = wifi_get_state();
        FILE *f = fopen(WIFI_STATE_FILE, "w");
        if (f) {
            fprintf(f, "connected=%d\n", s.connected);
            fprintf(f, "ssid=%s\n",      s.ssid);
            fprintf(f, "ip=%s\n",        s.ip);
            fprintf(f, "signal=%d\n",    s.signal);
            fprintf(f, "enabled=%d\n",   s.enabled);
            fclose(f);
        }
        sleep(10);
    }
    return 0;
}
