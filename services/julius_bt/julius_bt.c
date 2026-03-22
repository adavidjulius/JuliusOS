#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>

#define BT_STATE_FILE "/var/run/julius_bt.state"
#define BT_LOG        "/var/log/julius_bt.log"
#define BT_PAIRS_FILE "/etc/julius/bt_pairs.conf"
#define BT_INTERFACE  "hci0"

typedef struct {
    char addr[18];
    char name[64];
    int  rssi;
    int  paired;
    int  connected;
} BTDevice;

typedef struct {
    int enabled;
    int connected;
    int discoverable;
    int device_count;
    BTDevice devices[32];
} BTState;

static BTState state = {0};
static pthread_mutex_t bt_lock = PTHREAD_MUTEX_INITIALIZER;

void bt_log(const char *msg) {
    FILE *f = fopen(BT_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(f, "[%s] %s\n", ts, msg);
    fclose(f);
}

int bt_enable(void) {
    bt_log("Enabling Bluetooth...");
    int ret = system("hciconfig " BT_INTERFACE " up");
    if (ret == 0) {
        system("hciconfig " BT_INTERFACE " piscan");
        pthread_mutex_lock(&bt_lock);
        state.enabled = 1;
        pthread_mutex_unlock(&bt_lock);
        bt_log("Bluetooth enabled");
        return 0;
    }
    bt_log("Bluetooth enable failed");
    return -1;
}

int bt_disable(void) {
    bt_log("Disabling Bluetooth...");
    system("hciconfig " BT_INTERFACE " down");
    pthread_mutex_lock(&bt_lock);
    state.enabled   = 0;
    state.connected = 0;
    pthread_mutex_unlock(&bt_lock);
    bt_log("Bluetooth disabled");
    return 0;
}

int bt_scan(BTDevice *devices, int max) {
    bt_log("Scanning for BT devices...");
    int dev_id = hci_get_route(NULL);
    int sock   = hci_open_dev(dev_id);
    if (dev_id < 0 || sock < 0) return 0;

    inquiry_info *ii    = NULL;
    int           count = hci_inquiry(dev_id, 8, max, NULL, &ii, IREQ_CACHE_FLUSH);
    if (count < 0) {
        close(sock);
        return 0;
    }

    for (int i = 0; i < count; i++) {
        ba2str(&(ii+i)->bdaddr, devices[i].addr);
        memset(devices[i].name, 0, sizeof(devices[i].name));
        if (hci_read_remote_name(sock, &(ii+i)->bdaddr, sizeof(devices[i].name),
                devices[i].name, 0) < 0)
            strcpy(devices[i].name, "Unknown");
        devices[i].rssi    = 0;
        devices[i].paired  = 0;
        devices[i].connected = 0;
    }

    free(ii);
    close(sock);
    char msg[64];
    snprintf(msg, sizeof(msg), "Found %d BT devices", count);
    bt_log(msg);
    return count;
}

int bt_pair(const char *addr) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd),
        "echo -e 'pair %s\\nyes\\n' | bluetoothctl", addr);
    int ret = system(cmd);
    if (ret == 0) {
        char msg[64];
        snprintf(msg, sizeof(msg), "Paired with %s", addr);
        bt_log(msg);
        // Save to pairs file
        FILE *f = fopen(BT_PAIRS_FILE, "a");
        if (f) { fprintf(f, "%s\n", addr); fclose(f); }
        return 0;
    }
    return -1;
}

int bt_connect(const char *addr) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd),
        "echo 'connect %s' | bluetoothctl", addr);
    int ret = system(cmd);
    if (ret == 0) {
        pthread_mutex_lock(&bt_lock);
        state.connected = 1;
        pthread_mutex_unlock(&bt_lock);
        char msg[64];
        snprintf(msg, sizeof(msg), "Connected to %s", addr);
        bt_log(msg);
        return 0;
    }
    return -1;
}

void bt_disconnect(const char *addr) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd),
        "echo 'disconnect %s' | bluetoothctl", addr);
    system(cmd);
    pthread_mutex_lock(&bt_lock);
    state.connected = 0;
    pthread_mutex_unlock(&bt_lock);
    bt_log("Disconnected");
}

void bt_set_discoverable(int on) {
    if (on) system("hciconfig " BT_INTERFACE " piscan");
    else    system("hciconfig " BT_INTERFACE " noscan");
    pthread_mutex_lock(&bt_lock);
    state.discoverable = on;
    pthread_mutex_unlock(&bt_lock);
}

int main(void) {
    printf("[BT] Julius Bluetooth daemon starting...\n");
    bt_enable();

    while (1) {
        BTState s;
        pthread_mutex_lock(&bt_lock);
        s = state;
        pthread_mutex_unlock(&bt_lock);

        FILE *f = fopen(BT_STATE_FILE, "w");
        if (f) {
            fprintf(f, "enabled=%d\n",      s.enabled);
            fprintf(f, "connected=%d\n",    s.connected);
            fprintf(f, "discoverable=%d\n", s.discoverable);
            fclose(f);
        }
        sleep(15);
    }
    return 0;
}
