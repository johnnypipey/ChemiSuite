# pages/archemedes.py
# ARChemedes - Remote Monitoring System using MQTT
from nicegui import ui
import json
import os
from typing import Optional
import time
import threading

# Global state
archemedes_state = {
    'client': None,
    'connected': False,
    'broker_url': '',
    'broker_port': 1883,
    'username': '',
    'password': '',
    'topic_prefix': 'chemisuite',
    'publish_timer': None,
    'publish_thread': None,
    'stop_publishing_event': None,
    'status_label': None,
    'config_file': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archemedes_config.json')
}

def load_config():
    """Load ARChemedes configuration from file"""
    try:
        if os.path.exists(archemedes_state['config_file']):
            with open(archemedes_state['config_file'], 'r') as f:
                config = json.load(f)
                archemedes_state['broker_url'] = config.get('broker_url', '')
                archemedes_state['broker_port'] = config.get('broker_port', 1883)
                archemedes_state['username'] = config.get('username', '')
                archemedes_state['password'] = config.get('password', '')
                archemedes_state['topic_prefix'] = config.get('topic_prefix', 'chemisuite')
                return True
    except Exception as e:
        print(f"Error loading ARChemedes config: {e}")
    return False

def save_config():
    """Save ARChemedes configuration to file"""
    try:
        config = {
            'broker_url': archemedes_state['broker_url'],
            'broker_port': archemedes_state['broker_port'],
            'username': archemedes_state['username'],
            'password': archemedes_state['password'],
            'topic_prefix': archemedes_state['topic_prefix']
        }
        with open(archemedes_state['config_file'], 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving ARChemedes config: {e}")
        return False

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        archemedes_state['connected'] = True
        archemedes_state['connection_message'] = 'success'
        print("✅ Successfully connected to MQTT broker!")

        # Publish connection status message
        try:
            connection_msg = {
                'status': 'connected',
                'client': 'ChemiSuite',
                'timestamp': time.time()
            }
            client.publish(
                f"{archemedes_state['topic_prefix']}/system/status",
                json.dumps(connection_msg),
                retain=True
            )
        except:
            pass
    else:
        archemedes_state['connected'] = False
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code {rc}")
        archemedes_state['connection_message'] = f'failed:{error_msg}'
        print(f"❌ Connection failed: {error_msg}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    archemedes_state['connected'] = False
    if archemedes_state['status_label']:
        archemedes_state['status_label'].set_text("● Disconnected")
        archemedes_state['status_label'].style("color: #ff4757; font-size: 14px; font-weight: bold;")

def connect_to_broker():
    """Connect to MQTT broker"""
    if not archemedes_state['broker_url']:
        ui.notify("Please configure broker URL first", type='warning')
        return False

    try:
        # Import paho-mqtt (will need to be installed)
        import paho.mqtt.client as mqtt

        ui.notify(f"Connecting to {archemedes_state['broker_url']}...", type='info')

        # Create MQTT client
        client = mqtt.Client(client_id=f"chemisuite_{int(time.time())}")

        # Set credentials if provided
        if archemedes_state['username'] and archemedes_state['password']:
            client.username_pw_set(archemedes_state['username'], archemedes_state['password'])
            ui.notify("Credentials set", type='info')

        # Enable TLS for secure connection (required for HiveMQ)
        try:
            client.tls_set()
            ui.notify("TLS/SSL enabled", type='info')
        except Exception as e:
            ui.notify(f"TLS setup failed: {str(e)}", type='negative')
            return False

        # Set callbacks
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        # Connect to broker
        ui.notify("Attempting connection...", type='info')
        client.connect(archemedes_state['broker_url'], archemedes_state['broker_port'], 60)

        # Start network loop in background thread
        client.loop_start()

        archemedes_state['client'] = client
        ui.notify("Connection initiated, waiting for broker response...", type='info')
        return True

    except ImportError:
        ui.notify("paho-mqtt not installed. Run: pip install paho-mqtt", type='negative')
        return False
    except Exception as e:
        ui.notify(f"Connection error: {str(e)}", type='negative')
        return False

def disconnect_from_broker():
    """Disconnect from MQTT broker"""
    if archemedes_state['client']:
        try:
            archemedes_state['client'].loop_stop()
            archemedes_state['client'].disconnect()
        except:
            pass
        archemedes_state['client'] = None
        archemedes_state['connected'] = False
        ui.notify("Disconnected from MQTT broker", type='info')

def publish_data():
    """Publish ChemiSuite data to MQTT broker"""
    if not archemedes_state['connected'] or not archemedes_state['client']:
        print("⚠️ Skipping publish - not connected or no client")
        return

    print(f"\n📡 Publishing data at {time.strftime('%H:%M:%S')}...")

    try:
        # Import data sources
        from pages import fume_hood as fume_hood_page
        from pages import roboschlenk as roboschlenk_page
        from pages import devices as devices_page

        topic_prefix = archemedes_state['topic_prefix']

        # Publish fume hood sash status
        fume_hoods = fume_hood_page.fume_hoods
        for hood in fume_hoods:
            hood_id = hood.get('id', 'unknown')

            # Only publish sash status (relevant safety data)
            sash_data = {
                'name': hood.get('name', 'Unknown'),
                'sash_open': hood.get('sash_open', False),
                'location': hood.get('location', ''),
                'timestamp': time.time()
            }
            archemedes_state['client'].publish(
                f"{topic_prefix}/fumehood/{hood_id}/sash",
                json.dumps(sash_data),
                retain=True
            )

            # Publish device sensor data for devices assigned to this hood
            if hood.get('assigned_devices'):
                for assigned_device in hood.get('assigned_devices', []):
                    device_name = assigned_device.get('name', 'unknown')

                    # Find the actual device object in devices list to get current state
                    actual_device = None
                    for dev in devices_page.devices:
                        if dev.get('name') == device_name:
                            actual_device = dev
                            break

                    # Skip if device not found or not connected
                    if not actual_device or not actual_device.get('connection_state', {}).get('connected', False):
                        continue

                    device_type = actual_device.get('type', 'unknown')
                    device_data = {
                        'name': device_name,
                        'type': device_type,
                        'timestamp': time.time()
                    }

                    # Get real-time sensor data based on device type
                    try:
                        driver = actual_device.get('driver')
                        if driver:
                            # IKA Stirrer/Hotplate - temperature and stir speed
                            if device_type in ['IKA RCT Digital', 'ika_stirrer']:
                                try:
                                    temp = driver.get_temperature(sensor_type=2)
                                    device_data['temperature'] = round(temp, 1)
                                    device_data['temperature_unit'] = '°C'
                                except Exception as e:
                                    device_data['temperature'] = None
                                    print(f"    ✗ Error reading temp from {device_name}: {e}")

                                try:
                                    speed = driver.get_speed()
                                    device_data['stir_speed'] = round(speed, 0)
                                    device_data['stir_speed_unit'] = 'RPM'
                                except Exception as e:
                                    device_data['stir_speed'] = None
                                    print(f"    ✗ Error reading speed from {device_name}: {e}")
                            # Edwards TIC - pressure
                            elif device_type == 'Edwards TIC':
                                try:
                                    pressure = driver.get_pressure()
                                    device_data['pressure'] = pressure
                                    device_data['pressure_unit'] = 'mbar'
                                except Exception as e:
                                    device_data['pressure'] = None
                                    print(f"    ✗ Error reading pressure from {device_name}: {e}")
                    except Exception as e:
                        print(f"  ERROR reading device {device_name}: {e}")
                        import traceback
                        traceback.print_exc()

                    # Publish device data
                    archemedes_state['client'].publish(
                        f"{topic_prefix}/device/{hood_id}/{device_name}",
                        json.dumps(device_data),
                        retain=True
                    )

        # Publish standalone devices (not assigned to fume hoods)
        for device in devices_page.devices:
            if device.get('connection_state', {}).get('connected', False):
                device_name = device.get('name', 'unknown')
                device_type = device.get('type', 'unknown')

                device_data = {
                    'name': device_name,
                    'type': device_type,
                    'timestamp': time.time()
                }

                # Get real-time sensor data
                try:
                    driver = device.get('driver')
                    if driver:
                        # IKA Stirrer/Hotplate
                        if device_type in ['IKA RCT Digital', 'ika_stirrer']:
                            try:
                                temp = driver.get_temperature(sensor_type=2)
                                device_data['temperature'] = round(temp, 1)
                                device_data['temperature_unit'] = '°C'
                            except Exception as e:
                                device_data['temperature'] = None
                                print(f"    ✗ Error reading temp from {device_name}: {e}")

                            try:
                                speed = driver.get_speed()
                                device_data['stir_speed'] = round(speed, 0)
                                device_data['stir_speed_unit'] = 'RPM'
                            except Exception as e:
                                device_data['stir_speed'] = None
                                print(f"    ✗ Error reading speed from {device_name}: {e}")

                        # Edwards TIC
                        elif device_type == 'Edwards TIC':
                            try:
                                pressure = driver.get_pressure()
                                device_data['pressure'] = pressure
                                device_data['pressure_unit'] = 'mbar'
                            except Exception as e:
                                device_data['pressure'] = None
                                print(f"    ✗ Error reading pressure from {device_name}: {e}")
                except Exception as e:
                    print(f"  ERROR reading {device_name}: {e}")
                    import traceback
                    traceback.print_exc()

                # Publish standalone device data
                archemedes_state['client'].publish(
                    f"{topic_prefix}/device/standalone/{device_name}",
                    json.dumps(device_data),
                    retain=True
                )

        # Publish RoboSchlenk data (tap positions and angles)
        if roboschlenk_page.roboschlenk_state.get('connected'):
            controller = roboschlenk_page.roboschlenk_state.get('controller')
            if controller:
                for motor_name in ['A', 'B', 'C', 'D']:
                    status = controller.get_motor_status(motor_name)
                    if status:
                        motor_data = {
                            'motor': motor_name,
                            'angle': round(status.angle, 1),
                            'moving': status.moving,
                            'position': determine_position(status.angle, status.moving),
                            'timestamp': time.time()
                        }
                        archemedes_state['client'].publish(
                            f"{topic_prefix}/roboschlenk/motor/{motor_name}",
                            json.dumps(motor_data),
                            retain=True
                        )

    except Exception as e:
        print(f"Error publishing data: {e}")

def determine_position(angle, moving):
    """Determine position name from angle"""
    if moving:
        return "MOVING"
    elif abs(angle - 0) < 10 or abs(angle - 180) < 10:
        return "CLOSED"
    elif abs(angle - 90) < 10:
        return "GAS"
    elif abs(angle - 270) < 10:
        return "VACUUM"
    else:
        return "MOVING"

def start_publishing():
    """Start publishing data at regular intervals using background thread"""
    # Check if already publishing
    if archemedes_state['publish_thread'] and archemedes_state['publish_thread'].is_alive():
        print("Already publishing, skipping duplicate thread creation")
        return

    # Create stop event
    archemedes_state['stop_publishing_event'] = threading.Event()

    def publish_loop():
        """Background thread that publishes data every 2 seconds"""
        print("📡 Publishing thread started")

        # Publish immediately
        try:
            publish_data()
        except Exception as e:
            print(f"Error in initial publish: {e}")
            import traceback
            traceback.print_exc()

        # Continue publishing every 2 seconds until stopped
        while not archemedes_state['stop_publishing_event'].is_set():
            try:
                # Wait 2 seconds, but check stop event every 0.1s for responsiveness
                if archemedes_state['stop_publishing_event'].wait(timeout=2.0):
                    break  # Stop event was set

                publish_data()
            except Exception as e:
                print(f"Error in publish loop: {e}")
                import traceback
                traceback.print_exc()
                # Continue publishing even on error

        print("📡 Publishing thread stopped")

    # Start background thread
    archemedes_state['publish_thread'] = threading.Thread(target=publish_loop, daemon=True, name="ARChemedes-Publisher")
    archemedes_state['publish_thread'].start()

    ui.notify("📡 Starting data broadcast...", type='info')
    ui.notify("✅ Broadcasting ChemiSuite data every 2 seconds", type='positive')
    print(f"✅ Publishing thread started: {archemedes_state['publish_thread'].name}")

def stop_publishing():
    """Stop publishing data"""
    if archemedes_state['stop_publishing_event']:
        archemedes_state['stop_publishing_event'].set()

    if archemedes_state['publish_thread']:
        # Wait for thread to finish (with timeout)
        archemedes_state['publish_thread'].join(timeout=3.0)
        archemedes_state['publish_thread'] = None
        archemedes_state['stop_publishing_event'] = None

    ui.notify("⏸️ Stopped broadcasting data", type='info')
    print("⏸️ Publishing stopped")

def generate_viewer():
    """Generate standalone HTML viewer"""
    viewer_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChemiSuite Remote Viewer - ARChemedes</title>
    <script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,255,255,0.2);
            margin-bottom: 30px;
        }
        .header h1 { font-size: 48px; margin-bottom: 10px; }
        .header p { font-size: 18px; opacity: 0.8; }
        .status {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .status-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .connected { background: #00d26a; }
        .disconnected { background: #ff4757; }
        .config-panel {
            background: rgba(0,0,0,0.3);
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 14px;
        }
        .input-group input {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 14px;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover { background: #2980b9; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .card {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        .card h3 {
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }
        .badge-green { background: #10b981; }
        .badge-red { background: #ef4444; }
        .badge-blue { background: #3b82f6; }
        .badge-orange { background: #f97316; }
        .badge-grey { background: #888888; }
        .motor-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        .motor-item {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 8px;
        }
        .motor-item h4 {
            font-size: 16px;
            margin-bottom: 10px;
        }
        .angle {
            font-size: 24px;
            font-weight: bold;
            margin: 5px 0;
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 ChemiSuite Remote Viewer</h1>
            <p>Powered by ARChemedes</p>
        </div>

        <div id="configPanel" class="config-panel">
            <h2 style="margin-bottom: 20px;">Connect to MQTT Broker</h2>
            <div class="input-group">
                <label>Broker URL:</label>
                <input type="text" id="brokerUrl" value="broker.emqx.io" placeholder="broker.emqx.io">
            </div>
            <div class="input-group">
                <label>Port:</label>
                <input type="number" id="brokerPort" value="8083" placeholder="8083">
            </div>
            <div class="input-group">
                <label>Username (optional):</label>
                <input type="text" id="username" placeholder="username">
            </div>
            <div class="input-group">
                <label>Password (optional):</label>
                <input type="password" id="password" placeholder="password">
            </div>
            <div class="input-group">
                <label>Topic Prefix:</label>
                <input type="text" id="topicPrefix" value="chemisuite" placeholder="chemisuite">
            </div>
            <button onclick="connectToMQTT()">Connect</button>
        </div>

        <div class="status">
            <span class="status-dot disconnected" id="statusDot"></span>
            <span id="statusText">Disconnected</span>
        </div>

        <div id="dataContainer" class="grid"></div>
    </div>

    <script>
        let client = null;
        let fumeHoods = {};
        let motors = {};

        function connectToMQTT() {
            const broker = document.getElementById('brokerUrl').value;
            const port = parseInt(document.getElementById('brokerPort').value);
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const prefix = document.getElementById('topicPrefix').value;

            const url = `wss://${broker}:${port}/mqtt`;

            const options = {
                clientId: 'chemisuite_viewer_' + Math.random().toString(16).substr(2, 8),
                clean: true,
                reconnectPeriod: 1000
            };

            if (username && password) {
                options.username = username;
                options.password = password;
            }

            client = mqtt.connect(url, options);

            client.on('connect', function() {
                updateStatus(true);
                document.getElementById('configPanel').classList.add('hidden');

                // Subscribe to all topics
                client.subscribe(`${prefix}/fumehood/+/sash`);
                client.subscribe(`${prefix}/fumehood/+/devices`);
                client.subscribe(`${prefix}/roboschlenk/motor/+`);
            });

            client.on('message', function(topic, message) {
                try {
                    const data = JSON.parse(message.toString());

                    if (topic.includes('/fumehood/')) {
                        handleFumeHoodData(topic, data);
                    } else if (topic.includes('/roboschlenk/motor/')) {
                        handleMotorData(topic, data);
                    }

                    updateDisplay();
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            });

            client.on('error', function(error) {
                console.error('Connection error:', error);
                updateStatus(false);
            });

            client.on('close', function() {
                updateStatus(false);
            });
        }

        function handleFumeHoodData(topic, data) {
            const parts = topic.split('/');
            const hoodId = parts[parts.length - 2];

            if (!fumeHoods[hoodId]) {
                fumeHoods[hoodId] = {};
            }

            if (topic.endsWith('/sash')) {
                fumeHoods[hoodId].sash = data;
            } else if (topic.endsWith('/devices')) {
                fumeHoods[hoodId].devices = data;
            }
        }

        function handleMotorData(topic, data) {
            const motorName = data.motor;
            motors[motorName] = data;
        }

        function updateDisplay() {
            const container = document.getElementById('dataContainer');
            container.innerHTML = '';

            // Display fume hoods
            for (const [id, hood] of Object.entries(fumeHoods)) {
                if (hood.sash) {
                    const card = document.createElement('div');
                    card.className = 'card';

                    const sashBadge = hood.sash.sash_open ?
                        '<span class="badge badge-red">OPEN</span>' :
                        '<span class="badge badge-green">CLOSED</span>';

                    card.innerHTML = `
                        <h3>🧪 ${hood.sash.name}</h3>
                        <p style="margin-bottom: 10px; opacity: 0.7;">${hood.sash.location || 'No location'}</p>
                        <p><strong>Sash Status:</strong> ${sashBadge}</p>
                        <p style="margin-top: 10px; opacity: 0.6; font-size: 12px;">
                            Last update: ${new Date(hood.sash.timestamp * 1000).toLocaleTimeString()}
                        </p>
                    `;
                    container.appendChild(card);
                }
            }

            // Display RoboSchlenk motors
            if (Object.keys(motors).length > 0) {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = '<h3>⚙️ RoboSchlenk Motors</h3><div class="motor-grid" id="motorGrid"></div>';
                container.appendChild(card);

                const motorGrid = document.getElementById('motorGrid');
                for (const [name, motor] of Object.entries(motors).sort()) {
                    const positionColor = {
                        'CLOSED': 'badge-green',
                        'GAS': 'badge-blue',
                        'VACUUM': 'badge-orange',
                        'MOVING': 'badge-grey'
                    }[motor.position] || 'badge-grey';

                    const motorItem = document.createElement('div');
                    motorItem.className = 'motor-item';
                    motorItem.innerHTML = `
                        <h4>Motor ${name}</h4>
                        <span class="badge ${positionColor}">${motor.position}</span>
                        <div class="angle">${motor.angle.toFixed(1)}°</div>
                        <p style="opacity: 0.6; font-size: 11px; margin-top: 5px;">
                            ${new Date(motor.timestamp * 1000).toLocaleTimeString()}
                        </p>
                    `;
                    motorGrid.appendChild(motorItem);
                }
            }
        }

        function updateStatus(connected) {
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');

            if (connected) {
                dot.className = 'status-dot connected';
                text.textContent = 'Connected to MQTT Broker';
            } else {
                dot.className = 'status-dot disconnected';
                text.textContent = 'Disconnected';
            }
        }
    </script>
</body>
</html>'''.replace('BROKER_URL_PLACEHOLDER', archemedes_state['broker_url'] or 'broker.emqx.io')

    # Save viewer HTML file
    viewer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archemedes_viewer.html')
    try:
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(viewer_html)
        ui.notify(f"Remote viewer saved to: {viewer_path}", type='positive')
        ui.notify("Share this HTML file with anyone who needs remote access!", type='info')
    except Exception as e:
        ui.notify(f"Error saving viewer: {str(e)}", type='negative')

def render():
    """Render the ARChemedes page content"""

    # Load existing config
    load_config()

    # Check if we're already connected when rendering the page
    is_currently_connected = archemedes_state.get('connected', False)

    # Notify user if connection is active when they return to this page
    if is_currently_connected:
        ui.notify("📡 ARChemedes is currently broadcasting", type='info')

    with ui.column().style("width: 100%; max-width: 1400px; margin: 0 auto; padding: 20px; gap: 20px;"):
        # Header
        with ui.row().style("width: 100%; align-items: center; justify-content: space-between;"):
            with ui.column().style("gap: 5px;"):
                ui.label("ARChemedes").style("color: white; font-size: 32px; font-weight: bold;")
                ui.label("Remote Monitoring System").style("color: #888888; font-size: 16px;")

            # Status indicator - set initial state based on connection status
            if is_currently_connected:
                archemedes_state['status_label'] = ui.label("● Connected").style(
                    "color: #00d26a; font-size: 14px; font-weight: bold;"
                )
            else:
                archemedes_state['status_label'] = ui.label("● Disconnected").style(
                    "color: #ff4757; font-size: 14px; font-weight: bold;"
                )

        ui.separator().style("background-color: #444444;")

        # Info section
        with ui.card().style("background-color: #2c3e50; padding: 20px; width: 100%;"):
            with ui.row().style("gap: 15px; align-items: flex-start;"):
                ui.icon("info", size="32px").style("color: #3498db;")
                with ui.column().style("gap: 10px; flex: 1;"):
                    ui.label("About ARChemedes").style("color: white; font-size: 18px; font-weight: bold;")
                    ui.label(
                        "ARChemedes broadcasts your ChemiSuite data over the internet using MQTT, "
                        "allowing remote devices to monitor your lab in real-time without direct network access."
                    ).style("color: #cccccc; font-size: 14px; line-height: 1.5;")

                    with ui.expansion("Free MQTT Broker Options", icon="cloud").props("dense").style("margin-top: 10px;"):
                        with ui.column().style("padding: 10px; gap: 10px;"):
                            ui.label("Recommended free MQTT brokers:").style("color: white; font-weight: bold;")
                            ui.label("• HiveMQ Cloud - Free tier available at hivemq.com/cloud").style("color: #cccccc; font-size: 13px;")
                            ui.label("• EMQX Cloud (broker.emqx.io) - Port 1883, no auth needed for testing").style("color: #cccccc; font-size: 13px;")
                            ui.label("• Eclipse Mosquitto Test (test.mosquitto.org) - Port 1883, public test broker").style("color: #cccccc; font-size: 13px;")

        # Configuration section
        with ui.card().style("background-color: #444444; padding: 25px; width: 100%;"):
            ui.label("MQTT Broker Configuration").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 15px;")

            with ui.grid(columns=2).style("width: 100%; gap: 20px;"):
                # Broker URL
                broker_input = ui.input(
                    label="Broker URL",
                    placeholder="broker.emqx.io",
                    value=archemedes_state['broker_url']
                ).style("width: 100%;").props("dark outlined")

                # Broker Port
                port_input = ui.number(
                    label="Broker Port",
                    value=archemedes_state['broker_port'],
                    min=1,
                    max=65535
                ).style("width: 100%;").props("dark outlined")

                # Username
                username_input = ui.input(
                    label="Username (optional)",
                    placeholder="username",
                    value=archemedes_state['username']
                ).style("width: 100%;").props("dark outlined")

                # Password
                password_input = ui.input(
                    label="Password (optional)",
                    placeholder="password",
                    value=archemedes_state['password'],
                    password=True,
                    password_toggle_button=True
                ).style("width: 100%;").props("dark outlined")

            # Topic prefix
            with ui.row().style("width: 100%; margin-top: 10px;"):
                topic_input = ui.input(
                    label="Topic Prefix",
                    placeholder="chemisuite",
                    value=archemedes_state['topic_prefix']
                ).style("flex: 1;").props("dark outlined")

                ui.label("Topics: prefix/fumehood/id/..., prefix/roboschlenk/...").style(
                    "color: #888888; font-size: 12px; align-self: center; margin-left: 10px;"
                )

            # Buttons
            with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 20px;"):
                def save_settings():
                    archemedes_state['broker_url'] = broker_input.value
                    archemedes_state['broker_port'] = int(port_input.value)
                    archemedes_state['username'] = username_input.value
                    archemedes_state['password'] = password_input.value
                    archemedes_state['topic_prefix'] = topic_input.value

                    if save_config():
                        ui.notify("Configuration saved", type='positive')
                    else:
                        ui.notify("Failed to save configuration", type='negative')

                # Set button initial state based on connection status
                if is_currently_connected:
                    connect_button = ui.button(
                        "Stop Broadcasting",
                        color="negative"
                    ).props("icon=broadcast_on_personal")
                else:
                    connect_button = ui.button(
                        "Connect & Start Broadcasting",
                        color="positive"
                    ).props("icon=broadcast")

                def toggle_connection():
                    if archemedes_state['connected']:
                        stop_publishing()
                        disconnect_from_broker()
                        connect_button.text = "Connect & Start Broadcasting"
                        connect_button.props("color=positive icon=broadcast")
                    else:
                        # Save config first
                        save_settings()
                        # Reset connection message
                        archemedes_state['connection_message'] = None
                        if connect_to_broker():
                            # Start a timer to check for connection status
                            def check_connection_status():
                                if archemedes_state.get('connection_message') == 'success':
                                    ui.notify("✅ Successfully connected to MQTT broker!", type='positive')
                                    ui.notify("🚀 ChemiSuite is now broadcasting data", type='positive')
                                    if archemedes_state['status_label']:
                                        archemedes_state['status_label'].set_text("● Connected")
                                        archemedes_state['status_label'].style("color: #00d26a; font-size: 14px; font-weight: bold;")
                                    archemedes_state['connection_message'] = None
                                    start_publishing()
                                    connect_button.text = "Stop Broadcasting"
                                    connect_button.props("color=negative icon=broadcast_on_personal")
                                elif archemedes_state.get('connection_message', '').startswith('failed:'):
                                    error_msg = archemedes_state['connection_message'].replace('failed:', '')
                                    ui.notify(f"❌ Connection failed: {error_msg}", type='negative')
                                    if archemedes_state['status_label']:
                                        archemedes_state['status_label'].set_text("● Disconnected")
                                        archemedes_state['status_label'].style("color: #ff4757; font-size: 14px; font-weight: bold;")
                                    archemedes_state['connection_message'] = None
                                elif archemedes_state.get('connection_message') is not None:
                                    # Still waiting, check again
                                    ui.timer(0.1, check_connection_status, once=True)

                            ui.timer(0.1, check_connection_status, once=True)

                connect_button.on_click(toggle_connection)

                ui.button("Save Configuration", on_click=save_settings).props("outline color=primary")

        # Published Topics section
        with ui.card().style("background-color: #444444; padding: 25px; width: 100%;"):
            ui.label("Published Topics").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 15px;")

            with ui.column().style("gap: 10px;"):
                ui.label("ChemiSuite publishes the following data topics:").style("color: #cccccc; font-size: 14px;")

                with ui.card().style("background-color: #333333; padding: 15px;"):
                    ui.label("Fume Hood Topics:").style("color: white; font-weight: bold; margin-bottom: 5px;")
                    ui.label("• {prefix}/fumehood/{id}/sash - Sash status and safety info").style("color: #cccccc; font-size: 13px; font-family: monospace;")
                    ui.label("• {prefix}/fumehood/{id}/devices - Assigned devices").style("color: #cccccc; font-size: 13px; font-family: monospace;")

                with ui.card().style("background-color: #333333; padding: 15px;"):
                    ui.label("RoboSchlenk Topics:").style("color: white; font-weight: bold; margin-bottom: 5px;")
                    ui.label("• {prefix}/roboschlenk/motor/A - Motor A status (angle, position, moving)").style("color: #cccccc; font-size: 13px; font-family: monospace;")
                    ui.label("• {prefix}/roboschlenk/motor/B - Motor B status").style("color: #cccccc; font-size: 13px; font-family: monospace;")
                    ui.label("• {prefix}/roboschlenk/motor/C - Motor C status").style("color: #cccccc; font-size: 13px; font-family: monospace;")
                    ui.label("• {prefix}/roboschlenk/motor/D - Motor D status").style("color: #cccccc; font-size: 13px; font-family: monospace;")

        # Remote Viewer section
        with ui.card().style("background-color: #444444; padding: 25px; width: 100%;"):
            ui.label("Remote Viewer").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 15px;")

            with ui.column().style("gap: 15px;"):
                ui.label(
                    "Generate a standalone HTML file that can be opened on any device to view your lab data in real-time. "
                    "Share this file with colleagues, students, or supervisors - they just need to open it in a web browser!"
                ).style("color: #cccccc; font-size: 14px; line-height: 1.5;")

                ui.button(
                    "Generate Remote Viewer HTML",
                    on_click=lambda: generate_viewer(),
                    color="primary"
                ).props("icon=code")
