# import RPi.GPIO as GPIO
import gpiod
import threading
import time
from gpiod.line import Direction, Value
import signal
import sys

from gpio_client import GPIOClient
from gpio_types import Direction

# GPIO.setmode(GPIO.BCM)
CHIP = "/dev/gpiochip0"

import atexit

# Define input pin keys globally so they are consistent and easy to update
# INPUT_PIN_KEYS = ['powered', 'active', 'enabled', 'closed', 'overriden']
# OUTPUT_PIN_KEYS = ['enable', 'override']

class GPIOSupervisor:
    def __init__(self, on_pin_change=None, client_id="device_app"):
        self.devices = {}
        self.client = GPIOClient(client_id)
        
        # signal.signal(signal.SIGINT, self.cleanup)
        atexit.register(self.cleanup, None, None)   # instead of SIGINT due to eventlet and flask

        # Allow multiple observers, default to empty list if None
        self.on_pin_change = on_pin_change if on_pin_change is not None else []
        # self.line_requests = {}  # {pin: request object}
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def cleanup(self, signum, frame):
        print("Caught CTRL-C, releasing GPIO lines...")
        # for request in self.line_requests.values():
        #     request.release()
        def release_all():
            for device in self.devices.values():
                for pin_data in device.get('pins', {}).values():
                    pin_num = pin_data['pin']
                    try:
                        self.client.release_pin(pin_num)
                        print(f"Released pin {pin_num}")
                    except Exception as e:
                        print(f"Error releasing pin {pin_num}: {e}")

        cleanup_thread = threading.Thread(target=release_all)
        cleanup_thread.start()
        cleanup_thread.join(timeout=5)  # Wait for cleanup to finish before exiting
        # sys.exit(0)

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
            pin_num = pin_data['pin']
            # if pin_data.get('type') == 'in':
            #     settings = gpiod.LineSettings(direction=Direction.INPUT)
            # elif pin_data.get('type') == 'out':
            #     initial = Value.ACTIVE if pin_data.get('value', 0) else Value.INACTIVE
            #     settings = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=initial)
            # else:
            #     continue
            # request = gpiod.request_lines(CHIP, consumer="device_app", config={pin_num: settings})
            # self.line_requests[pin_num] = request           

            direction = Direction.IN if pin_data.get('type') == 'in' else Direction.OUT
            self.client.request_pin(pin_num, direction)

            # For output pins, set initial value
            if direction == Direction.OUT:
                value = pin_data.get('value', 0)
                self.client.write_pin(pin_num, value)



    def update_device(self, device):
        device_id = device['id']
        new_pins = device.get('pins', {})
        old_device = self.devices.get(device_id, {})
        old_pins = old_device.get('pins', {})

        # Track pins to release
        for key, old_pin_data in old_pins.items():
            old_pin_num = old_pin_data['pin']
            old_direction = old_pin_data['type']

            new_pin_data = new_pins.get(key)
            if not new_pin_data:
                # Pin removed
                self.client.release_pin(old_pin_num)
            else:
                new_direction = new_pin_data['type']
                if new_direction != old_direction:
                    # Direction changed
                    self.client.release_pin(old_pin_num)

        # Update device and request new pins
        self.add_device(device)


    def remove_device(self, id):
        if id in self.devices:
            for pin_data in self.devices[id].get('pins', {}).values():
                pin_num = pin_data['pin']
                # if pin_num in self.line_requests:
                #     self.line_requests[pin_num].release()
                #     del self.line_requests[pin_num]
                self.client.release_pin(pin_num)
            del self.devices[id]

    def read_input_pins(self, device):
        pins = device.get('pins', {})
        new_pins = {}

        for key, pin_data in pins.items():
            pin_num = pin_data['pin']
            if pin_data.get('type') == 'in':
                try:
                    # value = self.line_requests[pin_num].get_value(pin_num).value
                    resp = self.client.read_pin(pin_num)
                    value = resp.get("value") if resp.get("success") else None
                except Exception as e:
                    print(f"Error reading GPIO {pin_num}: {e}")
                    value = None
                new_pins[key] = {'pin': pin_num, 'value': value, 'type': 'in'}
            else:
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
        if not pin_info or pin_info.get('type') != 'out':
            return {"success": False, "error": f"Pin {pin_key} not found"}

        pin_num = pin_info['pin']

        try:
            # val = Value.ACTIVE if value else Value.INACTIVE
            # request = self.line_requests.get(pin_num)
            # if not request:
            #     raise RuntimeError(f"No request found for GPIO {pin_num}")
            
            # self.line_requests[pin_num].set_value(pin_num, val)
            resp = self.client.write_pin(pin_num, value)
            print(f"Writing {value} to pin {pin_num}")
            if not resp.get("success"):
                raise RuntimeError(resp.get("message", "Unknown error"))
            
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
                            # current_value = self.line_requests[pin_num].get_value(pin_num).value
                            resp = self.client.read_pin(pin_num)
                            current_value = resp.get("value") if resp.get("success") else None
                        except Exception as e:
                            print(f"Error reading GPIO pin {pin_num}: {e}")
                            continue

                        last_value = pin_info.get('value')
                        if current_value != last_value:
                            # Update in-memory value
                            print(f"Pin {pin_num} changed from {last_value} to {current_value}")
                            self.devices[device_id]['pins'][key]['value'] = current_value

                            # Notify observers
                            for observer in self.on_pin_change:
                                try:
                                    observer(device_id, key, current_value)
                                except Exception as e:
                                    print(f"Error in on_pin_change observer: {e}")

            time.sleep(1)

