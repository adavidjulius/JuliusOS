#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sched.h>
#include <seccomp.h>
#include <linux/seccomp.h>
#include <fcntl.h>
#include <pwd.h>
#include <grp.h>
#include <time.h>

#define SANDBOX_VERSION "1.0"
#define SANDBOX_ROOT    "/var/julius/sandbox"
#define SANDBOX_LOG     "/var/log/julius_sandbox.log"

typedef struct {
    char app_name[64];
    char sandbox_path[256];
    char allowed_paths[16][256];
    int  allowed_count;
    int  allow_network;
    int  allow_camera;
    int  allow_mic;
    int  allow_location;
    uid_t uid;
    gid_t gid;
} SandboxProfile;

void sandbox_log(const char *level, const char *msg) {
    FILE *f = fopen(SANDBOX_LOG, "a");
    if (!f) return;
    time_t now = time(NULL);
    char   ts[32];
    strftime(ts,sizeof(ts),"%Y-%m-%d %H:%M:%S",localtime(&now));
    fprintf(f, "[%s] [SANDBOX/%s] %s\n", ts, level, msg);
    fclose(f);
    printf("[SANDBOX] [%s] %s\n", level, msg);
}

SandboxProfile get_default_profile(const char *app_name) {
    SandboxProfile p;
    memset(&p, 0, sizeof(p));
    strncpy(p.app_name, app_name, 63);
    snprintf(p.sandbox_path, sizeof(p.sandbox_path),
        "%s/%s", SANDBOX_ROOT, app_name);

    // Default: no network, no camera, no mic, no location
    p.allow_network  = 0;
    p.allow_camera   = 0;
    p.allow_mic      = 0;
    p.allow_location = 0;
    p.uid            = 1000;
    p.gid            = 1000;

    // Allow read-only access to app bundle
    snprintf(p.allowed_paths[p.allowed_count++],
        255, "/usr/julius/apps/%s", app_name);
    // Allow write to app data dir
    snprintf(p.allowed_paths[p.allowed_count++],
        255, "/var/julius/appdata/%s", app_name);
    // Allow temp
    strncpy(p.allowed_paths[p.allowed_count++],
        "/tmp", 255);

    // Network apps
    if (strcmp(app_name,"WiFi")==0 ||
        strcmp(app_name,"Scanner")==0 ||
        strcmp(app_name,"NetTools")==0 ||
        strcmp(app_name,"SSH")==0)
        p.allow_network = 1;

    return p;
}

int setup_seccomp(const SandboxProfile *p) {
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    if (!ctx) return -1;

    // Allow basic syscalls
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read),    0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open),    0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(stat),    0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(fstat),   0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mmap),    0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(munmap),  0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(brk),     0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit),    0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group),0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(getpid),  0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(getuid),  0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(futex),   0);

    // Allow network if permitted
    if (p->allow_network) {
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(socket),  0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(connect), 0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(sendto),  0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(recvfrom),0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(bind),    0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(listen),  0);
        seccomp_rule_add(ctx, SCMP_ACT_ALLOW,
            SCMP_SYS(accept),  0);
    }

    int ret = seccomp_load(ctx);
    seccomp_release(ctx);
    return ret;
}

int sandbox_launch(const char *app_name,
    const char *exec_path) {
    SandboxProfile profile = get_default_profile(app_name);

    char msg[256];
    snprintf(msg, sizeof(msg),
        "Launching %s in sandbox", app_name);
    sandbox_log("INFO", msg);

    pid_t pid = fork();
    if (pid < 0) return -1;

    if (pid == 0) {
        // Child — apply sandbox
        // 1. Set process name
        prctl(PR_SET_NAME, app_name, 0, 0, 0);

        // 2. Drop privileges
        setgid(profile.gid);
        setuid(profile.uid);

        // 3. Apply seccomp filter
        if (setup_seccomp(&profile) != 0) {
            sandbox_log("ERROR", "Seccomp setup failed");
            exit(1);
        }

        // 4. Create sandbox dir
        mkdir(profile.sandbox_path, 0750);

        // 5. Execute app
        char *argv[] = { (char*)exec_path, NULL };
        execv(exec_path, argv);
        exit(1);
    }

    snprintf(msg, sizeof(msg),
        "App %s running in sandbox (PID %d)",
        app_name, pid);
    sandbox_log("INFO", msg);
    return pid;
}

int main(int argc, char *argv[]) {
    printf("[SANDBOX] Julius Sandbox v%s\n", SANDBOX_VERSION);

    if (argc < 3) {
        printf("Usage: julius_sandbox <app_name> <exec_path>\n");
        return 1;
    }

    mkdir(SANDBOX_ROOT, 0755);
    int pid = sandbox_launch(argv[1], argv[2]);
    if (pid < 0) {
        sandbox_log("ERROR", "Failed to launch app");
        return 1;
    }

    int status;
    waitpid(pid, &status, 0);

    char msg[128];
    snprintf(msg, sizeof(msg),
        "App %s exited with status %d",
        argv[1], WEXITSTATUS(status));
    sandbox_log("INFO", msg);
    return 0;
}
