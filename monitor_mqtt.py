#!/usr/bin/env python3
"""
Simple MQTT Monitor for ARChemedes
Shows all messages being broadcast by ChemiSuite
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime

# Configuration - UPDATE THESE WITH YOUR HIVEMQ DETAILS
BROKER_HOST = "bffb82f07881437fa60424b51654251b.s1.eu.hivemq.cloud"  # Replace with your HiveMQ host
BROKER_PORT = 8883  # HiveMQ secure port
USERNAME = "chemisuite"  # Replace with your username
PASSWORD = "arcLAB25"  # Replace with your password
TOPIC_PREFIX = "chemisuite"  # Must match ChemiSuite configuration

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("✅ Connected to MQTT broker")
        print(f"📡 Listening to all topics under: {TOPIC_PREFIX}/#")
        print("-" * 80)
        # Subscribe to all topics under the prefix
        client.subscribe(f"{TOPIC_PREFIX}/#")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    try:
        # Parse JSON data
        data = json.loads(msg.payload.decode())

        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Print topic and data
        print(f"\n[{timestamp}] 📨 Topic: {msg.topic}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print("-" * 80)

    except json.JSONDecodeError:
        print(f"\n❌ Invalid JSON on topic {msg.topic}: {msg.payload.decode()}")
    except Exception as e:
        print(f"\n❌ Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"\n⚠️  Unexpected disconnection. Code: {rc}")

def main():
    """Main monitoring function"""
    print("🧪 ARChemedes MQTT Monitor")
    print("=" * 80)

    # Create MQTT client
    client = mqtt.Client(client_id=f"monitor_{datetime.now().timestamp()}")

    # Set credentials
    client.username_pw_set(USERNAME, PASSWORD)

    # Enable TLS for HiveMQ
    client.tls_set()

    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        # Connect to broker
        print(f"🔌 Connecting to {BROKER_HOST}:{BROKER_PORT}...")
        client.connect(BROKER_HOST, BROKER_PORT, 60)

        # Start listening (blocking call)
        print("⏳ Waiting for messages... (Press Ctrl+C to stop)")
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
        client.disconnect()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your broker host, username, and password")
        print("2. Make sure ChemiSuite is broadcasting")
        print("3. Verify your internet connection")

if __name__ == "__main__":
    main()
