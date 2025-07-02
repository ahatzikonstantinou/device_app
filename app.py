import eventlet #this must come first before anything else
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, abort
from flask_babel import Babel, _
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import uuid
import json
import os
from mqtt_service import MQTTService
from gpio_service import GPIOSupervisor
from device_service import DeviceProvider

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
CORS(app)
babel = Babel()
app.config['BABEL_DEFAULT_LOCALE'] = 'el'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = './translations'

DEVICE_FILE = 'devices.json'
CONFIG_FILE = 'config.json'

supervisor = GPIOSupervisor()

# Observer to emit pin change to frontend
def emit_pin_change(device_id, pin_key, new_value):
    device = device_provider.get_device_by_id(device_id)
    if not device:
        return
    socketio.emit("pin_update", {
        "device_id": device_id,
        "device_name": device["name"],
        "pin_key": pin_key,
        "new_value": new_value
    })

supervisor.add_pin_change_observer(emit_pin_change)
# --- Helper functions ---
def is_name_unique(name, device_list, exclude_id=None):
    return all(device['name'].lower() != name.lower() or (exclude_id is not None and device['id'] == exclude_id) for device in device_list)

def are_pins_unique(pins, device_list, exclude_id=None):
    used = set()
    for device in device_list:
        if exclude_id is not None and device['id'] == exclude_id:
            continue
        for pin_info in device['pins'].values():
            used.add(pin_info['pin'])
    for pin_info in pins.values():
        if pin_info['pin'] in used:
            return False
    return True

def normalize_pins(pins_in):
    # Μετατροπή pins ώστε όλα να είναι dict με 'pin' και 'value'
    pins = {}
    for key, val in pins_in.items():
        if isinstance(val, dict):
            pin_num = val.get('pin')
            value_num = val.get('value', 0)
        else:
            pin_num = val
            value_num = 0
        if not isinstance(pin_num, int) or not isinstance(value_num, int):
            abort(400, f"Invalid pin or value for {key}")
        pins[key] = {
            "pin": pin_num,
            "value": value_num
        }
    return pins

def load_devices():
    if not os.path.exists(DEVICE_FILE):
        return []
    with open(DEVICE_FILE) as f:
        return json.load(f)

device_provider = DeviceProvider(load_devices())

def save_devices(devices):
    device_provider.update_devices(devices)
    mqtt_client.update_subscriptions()
    with open(DEVICE_FILE, 'w') as f:
        json.dump(devices, f, indent=2)

def get_locale():
    return request.args.get('lang') or 'el'

babel.init_app(app, locale_selector=get_locale)

def execute_command_on_device(mqtt_topic, command, value):
    device = device_provider.get_device_by_topic(mqtt_topic)
    if not device:
        raise ValueError(f"MQTT observer: No device found for mqtt topic '{mqtt_topic}'.")
    # command is "enable" or "override" so it is the pin_key
    supervisor.set_output_value(device['id'], command, value)
    
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
mqtt_client = MQTTService(config, device_provider, execute_command_on_device)

#Update device data and save file
def on_pin_change_update_device(device_id, pin_key, new_value):
    device_list  = load_devices()
    device = next((d for d in device_list  if d['id'] == device_id), None)
    if not device:
        print(f"Device {device_id} not found!")
        return
    if pin_key in device['pins']:
        device['pins'][pin_key]['value'] = new_value

        save_devices(device_list)
        print(f"Updated device {device_id} pin {pin_key} to {new_value} and saved devices.json")
        
        mqtt_client.publish(device['mqtt']['status'], json.dumps(device['pins'], indent=2))
        print(f"Published status update {device['mqtt']['status']}: {json.dumps(device['pins'], indent=2)}")
    else:
        print(f"Pin key {pin_key} not found in device {device_id}")

supervisor.add_pin_change_observer(on_pin_change_update_device)

@app.route('/')
def index():
    return render_template('index.html', devices=load_devices())

@app.route('/api/devices', methods=['GET', 'POST'])
def devices():
    device_list  = load_devices()
    if request.method == 'POST':
        data = request.json
        print(json.dumps(data, indent=4))
        if not data or 'name' not in data or 'pins' not in data or 'mqtt' not in data:
            abort(400, "Invalid input")

        name = data['name']
        pins_in  = data['pins']
        mqtt = data['mqtt']

        pins = normalize_pins(pins_in)

        if not is_name_unique(name, device_list ):
            abort(400, "Device name must be unique.")

        if not are_pins_unique(pins, device_list ):
            abort(400, "Pins must be unique across all devices.")

        new_device = {
            "id": str(uuid.uuid4()),
            "name": name,
            "pins": pins,
            "mqtt": mqtt
        }
        device_list .append(new_device)
        save_devices(device_list )
        supervisor.add_device(new_device)

        return jsonify({'status': 'created'}), 201

    # GET: Για κάθε device, διάβασε τα input pins και αντικατέστησε το device
    updated_devices = []
    for device in device_list:
        updated_device = supervisor.read_input_pins(device)
        updated_devices.append(updated_device)
    return jsonify(device_list), 200

@app.route('/api/devices/<device_id>', methods=['PUT', 'DELETE'])
def update_device(device_id):
    device_list  = load_devices()
    device = next((d for d in device_list  if d['id'] == device_id), None)
    if not device:
        return jsonify({'error': 'Not found'}), 404

    if request.method == 'PUT':
        print(json.dumps(request.json, indent=4)) #only PUT has request body
        data = request.json
        name = data['name']
        pins_in  = data['pins']
        mqtt = data['mqtt']

        pins = normalize_pins(pins_in)

        if not is_name_unique(name, device_list, device_id ):
            abort(400, "Device name must be unique.")

        if not are_pins_unique(pins, device_list, device_id ):
            abort(400, "Pins must be unique across all devices.")

        new_device = {
            "id": str(uuid.uuid4()),
            "name": name,
            "pins": pins,
            "mqtt": mqtt
        }

        # replace old device with new deive in list
        for i, d in enumerate(device_list):
            if d['id'] == device_id:
                device_list[i] = new_device
                break

        supervisor.update_device(new_device)
    elif request.method == 'DELETE':
        device_list .remove(device)
        supervisor.remove_device(device['id'])

    save_devices(device_list)
    return jsonify({'status': 'ok'})

@app.route('/api/devices/status/<device_id>')
def get_device_status(device_id):
    device = supervisor.devices.get(device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    # This will re-read input pins and return the device dict
    updated_device = supervisor.read_input_pins(device)
    pins_status = updated_device['pins']

    # Only return the input pins' values
    return jsonify({
        'active': pins_status['active']['value'],
        'enabled': pins_status['enabled']['value'],
        'open': pins_status['open']['value']
    })

@app.route('/settings')
def settings():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return render_template('settings.html', config=config)

@app.route('/api/mqtt', methods=['GET', 'POST'])
def api_mqtt():
    if request.method == 'GET':
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify(config)
    else:
        new_config = request.json
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            old_config = json.load(f)

        # Save new config file
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2)

        # Check if MQTT connection params changed (ip, port, username, password)
        relevant_keys = ['ip', 'port', 'username', 'password']
        config_changed = any(old_config.get(k) != new_config.get(k) for k in relevant_keys)

        if config_changed:
            mqtt_client.update_config(new_config)
            mqtt_client.update_subscriptions(all=True)

        return jsonify({'status': 'updated'})

@app.route('/api/mqtt/status')
def mqtt_status():
    return jsonify({'connected': mqtt_client.connected})

@app.route('/api/mqtt/test', methods=['POST'])
def test_mqtt_connection():
    config = request.json
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client()
        if config.get('username'):
            client.username_pw_set(config['username'], config['password'])
        client.connect(config['ip'], config['port'], 60)
        client.disconnect()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/api/mqtt/publish', methods=['POST'])
def publish_mqtt():
    data = request.json
    topic = data.get('topic')
    payload = data.get('payload')
    if not topic or payload is None:
        return jsonify({'error': 'Missing topic or payload'}), 400

    mqtt_client.publish(topic, payload)
    return jsonify({'status': 'published'})

@app.route('/gpio/<int:pin>', methods=['PUT'])
def set_gpio_output(pin):
    data = request.get_json()

    if not data or 'value' not in data:
        return jsonify({'success': False, 'error': 'Missing "value" in JSON body'}), 400

    value = data['value']
    if value not in [0, 1]:
        return jsonify({'success': False, 'error': '"value" must be 0 or 1'}), 400

    device_list  = load_devices()
    device_id = None
    pin_key = None
    for device in device_list:
        for key, pin_info in device.get('pins', {}).items():
            if pin_info.get('pin') == pin:
                device_id = device['id']
                pin_key = key
                break
        if device_id is not None and pin_key is not None:
            break

    if device_id is None or pin_key is None:
        return jsonify({'success': False, 'error': f'Pin {pin} not found in any device'}), 404

    result = supervisor.set_output_value(device_id, pin_key, value)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

if __name__ == '__main__':
    mqtt_client.connect()
    supervisor.load_devices(load_devices())
    #app.run(host='0.0.0.0', port=5000) #socketio.run covers this too
    socketio.run(app, host="0.0.0.0", port=5000)