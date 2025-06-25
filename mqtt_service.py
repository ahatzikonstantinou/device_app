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

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker.")
            self.connected = True
            # Εδώ μπορείς να κάνεις subscribe αν χρειάζεται
            self.client.subscribe("#")
        else:
            print(f"⚠️ Failed to connect to MQTT broker (code {rc})")

    def _on_disconnect(self, client, userdata, rc):
        print("⚠️ Disconnected from MQTT broker.")
        self.connected = False

    def connect(self):
        self.reconnect_thread.start()

    def _reconnect_loop(self):
        while True:
            if not self.connected:
                try:
                    print(f"🔁 Attempting to connect to MQTT broker at {self.config['ip']}:{self.config['port']}")
                    self.client.connect(self.config['ip'], self.config['port'], keepalive=60)
                    self.client.loop_start()
                except Exception as e:
                    print(f"❌ MQTT connection failed: {e}")
            time.sleep(5)

    def publish(self, topic, payload):
        if self.connected:
            try:
                self.client.publish(topic, payload)
            except Exception as e:
                print(f"❌ Failed to publish to MQTT: {e}")
        else:
            print("⚠️ MQTT not connected. Skipping publish.")

    def subscribe(self, topic):
        if self.connected:
            try:
                self.client.subscribe(topic)
            except Exception as e:
                print(f"❌ Failed to subscribe to topic {topic}: {e}")

    def update_config(self, new_config):
        self.config = new_config
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            #The service will reconnect by thread _reconnect_loop

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
mqtt_client = MQTTService(config)