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
        self.devices[device['id']] = device
        pins = device['pins']
        GPIO.setup(pins['active']['pin'], GPIO.IN)
        GPIO.setup(pins['enabled']['pin'], GPIO.IN)
        GPIO.setup(pins['open']['pin'], GPIO.IN)
        GPIO.setup(pins['enable']['pin'], GPIO.OUT)
        self.set_output_value(pins['enable']['pin'], pins['enable']['value'])
        GPIO.setup(pins['override']['pin'], GPIO.OUT)
        self.set_output_value(pins['override']['pin'], pins['override']['value'])


    def update_device(self, device):
        # essentially updated the dictionary and reset the pins
        self.add_device(device)

    def remove_device(self, id):
        if id in self.devices:
            del self.devices[id]

    def read_input_pins(self, device):
        # pins που είναι input
        input_pins_keys = ['active', 'enabled', 'open']
        pins = device['pins']
        new_pins = {}

        for key in pins:
            pin_num = pins[key]['pin']
            if key in input_pins_keys:
                gpio_val = GPIO.input(pin_num)
                new_pins[key] = {'pin': pin_num, 'value': gpio_val}
            else:
                # Για output pins μπορείς να κρατήσεις απλά τον αριθμό ή και να αφαιρέσεις
                # Εδώ απλά κρατάμε την αρχική τιμή (προαιρετικό)
                new_pins[key] = pins[key]

        # Αντικαθιστούμε το pins dictionary με το νέο
        device['pins'] = new_pins
        return device
    
    def set_output_value(self, pin, value):
        """
        Set value (0 or 1) to the given GPIO output pin.
        If the pin is not configured as output, return error.
        """
        try:
            direction = GPIO.gpio_function(pin)
            if direction != GPIO.OUT:
                raise RuntimeError(f"GPIO {pin} is not configured as OUTPUT (mode={direction})")

            GPIO.output(pin, value)
            return {"success": True, "pin": pin, "value_set": value}

        except Exception as e:
            return {"success": False, "pin": pin, "error": str(e)}
        
    def monitor_loop(self):
        while True:
            #for id, device in self.devices.items():
                #status = GPIO.input(device['pins']['status'])
                #mqtt_client.publish(f"devices/{name}/status", json.dumps({"status": status}))
            time.sleep(1)