import RPi.GPIO as GPIO
import threading
import time
import json
from mqtt_service import mqtt_client

GPIO.setmode(GPIO.BCM)

class GPIOSupervisor:
    def __init__(self):
        self.devices = {}
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def load_devices(self, devices):
        for device in devices:
            self.add_device(device)

    def add_device(self, device):
        self.devices[device['name']] = device
        pins = device['pins']
        GPIO.setup(pins['active'], GPIO.IN)
        GPIO.setup(pins['enabled'], GPIO.IN)
        GPIO.setup(pins['open'], GPIO.IN)
        GPIO.setup(pins['enable'], GPIO.OUT)
        GPIO.setup(pins['override'], GPIO.OUT)

    def remove_device(self, name):
        if name in self.devices:
            del self.devices[name]

    def monitor_loop(self):
        while True:
            #for name, device in self.devices.items():
                #status = GPIO.input(device['pins']['status'])
                #mqtt_client.publish(f"devices/{name}/status", json.dumps({"status": status}))
            time.sleep(1)