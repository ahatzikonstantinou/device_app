import RPi.GPIO as GPIO
import threading
import time
import json

GPIO.setmode(GPIO.BCM)

class GPIOSupervisor:
    def __init__(self, on_pin_change=None):
        self.devices = {}
        
        # Allow multiple observers, default to empty list if None
        self.on_pin_change = on_pin_change if on_pin_change is not None else []

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def add_pin_change_observer(self, callback):
        if callable(callback):
            self.on_pin_change.append(callback)

    def remove_pin_change_observer(self, callback):
        if callback in self.on_pin_change:
            self.on_pin_change.remove(callback)

    def load_devices(self, devices):
        for device in devices:
            self.add_device(device)

    def add_device(self, device):
        self.devices[device['id']] = device
        pins = device['pins']
        GPIO.setup(pins['powered']['pin'], GPIO.IN)
        GPIO.setup(pins['active']['pin'], GPIO.IN)
        GPIO.setup(pins['enabled']['pin'], GPIO.IN)
        GPIO.setup(pins['open']['pin'], GPIO.IN)
        GPIO.setup(pins['overriden']['pin'], GPIO.IN)
        GPIO.setup(pins['enable']['pin'], GPIO.OUT)
        self.set_output_value(device['id'], 'enable', pins['enable']['value'])
        GPIO.setup(pins['override']['pin'], GPIO.OUT)
        self.set_output_value(device['id'], 'override', pins['override']['value'])


    def update_device(self, device):
        # essentially updated the dictionary and reset the pins
        self.add_device(device)

    def remove_device(self, id):
        if id in self.devices:
            del self.devices[id]

    def read_input_pins(self, device):
        # pins που είναι input
        input_pins_keys = ['powered', 'active', 'enabled', 'open', 'overriden']
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
    
    def set_output_value(self, device_id, pin_key, value):
        """
        Set value (0 or 1) to the given GPIO output pin.
        If the pin is not configured as output, return error.
        """
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "error": "Device not found"}

        pin_info = device['pins'].get(pin_key)
        if not pin_info:
            return {"success": False, "error": f"Pin {pin_key} not found"}

        pin_num = pin_info['pin']

        try:
            direction = GPIO.gpio_function(pin_num)
            if direction != GPIO.OUT:
                raise RuntimeError(f"GPIO {pin_num} is not configured as OUTPUT (mode={direction})")

            GPIO.output(pin_num, value)
            # Update in-memory
            device['pins'][pin_key]['value'] = value

            # Notify all observers that pin changed
            for observer in self.on_pin_change:
                try:
                    observer(device_id, pin_key, value)
                except Exception as e:
                    print(f"Error in on_pin_change observer: {e}")

            return {"success": True, "pin": pin_num, "value_set": value}

        except Exception as e:
            return {"success": False, "pin": pin_num, "error": str(e)}
        
    def monitor_loop(self):
        input_pins_keys = ['powered', 'active', 'enabled', 'open', 'overriden']

        while True:
            for device_id, device in self.devices.items():
                pins = device.get('pins', {})

                for key in input_pins_keys:
                    pin_info = pins.get(key)
                    if not pin_info:
                        continue

                    pin_num = pin_info['pin']
                    try:
                        current_value = GPIO.input(pin_num)
                    except Exception as e:
                        print(f"Error reading GPIO pin {pin_num}: {e}")
                        continue

                    # Compare with last known value
                    last_value = pin_info.get('value')
                    if current_value != last_value:
                        # Update in-memory value
                        self.devices[device_id]['pins'][key]['value'] = current_value

                        # Notify observers
                        for observer in self.on_pin_change:
                            try:
                                observer(device_id, key, current_value)
                            except Exception as e:
                                print(f"Error in on_pin_change observer: {e}")

            time.sleep(1)
