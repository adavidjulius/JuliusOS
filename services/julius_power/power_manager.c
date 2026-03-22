#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

#define BATTERY_CAPACITY "/sys/class/power_supply/battery/capacity"
#define BATTERY_STATUS   "/sys/class/power_supply/battery/status"
#define CHARGING_CURRENT "/sys/class/power_supply/magsafe/current_now"
#define POWER_STATE_FILE "/var/run/julius_power.state"
#define LOW_BATTERY_THR  15
#define CRITICAL_THR     5

typedef enum {
    POWER_NORMAL    = 0,
    POWER_LOW       = 1,
    POWER_CRITICAL  = 2,
    POWER_CHARGING  = 3,
    POWER_FULL      = 4,
} PowerState;

typedef struct {
    int        level;
    PowerState state;
    int        charging;
    int        current_ma;
    char       status[32];
} BatteryInfo;

static int read_int_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int val = -1;
    fscanf(f, "%d", &val);
    fclose(f);
    return val;
}

static void read_str_file(const char *path, char *buf, int len) {
    FILE *f = fopen(path, "r");
    if (!f) { buf[0]=0; return; }
    fgets(buf, len, f);
    fclose(f);
    buf[strcspn(buf, "\n")] = 0;
}

BatteryInfo get_battery_info(void) {
    BatteryInfo info = {0};
    info.level       = read_int_file(BATTERY_CAPACITY);
    info.current_ma  = read_int_file(CHARGING_CURRENT) / 1000;
    read_str_file(BATTERY_STATUS, info.status, sizeof(info.status));
    info.charging = (strcmp(info.status, "Charging") == 0 ||
                     strcmp(info.status, "Full") == 0);
    if (info.charging && info.level >= 100)
        info.state = POWER_FULL;
    else if (info.charging)
        info.state = POWER_CHARGING;
    else if (info.level <= CRITICAL_THR)
        info.state = POWER_CRITICAL;
    else if (info.level <= LOW_BATTERY_THR)
        info.state = POWER_LOW;
    else
        info.state = POWER_NORMAL;
    return info;
}

void save_power_state(const BatteryInfo *info) {
    FILE *f = fopen(POWER_STATE_FILE, "w");
    if (!f) return;
    fprintf(f, "level=%d\n",    info->level);
    fprintf(f, "charging=%d\n", info->charging);
    fprintf(f, "state=%d\n",    info->state);
    fprintf(f, "current=%d\n",  info->current_ma);
    fclose(f);
}

void handle_low_battery(const BatteryInfo *info) {
    if (info->state == POWER_CRITICAL) {
        printf("[PWR] CRITICAL: %d%% — initiating safe shutdown\n",
            info->level);
        system("julius_notify 'Battery critical! Shutting down...'");
        sleep(5);
        system("poweroff");
    } else if (info->state == POWER_LOW) {
        printf("[PWR] LOW: %d%% — notifying user\n", info->level);
        system("julius_notify 'Low battery! Please charge.'");
    }
}

void set_brightness_for_battery(const BatteryInfo *info) {
    int brightness = 255;
    if (info->level < 20 && !info->charging)
        brightness = 128;
    else if (info->level < 10 && !info->charging)
        brightness = 64;

    char cmd[128];
    snprintf(cmd, sizeof(cmd),
        "echo %d > /sys/class/backlight/julius_bl/brightness",
        brightness);
    system(cmd);
}

int main(void) {
    printf("[PWR] Julius Power Manager starting...\n");

    while (1) {
        BatteryInfo info = get_battery_info();

        printf("[PWR] Level: %d%% | State: %s | %s | %dmA\n",
            info.level,
            info.state == POWER_CHARGING ? "Charging" :
            info.state == POWER_FULL     ? "Full"     :
            info.state == POWER_LOW      ? "Low"      :
            info.state == POWER_CRITICAL ? "Critical" : "Normal",
            info.status,
            info.current_ma);

        save_power_state(&info);
        handle_low_battery(&info);
        set_brightness_for_battery(&info);

        sleep(30);
    }
    return 0;
}
