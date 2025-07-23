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
            # Check top-level MQTT topics
            mqtt = device.get('mqtt', {})
            if topic in mqtt.values():
                return device
            
            # Check pin-level MQTT topics
            pins = device.get('pins', {})
            for pin_data in pins.values():
                if pin_data.get('mqtt') == topic:
                    return device
                
        return None
    
    def get_pinName_by_topic(self, device_id, topic):
        device = self.get_device_by_id(device_id)
        if not device:
            return None
        
        pins = device.get('pins', {})
        for name, pin in pins.items():
            if pin['mqtt'] == topic:
                return name
                
        return None

    def get_status(self, device):
        if not device:
            return None

        status = {}

        pins = device.get('pins', {})
        for name, pin in pins.items():
            status[name] = {
                'pin': pin['pin'],
                'value': pin['value']
            }

        return status


    def get_publish_status_topic(self, device):
        if not device:
            return None
        return device.get('mqtt', {}).get('pub_status')
    
    def get_subscribe_report_status_topic(self, device):
        if not device:
            return None
        return device.get('mqtt', {}).get('sub_report_status')
