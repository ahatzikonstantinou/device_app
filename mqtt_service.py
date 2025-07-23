import paho.mqtt.client as mqtt
import threading
import time
import json


# Note: 
#  - device_provider must provide get_status(device_name) and get_publish_status_topic(device_name)
#  - on_message must be like on_message(mqtt_topic, command, value)
class MQTTService:
    def __init__(self, config, device_provider, on_message = None):
        self.config = config
        self.client = mqtt.Client()
        self.connected = False
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.device_provider = device_provider
        self.on_message = on_message
        self.client.on_message = self._on_message_wrapper
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Κρατάμε set με τρέχοντα subscriptions
        self.current_subscriptions = set()

    def _on_message_wrapper(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"Received MQTT message on '{topic}': '{payload}'")

        device = self.device_provider.get_device_by_topic(topic)
        if not device:
            print(f"MQTT service: No device found for mqtt topic '{topic}' — ignoring.")
            return
        
        print(f"Device:\n{json.dumps(device, indent=2)}")
        if topic == self.device_provider.get_subscribe_report_status_topic(device):
            # Respond by publishing current status
            self.publish_status(device)
        else:
            # Notify all observers that message
            if callable(self.on_message):
                try:
                    value = int(payload)
                    self.on_message(topic, value)
                except ValueError:
                    print(f"Ignoring invalid payload for {topic}: {payload}")

    def publish_status(self, device):
        status = json.dumps(self.device_provider.get_status(device), indent=2)
        publish_status_topic = self.device_provider.get_publish_status_topic(device)

        try:
            print(f"Publishing status {status}")
            self.publish(publish_status_topic, status)
        except Exception as e:
            print(f"Error handling report_status for {publish_status_topic}: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            self.connected = True
            # Fetch all current topics and subscribe
            self.update_subscriptions(all=True)
        else:
            print(f"Failed to connect to MQTT broker (code {rc})")

    def _on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker.")
        self.connected = False

    def connect(self):
        self.reconnect_thread.start()

    def _reconnect_loop(self):
        while True:
            if not self.connected:
                try:
                    print(f"Attempting to connect to MQTT broker at {self.config['ip']}:{self.config['port']}")
                    self.client.connect(self.config['ip'], self.config['port'], keepalive=60)
                    self.client.loop_start()
                except Exception as e:
                    print(f"MQTT connection failed: {e}")
            time.sleep(5)

    def publish(self, topic, payload):
        if self.connected:
            try:
                self.client.publish(topic, payload)
            except Exception as e:
                print(f"Failed to publish to MQTT: {e}")
        else:
            print("MQTT not connected. Skipping publish.")

    def subscribe(self, topic):
        if self.connected:
            try:
                self.client.subscribe(topic)
            except Exception as e:
                print(f"Failed to subscribe to topic {topic}: {e}")

    def unsubscribe(self, topic):
        if self.connected:
            try:
                self.client.unsubscribe(topic)
            except Exception as e:
                print(f"Failed to unsubscribe from topic {topic}: {e}")

    def update_config(self, new_config):
        self.config = new_config
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            # The service will reconnect by thread _reconnect_loop

    def update_subscriptions(self, all = False):
        # Νέα topics από τις συσκευές
        new_topics = set()
        for device in self.device_provider.get_devices():
            # Add device-level mqtt topics
            mqtt_subscribe_topic = self.device_provider.get_subscribe_report_status_topic(device)
            if mqtt_subscribe_topic:
                new_topics.add(mqtt_subscribe_topic)
            
            # Add mqtt topics from pins
            pins = device.get('pins', {})
            for pin_data in pins.values():
                topic = pin_data.get('mqtt')
                if topic:
                    new_topics.add(topic)

        if all:
            topics_to_subscribe = new_topics
            topics_to_unsubscribe = new_topics
        else:
            # Υπολογίζουμε ποια topics πρέπει να αφαιρεθούν
            topics_to_unsubscribe = self.current_subscriptions - new_topics
            # Και ποια πρέπει να προστεθούν
            topics_to_subscribe = new_topics - self.current_subscriptions

        # Αφαιρούμε τα παλιά που δεν χρειάζονται πια
        for topic in topics_to_unsubscribe:
            print(f"Unsubscribing from {topic}")
            self.unsubscribe(topic)

        # Προσθέτουμε τα νέα
        for topic in topics_to_subscribe:
            print(f"Subscribing to {topic}")
            self.subscribe(topic)

        # Ενημερώνουμε το set των τρεχόντων subscriptions
        self.current_subscriptions = new_topics