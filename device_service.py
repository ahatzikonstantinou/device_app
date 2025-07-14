import os
import json

DEVICE_FILE = 'devices.json'

class DeviceProvider:
    def __init__(self, devices):
        self.devices = devices

    def get_devices(self):
        return self.devices
    
    def update_devices(self, new_device_list):
        """Replace current device list and persist it."""
        self.devices = new_device_list

    def get_device_by_id(self, device_id):
        return next((d for d in self.devices if d['id'] == device_id), None)
    
    def get_device_by_topic(self, topic):
        """Find the device whose MQTT config includes the given topic."""
        for device in self.devices:
            mqtt = device.get('mqtt', {})
            if topic in mqtt.values():
                return device
        return None

    def get_status(self, device):
        if not device:
            return None
        pins = device.get('pins', {})
        return {
            key: pins[key]['value']
            for key in ['active', 'enabled', 'open', 'overriden']
            if key in pins and 'value' in pins[key]
        }

    def get_publish_status_topic(self, device):
        if not device:
            return None
        return device.get('mqtt', {}).get('status')
