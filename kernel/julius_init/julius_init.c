#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/reboot.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>

#define JULIUS_VERSION "1.3"
#define INIT_LOG       "/var/log/julius_init.log"

typedef enum {
    PHASE_KERNEL   = 0,
    PHASE_MOUNT    = 1,
    PHASE_DEVICES  = 2,
    PHASE_NETWORK  = 3,
    PHASE_SERVICES = 4,
    PHASE_UI       = 5,
    PHASE_READY    = 6,
} BootPhase;

static BootPhase current_phase = PHASE_KERNEL;
static FILE     *init_log      = NULL;

void init_log_msg(const char *level, const char *msg) {
    if (!init_log)
        init_log = fopen(INIT_LOG, "w");
    if (!init_log) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts, sizeof(ts),
        "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(init_log, "[%s] [%s] %s\n", ts, level, msg);
    fflush(init_log);
    printf("[INIT] [%s] %s\n", level, msg);
}

void print_julius_banner(void) {
    printf("\n");
    printf("     ██╗██╗   ██╗██╗     ██╗██╗   ██╗███████╗\n");
    printf("     ██║██║   ██║██║     ██║██║   ██║██╔════╝\n");
    printf("     ██║██║   ██║██║     ██║██║   ██║███████╗\n");
    printf("██   ██║██║   ██║██║     ██║██║   ██║╚════██║\n");
    printf("╚█████╔╝╚██████╔╝███████╗██║╚██████╔╝███████║\n");
    printf(" ╚════╝  ╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚══════╝\n");
    printf("                    OS v%s\n\n", JULIUS_VERSION);
    fflush(stdout);
}

// Phase 1 — Mount essential filesystems
int phase_mount(void) {
    init_log_msg("INFO", "Mounting filesystems...");
    struct {
        const char *src;
        const char *dst;
        const char *type;
        unsigned long flags;
    } mounts[] = {
        {"proc",     "/proc",     "proc",     MS_NOSUID|MS_NOEXEC|MS_NODEV},
        {"sysfs",    "/sys",      "sysfs",    MS_NOSUID|MS_NOEXEC|MS_NODEV},
        {"devtmpfs", "/dev",      "devtmpfs", MS_NOSUID},
        {"devpts",   "/dev/pts",  "devpts",   MS_NOSUID|MS_NOEXEC},
        {"tmpfs",    "/dev/shm",  "tmpfs",    MS_NOSUID|MS_NODEV},
        {"tmpfs",    "/tmp",      "tmpfs",    MS_NOSUID|MS_NODEV},
        {"tmpfs",    "/run",      "tmpfs",    MS_NOSUID|MS_NODEV},
        {"cgroup2",  "/sys/fs/cgroup","cgroup2",MS_NOSUID|MS_NOEXEC|MS_NODEV},
        {NULL, NULL, NULL, 0}
    };

    for (int i = 0; mounts[i].src; i++) {
        mkdir(mounts[i].dst, 0755);
        if (mount(mounts[i].src, mounts[i].dst,
                mounts[i].type, mounts[i].flags, NULL) != 0) {
            if (errno != EBUSY) {
                char err[128];
                snprintf(err, sizeof(err),
                    "Failed to mount %s: %s",
                    mounts[i].dst, strerror(errno));
                init_log_msg("WARN", err);
            }
        } else {
            char msg[64];
            snprintf(msg, sizeof(msg),
                "Mounted %s", mounts[i].dst);
            init_log_msg("INFO", msg);
        }
    }

    // Mount data partition
    mkdir("/data", 0755);
    if (mount("/dev/mmcblk0p2", "/data",
            "ext4", MS_RELATIME, NULL) != 0)
        init_log_msg("WARN", "Data partition not mounted");
    else
        init_log_msg("INFO", "Data partition mounted");

    return 0;
}

// Phase 2 — Initialize devices
int phase_devices(void) {
    init_log_msg("INFO", "Initializing devices...");

    // Create device nodes
    mknod("/dev/null",    S_IFCHR|0666, makedev(1,3));
    mknod("/dev/zero",    S_IFCHR|0666, makedev(1,5));
    mknod("/dev/random",  S_IFCHR|0444, makedev(1,8));
    mknod("/dev/urandom", S_IFCHR|0444, makedev(1,9));
    mknod("/dev/console", S_IFCHR|0600, makedev(5,1));
    mknod("/dev/tty",     S_IFCHR|0666, makedev(5,0));
    mknod("/dev/fb0",     S_IFCHR|0660, makedev(29,0));
    mknod("/dev/input/event0", S_IFCHR|0660, makedev(13,64));
    mknod("/dev/spidev0.0",    S_IFCHR|0660, makedev(153,0));
    mknod("/dev/i2c-0",        S_IFCHR|0660, makedev(89,0));

    // Set hostname
    int fd = open("/proc/sys/kernel/hostname", O_WRONLY);
    if (fd >= 0) {
        write(fd, "julius", 6);
        close(fd);
    }

    // Set timezone
    setenv("TZ", "Asia/Kolkata", 1);

    // Kernel parameters
    system("echo 1 > /proc/sys/net/ipv4/ip_forward");
    system("echo 3 > /proc/sys/vm/drop_caches");
    system("echo 100 > /proc/sys/vm/swappiness");
    system("ulimit -n 65535");

    init_log_msg("INFO", "Devices initialized");
    return 0;
}

// Phase 3 — Network early init
int phase_network(void) {
    init_log_msg("INFO", "Initializing network...");
    system("ip link set lo up");
    system("ip addr add 127.0.0.1/8 dev lo");
    init_log_msg("INFO", "Loopback configured");
    return 0;
}

// Phase 4 — Start backend services
int phase_services(void) {
    init_log_msg("INFO", "Starting Julius OS services...");

    // Create required directories
    const char *dirs[] = {
        "/var/run", "/var/log", "/var/julius",
        "/var/julius/sync", "/var/julius/drops",
        "/var/julius/appdata", "/var/julius/sandbox",
        "/etc/julius", "/usr/julius",
        NULL
    };
    for (int i = 0; dirs[i]; i++)
        mkdir(dirs[i], 0755);

    // Service startup order — critical first
    const char *services[] = {
        "/usr/bin/julius_audit",       // Audit first
        "/usr/bin/julius_enclave",     // Security enclave
        "/usr/bin/julius_ipc",         // IPC broker
        "/usr/bin/julius_keychain",    // Keychain
        "/usr/bin/julius_permissions", // Permissions
        "/usr/bin/julius_power",       // Power manager
        "/usr/bin/julius_wifi",        // WiFi
        "/usr/bin/julius_bt",          // Bluetooth
        "/usr/bin/julius_net",         // Network stack
        "/usr/bin/julius_push",        // Push notifications
        "/usr/bin/julius_sync",        // Sync engine
        "/usr/bin/julius_health",      // Health monitor
        "/usr/bin/julius_pm",          // Process manager (last)
        NULL
    };

    for (int i = 0; services[i]; i++) {
        if (access(services[i], X_OK) != 0) {
            char msg[128];
            snprintf(msg, sizeof(msg),
                "Service not found: %s", services[i]);
            init_log_msg("WARN", msg);
            continue;
        }

        pid_t pid = fork();
        if (pid == 0) {
            setsid();
            char *argv[] = { (char*)services[i], NULL };
            execv(services[i], argv);
            exit(1);
        } else if (pid > 0) {
            char msg[128];
            snprintf(msg, sizeof(msg),
                "Started: %s (PID %d)",
                services[i], pid);
            init_log_msg("INFO", msg);
            usleep(100000); // 100ms between services
        }
    }

    sleep(2); // Wait for services to stabilize
    init_log_msg("INFO", "All services started");
    return 0;
}

// Phase 5 — Start UI
int phase_ui(void) {
    init_log_msg("INFO", "Starting Julius OS UI...");

    // Set display environment
    setenv("SDL_VIDEODRIVER", "fbcon",  1);
    setenv("SDL_FBDEV",       "/dev/fb0",1);
    setenv("DISPLAY",         ":0",     1);
    setenv("PYTHONPATH",
        "/usr/julius/src", 1);

    pid_t pid = fork();
    if (pid == 0) {
        setsid();
        char *argv[] = {
            "/usr/bin/python3",
            "/usr/julius/src/julius_ui.py",
            NULL
        };
        execv("/usr/bin/python3", argv);
        exit(1);
    } else if (pid > 0) {
        char msg[64];
        snprintf(msg, sizeof(msg),
            "UI started (PID %d)", pid);
        init_log_msg("INFO", msg);
    }
    return 0;
}

void signal_handler(int sig) {
    if (sig == SIGCHLD) {
        int status;
        pid_t pid;
        while ((pid=waitpid(-1,&status,WNOHANG)) > 0) {
            char msg[64];
            snprintf(msg, sizeof(msg),
                "PID %d exited", pid);
            init_log_msg("INFO", msg);
        }
    }
    if (sig == SIGTERM || sig == SIGINT) {
        init_log_msg("INFO", "Shutting down Julius OS...");
        system("/usr/bin/julius_pm stop-all");
        sync();
        reboot(RB_POWER_OFF);
    }
}

int main(int argc, char *argv[]) {
    // We are PID 1
    if (getpid() != 1) {
        fprintf(stderr, "julius_init must be PID 1\n");
        return 1;
    }

    print_julius_banner();
    init_log_msg("INFO",
        "Julius OS init starting — Linux 6.6 LTS");

    signal(SIGCHLD, signal_handler);
    signal(SIGTERM, signal_handler);
    signal(SIGINT,  signal_handler);
    signal(SIGHUP,  SIG_IGN);

    // Boot sequence
    struct {
        const char *name;
        int (*fn)(void);
    } phases[] = {
        {"Mount Filesystems",  phase_mount},
        {"Initialize Devices", phase_devices},
        {"Network Early Init", phase_network},
        {"Start Services",     phase_services},
        {"Start UI",           phase_ui},
        {NULL, NULL}
    };

    for (int i = 0; phases[i].name; i++) {
        char msg[64];
        snprintf(msg, sizeof(msg),
            "Phase %d: %s", i+1, phases[i].name);
        init_log_msg("INFO", msg);
        printf("\033[32m[OK]\033[0m %s\n", phases[i].name);

        if (phases[i].fn() != 0) {
            char err[64];
            snprintf(err, sizeof(err),
                "Phase failed: %s", phases[i].name);
            init_log_msg("ERROR", err);
            printf("\033[31m[FAIL]\033[0m %s\n",
                phases[i].name);
        }
    }

    current_phase = PHASE_READY;
    init_log_msg("INFO", "Julius OS boot complete");
    printf("\n\033[32m Julius OS v%s ready\033[0m\n\n",
        JULIUS_VERSION);

    // PID 1 main loop — reap zombies forever
    while (1) {
        int   status;
        pid_t pid = wait(&status);
        if (pid > 0) {
            char msg[64];
            snprintf(msg, sizeof(msg),
                "Reaped PID %d", pid);
            init_log_msg("DEBUG", msg);
        }
        sleep(1);
    }
    return 0;
}
