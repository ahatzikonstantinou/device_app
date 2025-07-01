from flask import Flask, render_template, request, jsonify, abort
from flask_babel import Babel, _
from flask_cors import CORS
import uuid
import json
import os
from mqtt_service import mqtt_client
from gpio_service import GPIOSupervisor

app = Flask(__name__)
CORS(app)
babel = Babel()
app.config['BABEL_DEFAULT_LOCALE'] = 'el'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = './translations'

DEVICE_FILE = 'devices.json'
CONFIG_FILE = 'config.json'

supervisor = GPIOSupervisor()

# --- Helper functions ---
def is_name_unique(name, device_list ):
    return all(device['name'].lower() != name.lower() for device in device_list )

def are_pins_unique(pins, device_list ):
    used = set()
    for device in device_list :
        used.update(device['pins'].values())
    return all(pin not in used for pin in pins.values())

def load_devices():
    if not os.path.exists(DEVICE_FILE):
        return []
    with open(DEVICE_FILE) as f:
        return json.load(f)

def save_devices(devices):
    with open(DEVICE_FILE, 'w') as f:
        json.dump(devices, f, indent=2)

def get_locale():
    return request.args.get('lang') or 'el'

babel.init_app(app, locale_selector=get_locale)

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
        pins = data['pins']
        mqtt = data['mqtt']

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
        supervisor.add_device(data)
        return jsonify({'status': 'created'}), 201
    return jsonify(device_list )

@app.route('/api/devices/<device_id>', methods=['PUT', 'DELETE'])
def update_device(device_id):
    device_list  = load_devices()
    device = next((d for d in device_list  if d['id'] == device_id), None)
    if not device:
        return jsonify({'error': 'Not found'}), 404

    if request.method == 'PUT':
        data = request.json
        device.update(data)
    elif request.method == 'DELETE':
        device_list .remove(device)
        supervisor.remove_device(device['id'])

    save_devices(device_list )
    return jsonify({'status': 'ok'})

@app.route('/test-design')
def test_design():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return render_template('test-design.html', config=config)


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
        config = request.json
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        mqtt_client.update_config(config)
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

if __name__ == '__main__':
    mqtt_client.connect()
    supervisor.load_devices(load_devices())
    app.run(host='0.0.0.0', port=5000)