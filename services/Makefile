CC      = gcc
CFLAGS  = -Wall -O2 -pthread
LDFLAGS = -lssl -lcrypto -lpthread

SERVICES = \
    julius_enclave/julius_enclave \
    julius_pm/julius_pm \
    julius_mm/julius_mm \
    julius_ipc/julius_ipc \
    julius_keychain/julius_keychain \
    julius_audit/julius_audit \
    julius_health/julius_health \
    julius_push/julius_push \
    julius_sync/julius_sync \
    julius_net/julius_net \
    julius_sandbox/julius_sandbox \
    julius_permissions/julius_permissions

all: $(SERVICES)

julius_enclave/julius_enclave: julius_enclave/julius_enclave.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_pm/julius_pm: julius_pm/julius_pm.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_mm/julius_mm: julius_mm/julius_mm.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_ipc/julius_ipc: julius_ipc/julius_ipc.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_keychain/julius_keychain: julius_keychain/julius_keychain.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_audit/julius_audit: julius_audit/julius_audit.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_health/julius_health: julius_health/julius_health.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_push/julius_push: julius_push/julius_push.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_sync/julius_sync: julius_sync/julius_sync.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_net/julius_net: julius_net/julius_net.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

julius_sandbox/julius_sandbox: julius_sandbox/julius_sandbox.c
	$(CC) $(CFLAGS) -o $@ $< -lseccomp $(LDFLAGS)

julius_permissions/julius_permissions: julius_permissions/julius_permissions.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

install:
	install -m 755 julius_enclave/julius_enclave  /usr/bin/
	install -m 755 julius_pm/julius_pm            /usr/bin/
	install -m 755 julius_mm/julius_mm            /usr/bin/
	install -m 755 julius_ipc/julius_ipc          /usr/bin/
	install -m 755 julius_keychain/julius_keychain /usr/bin/
	install -m 755 julius_audit/julius_audit      /usr/bin/
	install -m 755 julius_health/julius_health    /usr/bin/
	install -m 755 julius_push/julius_push        /usr/bin/
	install -m 755 julius_sync/julius_sync        /usr/bin/
	install -m 755 julius_net/julius_net          /usr/bin/
	install -m 755 julius_sandbox/julius_sandbox  /usr/bin/
	install -m 755 julius_permissions/julius_permissions /usr/bin/

clean:
	find . -name "*.o" -delete
	find . -type f -executable -not -name "*.c" -delete
