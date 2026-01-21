# ARChemedes - Remote Monitoring System

ARChemedes allows you to broadcast ChemiSuite data over the internet using MQTT, enabling remote monitoring from any device without requiring direct network access.

## Installation

Install the required MQTT library:

```bash
pip install paho-mqtt
```

## Setup

1. **Choose a Free MQTT Broker**:
   - **EMQX Cloud** (Recommended for testing):
     - Broker: `broker.emqx.io`
     - Port: `1883` (for ChemiSuite publisher) or `8083` (for web viewer)
     - No authentication required for testing

   - **Eclipse Mosquitto Test Server**:
     - Broker: `test.mosquitto.org`
     - Port: `1883`
     - Public test broker (not for production)

   - **HiveMQ Cloud** (Best for production):
     - Sign up at: https://www.hivemq.com/cloud/
     - Free tier: 100 connections
     - Provides secure credentials

2. **Configure ARChemedes in ChemiSuite**:
   - Open ChemiSuite
   - Navigate to "ARChemedes" in the sidebar
   - Enter your MQTT broker details:
     - Broker URL (e.g., `broker.emqx.io`)
     - Port (e.g., `1883`)
     - Username/Password (if required by your broker)
     - Topic Prefix (default: `chemisuite`)
   - Click "Save Configuration"

3. **Start Broadcasting**:
   - Click "Connect & Start Broadcasting"
   - ChemiSuite will now publish data every 2 seconds to the MQTT broker

4. **Generate Remote Viewer**:
   - Click "Generate Remote Viewer HTML"
   - Share the generated `archemedes_viewer.html` file with anyone who needs remote access
   - They can open it in any web browser (Chrome, Firefox, Safari, Edge, etc.)

## Remote Viewer Setup

The remote viewer is a standalone HTML file that can be opened on any device:

1. **Open the Viewer**:
   - Double-click `archemedes_viewer.html`
   - It will open in your default web browser

2. **Configure Connection**:
   - Enter the same broker details as ChemiSuite:
     - Broker URL
     - Port (use `8083` for WebSocket connections)
     - Username/Password (if applicable)
     - Topic Prefix (must match ChemiSuite's prefix)
   - Click "Connect"

3. **View Real-time Data**:
   - Once connected, you'll see real-time updates of:
     - Fume hood sash status
     - RoboSchlenk motor positions and angles
     - All connected devices

## Published Topics

ARChemedes publishes the following MQTT topics:

### Fume Hood Topics
- `{prefix}/fumehood/{id}/sash` - Sash status (open/closed), location, safety info
- `{prefix}/fumehood/{id}/devices` - Assigned devices list

### RoboSchlenk Topics
- `{prefix}/roboschlenk/motor/A` - Motor A status (angle, position, moving state)
- `{prefix}/roboschlenk/motor/B` - Motor B status
- `{prefix}/roboschlenk/motor/C` - Motor C status
- `{prefix}/roboschlenk/motor/D` - Motor D status

## Data Format

All data is published as JSON with timestamps:

### Fume Hood Sash Example:
```json
{
  "name": "Main Fume Hood",
  "sash_open": false,
  "location": "Lab 101",
  "timestamp": 1234567890.123
}
```

### RoboSchlenk Motor Example:
```json
{
  "motor": "A",
  "angle": 90.5,
  "moving": false,
  "position": "GAS",
  "timestamp": 1234567890.123
}
```

## Security Notes

- **Free public brokers** (like EMQX public or Mosquitto test) are **NOT secure** and should only be used for testing
- For production use, consider:
  - Using a private MQTT broker with authentication
  - Enabling TLS/SSL encryption
  - Using a dedicated topic prefix to avoid conflicts
  - Setting up access control lists (ACLs)

## Troubleshooting

### ChemiSuite won't connect:
- Check your internet connection
- Verify broker URL and port are correct
- Try using a public test broker first (`broker.emqx.io:1883`)
- Check firewall settings (MQTT typically uses ports 1883, 8883)

### Remote viewer won't connect:
- Use port `8083` for WebSocket connections (not `1883`)
- Check browser console for errors (F12)
- Ensure the topic prefix matches exactly with ChemiSuite
- Try using `wss://` protocol for secure connections

### No data appearing:
- Ensure ChemiSuite is broadcasting (check status indicator)
- Verify topic prefix matches between ChemiSuite and viewer
- Check that devices are actually generating data (e.g., fume hood connected, RoboSchlenk active)
- Use an MQTT client tool (like MQTT Explorer) to verify messages are being published

## Use Cases

- **Remote Lab Monitoring**: Check lab status from home or office
- **Safety Oversight**: Monitor fume hood usage from supervisor desk
- **Multi-Site Access**: Share lab data with collaborators at other institutions
- **Mobile Monitoring**: View lab status on phone or tablet
- **Student Access**: Allow students to monitor experiments remotely

## Network Restrictions

ARChemedes is specifically designed to work over the internet, bypassing university network restrictions:
- **No port forwarding required**
- **No VPN needed**
- **Works through firewalls**
- **Works on restricted networks** (like university WiFi)

The MQTT broker acts as an intermediary, allowing ChemiSuite and remote viewers to communicate without direct network connectivity.
