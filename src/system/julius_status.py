import pygame
import time
import os
import sys
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

try:
    from system.julius_bridge import get_bridge
    BRIDGE_AVAILABLE = True
except:
    BRIDGE_AVAILABLE = False

BG     = (8,   8,  18)
WHITE  = (255, 255, 255)
GREEN  = (48,  209,  88)
RED    = (255,  69,  58)
BLUE   = (10,  132, 255)
ORANGE = (255, 159,  10)
DIM    = (100, 100, 110)
PURPLE = (191,  90, 242)

class JuliusStatus:
    def __init__(self):
        self.battery_level  = 85
        self.charging       = False
        self.wifi_connected = False
        self.wifi_ssid      = ""
        self.wifi_signal    = 0
        self.bt_connected   = False
        self.bt_enabled     = True
        self.health_score   = 100
        self.cpu_usage      = 0
        self.mem_available  = 0
        self.net_rx         = 0
        self.net_tx         = 0
        self.last_update    = 0
        self.bridge         = None

        if BRIDGE_AVAILABLE:
            try:
                self.bridge = get_bridge()
                self._subscribe_events()
            except Exception as e:
                print(f"[Status] Bridge error: {e}")

    def _subscribe_events(self):
        if not self.bridge:
            return
        self.bridge.subscribe(
            "BATTERY", self._on_battery)
        self.bridge.subscribe(
            "WIFI_STATE", self._on_wifi)
        self.bridge.subscribe(
            "BT_STATE", self._on_bt)

    def _on_battery(self, topic, data):
        try:
            import struct
            self.battery_level = struct.unpack(
                'I', data[:4])[0]
        except:
            pass

    def _on_wifi(self, topic, data):
        try:
            import json
            info = json.loads(data.decode())
            self.wifi_connected = info.get(
                "connected", False)
            self.wifi_ssid   = info.get("ssid", "")
            self.wifi_signal = info.get("signal", 0)
        except:
            pass

    def _on_bt(self, topic, data):
        try:
            import json
            info = json.loads(data.decode())
            self.bt_connected = info.get(
                "connected", False)
        except:
            pass

    def update(self):
        now = time.time()
        if now - self.last_update < 5:
            return
        self.last_update = now

        if self.bridge:
            # Get from bridge
            self.battery_level = self.bridge.get_battery_level()
            self.charging       = self.bridge.get_charging()
            wifi = self.bridge.get_wifi_state()
            self.wifi_connected = wifi.get("connected","0")=="1"
            self.wifi_ssid      = wifi.get("ssid","")
            bt = self.bridge.get_bt_state()
            self.bt_enabled = bt.get("enabled","0")=="1"
            self.health_score = self.bridge.get_health_score()
        else:
            # Fallback — read files directly
            self._read_battery()
            self._read_wifi()
            self._read_cpu()

    def _read_battery(self):
        try:
            with open("/sys/class/power_supply/"
                      "battery/capacity") as f:
                self.battery_level = int(f.read().strip())
            with open("/sys/class/power_supply/"
                      "battery/status") as f:
                status = f.read().strip()
                self.charging = status in [
                    "Charging","Full"]
        except:
            pass

    def _read_wifi(self):
        try:
            state_file = "/var/run/julius_wifi.state"
            if os.path.exists(state_file):
                with open(state_file) as f:
                    for line in f:
                        if line.startswith("connected="):
                            self.wifi_connected = \
                                line.strip().split("=")[1]=="1"
                        elif line.startswith("ssid="):
                            self.wifi_ssid = \
                                line.strip().split("=")[1]
                        elif line.startswith("signal="):
                            try:
                                self.wifi_signal = int(
                                    line.strip().split("=")[1])
                            except:
                                pass
        except:
            pass

    def _read_cpu(self):
        try:
            with open("/proc/stat") as f:
                line = f.readline()
            fields = [int(x) for x in line.split()[1:]]
            idle  = fields[3]
            total = sum(fields)
            self.cpu_usage = max(0, min(100,
                100 - int(idle*100/total)))
        except:
            pass

    def get_wifi_bars(self):
        if not self.wifi_connected:
            return 0
        s = self.wifi_signal
        if s > -50: return 4
        if s > -60: return 3
        if s > -70: return 2
        if s > -80: return 1
        return 0

    def send_notification(self, app, title, body):
        if self.bridge:
            self.bridge.send_notification(app, title, body)

    def check_permission(self, app, perm_type):
        if self.bridge:
            return self.bridge.check_permission(
                app, perm_type)
        return True  # Allow all if no bridge

    def save_to_keychain(self, service, account, data):
        if self.bridge:
            return self.bridge.keychain_save(
                service, account, data)
        return False

    def get_from_keychain(self, service, account):
        if self.bridge:
            return self.bridge.keychain_get(
                service, account)
        return None

# Global status instance
_status = None

def get_status():
    global _status
    if _status is None:
        _status = JuliusStatus()
    return _status
