import paho.mqtt.client as mqtt
import threading
import time
import json

class MQTTService:
    def __init__(self, config, on_message=None):
        self.config = config
        self.client = mqtt.Client()
        self.connected = False
        self.on_message_callback = on_message
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)

        if self.on_message_callback:
            self.client.on_message = self.on_message_callback
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Κρατάμε set με τρέχοντα subscriptions
        self.current_subscriptions = set()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            self.connected = True
            # Κάνουμε subscribe σε όσα ήδη έχουμε στη λίστα
            for topic in self.current_subscriptions:
                self.client.subscribe(topic)
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

    def update_subscriptions(self, device_list):
        # Νέα topics από τις συσκευές
        new_topics = set()
        for device in device_list:
            mqtt = device.get('mqtt', {})
            for key in ['enable', 'override', 'report_status']:
                topic = mqtt.get(key)
                if topic:
                    new_topics.add(topic)

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


with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
mqtt_client = MQTTService(config)