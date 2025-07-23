import RPi.GPIO as GPIO
import threading
import time

GPIO.setmode(GPIO.BCM)

# Define input pin keys globally so they are consistent and easy to update
INPUT_PIN_KEYS = ['powered', 'active', 'enabled', 'closed', 'overriden']
OUTPUT_PIN_KEYS = ['enable', 'override']

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
        pins = device.get('pins', {})

        for key, pin_data in pins.items():
            if pin_data.get('type') == 'in':
                GPIO.setup(pin_data['pin'], GPIO.IN)
            elif pin_data.get('type') == 'out':
                GPIO.setup(pin_data['pin'], GPIO.OUT)
                self.set_output_value(device['id'], key, pin_data.get('value', 0))

    def update_device(self, device):
        # essentially updated the dictionary and reset the pins
        self.add_device(device)

    def remove_device(self, id):
        if id in self.devices:
            del self.devices[id]

    def read_input_pins(self, device):
        pins = device.get('pins', {})
        new_pins = {}

        for key, pin_data in pins.items():
            if pin_data.get('type') == 'in':
                pin_num = pin_data['pin']
                gpio_val = GPIO.input(pin_num)
                new_pins[key] = {'pin': pin_num, 'value': gpio_val, 'type': 'in'}
            else:
                # Keep output pins as they are
                new_pins[key] = pin_data

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

        pin_info = device.get('pins', {}).get(pin_key)
        pin_info = pin_info if pin_info and pin_info.get('type') == 'out' else None

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
        while True:
            for device_id, device in self.devices.items():
                pins = device.get('pins', {})

                for key, pin_info in pins.items():
                    if pin_info.get('type') == 'in':
                        pin_num = pin_info['pin']
                        try:
                            current_value = GPIO.input(pin_num)
                        except Exception as e:
                            print(f"Error reading GPIO pin {pin_num}: {e}")
                            continue

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

