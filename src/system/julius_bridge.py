import socket
import struct
import json
import os
import threading
import time

IPC_SOCKET   = "/var/run/julius_ipc.sock"
PUSH_SOCKET  = "/var/run/julius_push.sock"
PERMS_SOCKET = "/var/run/julius_perms.sock"
KC_SOCKET    = "/var/run/julius_keychain.sock"
WIFI_STATE   = "/var/run/julius_wifi.state"
BT_STATE     = "/var/run/julius_bt.state"
POWER_STATE  = "/var/run/julius_power.state"
HEALTH_STATE = "/var/run/julius_health.state"
NET_STATE    = "/var/run/julius_net.state"

class JuliusBridge:
    def __init__(self):
        self._ipc_sock    = None
        self._callbacks   = {}
        self._running     = True
        self._lock        = threading.Lock()
        self._connect_ipc()
        self._start_listener()

    def _connect_ipc(self):
        try:
            s = socket.socket(socket.AF_UNIX,
                              socket.SOCK_STREAM)
            s.connect(IPC_SOCKET)
            self._ipc_sock = s
            print("[Bridge] Connected to IPC")
        except Exception as e:
            print(f"[Bridge] IPC not available: {e}")
            self._ipc_sock = None

    def _start_listener(self):
        def listen():
            while self._running:
                if not self._ipc_sock:
                    time.sleep(2)
                    self._connect_ipc()
                    continue
                try:
                    data = self._ipc_sock.recv(8256)
                    if not data:
                        break
                    self._handle_message(data)
                except Exception:
                    self._ipc_sock = None
                    time.sleep(1)
        t = threading.Thread(target=listen, daemon=True)
        t.start()

    def _handle_message(self, data):
        try:
            topic = data[:64].rstrip(b'\x00').decode()
            payload = data[64:64+8192].rstrip(b'\x00')
            if topic in self._callbacks:
                for cb in self._callbacks[topic]:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        print(f"[Bridge] Callback error: {e}")
        except Exception as e:
            print(f"[Bridge] Message error: {e}")

    def subscribe(self, topic, callback):
        with self._lock:
            if topic not in self._callbacks:
                self._callbacks[topic] = []
            self._callbacks[topic].append(callback)
        self._send_ipc("__subscribe__", topic.encode())

    def publish(self, topic, data):
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        self._send_ipc(topic, data)

    def _send_ipc(self, topic, data):
        if not self._ipc_sock:
            return
        try:
            msg = topic.encode().ljust(64, b'\x00')
            msg += (data if data else b'').ljust(8192, b'\x00')
            msg += struct.pack('I', len(data) if data else 0)
            msg += struct.pack('I', os.getpid())
            msg += struct.pack('Q', int(time.time()))
            msg += struct.pack('I', 0)
            self._ipc_sock.sendall(msg[:8272])
        except Exception as e:
            print(f"[Bridge] Send error: {e}")
            self._ipc_sock = None

    def read_state(self, path):
        state = {}
        try:
            if not os.path.exists(path):
                return state
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        k, v = line.split('=', 1)
                        state[k.strip()] = v.strip()
        except Exception:
            pass
        return state

    # WiFi
    def get_wifi_state(self):
        return self.read_state(WIFI_STATE)

    def wifi_connect(self, ssid, password):
        self.publish("WIFI_CONNECT",
            {"ssid":ssid,"password":password})

    def wifi_disconnect(self):
        self.publish("WIFI_DISCONNECT", {})

    def wifi_scan(self):
        self.publish("WIFI_SCAN", {})

    # Bluetooth
    def get_bt_state(self):
        return self.read_state(BT_STATE)

    def bt_scan(self):
        self.publish("BT_SCAN", {})

    def bt_connect(self, addr):
        self.publish("BT_CONNECT", {"addr":addr})

    # Power
    def get_power_state(self):
        return self.read_state(POWER_STATE)

    def get_battery_level(self):
        state = self.get_power_state()
        try:
            return int(state.get("level", 85))
        except:
            return 85

    def get_charging(self):
        state = self.get_power_state()
        return state.get("charging","0") == "1"

    # Health
    def get_health_state(self):
        return self.read_state(HEALTH_STATE)

    def get_health_score(self):
        state = self.get_health_state()
        try:
            return int(state.get("score", 100))
        except:
            return 100

    # Network
    def get_net_state(self):
        return self.read_state(NET_STATE)

    # Push notifications
    def send_notification(self, app, title,
                          body, priority=1):
        try:
            s = socket.socket(socket.AF_UNIX,
                              socket.SOCK_STREAM)
            s.connect(PUSH_SOCKET)
            op      = struct.pack('I', 1)
            app_b   = app.encode().ljust(64, b'\x00')
            title_b = title.encode().ljust(128, b'\x00')
            body_b  = body.encode().ljust(256, b'\x00')
            action_b= b'\x00' * 64
            badge   = struct.pack('I', 0)
            sound   = struct.pack('I', 1)
            prio    = struct.pack('I', priority)
            notif_id= struct.pack('I', 0)
            msg = (op + app_b + title_b + body_b +
                   action_b + badge + sound + prio + notif_id)
            s.sendall(msg)
            resp = s.recv(4)
            s.close()
            return struct.unpack('I', resp)[0]
        except Exception as e:
            print(f"[Bridge] Push error: {e}")
            return -1

    # Permissions
    def check_permission(self, app, perm_type):
        try:
            s = socket.socket(socket.AF_UNIX,
                              socket.SOCK_STREAM)
            s.connect(PERMS_SOCKET)
            op    = struct.pack('I', 1)
            app_b = app.encode().ljust(64, b'\x00')
            ptype = struct.pack('I', perm_type)
            s.sendall(op + app_b + ptype)
            resp  = s.recv(8)
            s.close()
            if len(resp) >= 8:
                status, granted = struct.unpack('II', resp)
                return granted == 1
        except Exception:
            pass
        return False

    # Keychain
    def keychain_save(self, service, account, data):
        try:
            s = socket.socket(socket.AF_UNIX,
                              socket.SOCK_STREAM)
            s.connect(KC_SOCKET)
            op      = struct.pack('I', 1)
            svc_b   = service.encode().ljust(64, b'\x00')
            acc_b   = account.encode().ljust(64, b'\x00')
            data_b  = (data.encode()
                       if isinstance(data,str)
                       else data)
            data_p  = data_b.ljust(512, b'\x00')
            dlen    = struct.pack('I', len(data_b))
            label_b = b'\x00' * 128
            s.sendall(op+svc_b+acc_b+data_p+dlen+label_b)
            resp = s.recv(648)
            s.close()
            return struct.unpack('i', resp[:4])[0] == 0
        except Exception as e:
            print(f"[Bridge] Keychain save error: {e}")
            return False

    def keychain_get(self, service, account):
        try:
            s = socket.socket(socket.AF_UNIX,
                              socket.SOCK_STREAM)
            s.connect(KC_SOCKET)
            op     = struct.pack('I', 2)
            svc_b  = service.encode().ljust(64, b'\x00')
            acc_b  = account.encode().ljust(64, b'\x00')
            pad    = b'\x00' * (512+4+128)
            s.sendall(op+svc_b+acc_b+pad)
            resp   = s.recv(648)
            s.close()
            if len(resp) >= 8:
                status = struct.unpack('i', resp[:4])[0]
                dlen   = struct.unpack('I', resp[4:8])[0]
                if status == 0 and dlen > 0:
                    return resp[8:8+dlen].decode(
                        errors='ignore')
        except Exception as e:
            print(f"[Bridge] Keychain get error: {e}")
        return None

    def stop(self):
        self._running = False
        if self._ipc_sock:
            self._ipc_sock.close()

# Global bridge instance
_bridge = None

def get_bridge():
    global _bridge
    if _bridge is None:
        _bridge = JuliusBridge()
    return _bridge
