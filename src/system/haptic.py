import threading
import time
import os

class HapticFeedback:
    def __init__(self):
        self.enabled   = True
        self.intensity = 100
        self.gpio_path = "/sys/class/gpio"
        self.motor_pin = 18
        self._setup()

    def _setup(self):
        try:
            # Export GPIO pin for vibration motor
            with open(f"{self.gpio_path}/export", "w") as f:
                f.write(str(self.motor_pin))
            with open(f"{self.gpio_path}/gpio{self.motor_pin}/direction","w") as f:
                f.write("out")
        except:
            pass

    def _vibrate_gpio(self, duration):
        try:
            gpio_val = f"{self.gpio_path}/gpio{self.motor_pin}/value"
            with open(gpio_val, "w") as f:
                f.write("1")
            time.sleep(duration)
            with open(gpio_val, "w") as f:
                f.write("0")
        except:
            pass

    def _vibrate_thread(self, pattern):
        for duration, pause in pattern:
            adjusted = duration * (self.intensity/100)
            self._vibrate_gpio(adjusted)
            if pause > 0:
                time.sleep(pause)

    def vibrate(self, pattern=None):
        if not self.enabled:
            return
        if pattern is None:
            pattern = [(0.05, 0)]
        t = threading.Thread(
            target=self._vibrate_thread,
            args=(pattern,),
            daemon=True
        )
        t.start()

    # Haptic patterns
    def tap(self):
        self.vibrate([(0.03, 0)])

    def double_tap(self):
        self.vibrate([(0.03, 0.05), (0.03, 0)])

    def heavy(self):
        self.vibrate([(0.1, 0)])

    def success(self):
        self.vibrate([(0.05, 0.05), (0.05, 0.05), (0.1, 0)])

    def error(self):
        self.vibrate([(0.1, 0.05), (0.1, 0.05), (0.1, 0)])

    def unlock(self):
        self.vibrate([(0.05, 0.03), (0.05, 0.03), (0.15, 0)])

    def notification(self):
        self.vibrate([(0.05, 0.1), (0.05, 0)])

    def swipe(self):
        self.vibrate([(0.02, 0)])

    def long_press(self):
        self.vibrate([(0.08, 0)])
