#!/usr/bin/env python3
"""
Test MQTT Connection to HiveMQ
Simple script to verify broker credentials and connectivity
"""

import paho.mqtt.client as mqtt
import time
import sys

# Configuration - UPDATE THESE WITH YOUR HIVEMQ DETAILS
BROKER_HOST = "bffb82f07881437fa60424b51654251b.s1.eu.hivemq.cloud"  # Replace with your HiveMQ host
BROKER_PORT = 8883  # HiveMQ secure port
USERNAME = "chemisuite"  # Replace with your username
PASSWORD = "arcLAB25"  # Replace with your password

# Test results
test_results = {
    'connected': False,
    'published': False,
    'received': False
}

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"   Connected to {BROKER_HOST}:{BROKER_PORT}")
        test_results['connected'] = True

        # Subscribe to test topic
        client.subscribe("chemisuite/test")
        print("📡 Subscribed to test topic")

        # Publish test message
        print("📤 Publishing test message...")
        result = client.publish("chemisuite/test", "Hello from ChemiSuite!", qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ MESSAGE PUBLISHED SUCCESSFULLY!")
            test_results['published'] = True
        else:
            print(f"❌ Failed to publish message: {result.rc}")
    else:
        print(f"❌ CONNECTION FAILED!")
        print(f"   Error code: {rc}")
        print("\n   Error meanings:")
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        if rc in error_messages:
            print(f"   {error_messages[rc]}")

        if rc == 4:
            print("\n   ⚠️  Check your username and password!")
        elif rc == 5:
            print("\n   ⚠️  Check your HiveMQ access permissions!")

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    print(f"📥 MESSAGE RECEIVED!")
    print(f"   Topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")
    test_results['received'] = True

def on_publish(client, userdata, mid):
    """Callback when message is published"""
    print(f"📤 Message published (ID: {mid})")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"\n⚠️  Unexpected disconnection. Code: {rc}")

def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 ARChemedes MQTT Connection Test")
    print("=" * 80)
    print()

    # Validate configuration
    if BROKER_HOST == "your-hivemq-host.s1.eu.hivemq.cloud":
        print("❌ ERROR: Please update the BROKER_HOST in the script!")
        print("   Edit lines 10-13 with your actual HiveMQ credentials")
        sys.exit(1)

    if USERNAME == "your-username":
        print("❌ ERROR: Please update the USERNAME in the script!")
        print("   Edit lines 10-13 with your actual HiveMQ credentials")
        sys.exit(1)

    print(f"📋 Configuration:")
    print(f"   Host: {BROKER_HOST}")
    print(f"   Port: {BROKER_PORT}")
    print(f"   Username: {USERNAME}")
    print(f"   Password: {'*' * len(PASSWORD)}")
    print()

    # Create MQTT client
    client_id = f"test_client_{int(time.time())}"
    print(f"🔧 Creating MQTT client (ID: {client_id})")
    client = mqtt.Client(client_id=client_id)

    # Set credentials
    print("🔑 Setting credentials...")
    client.username_pw_set(USERNAME, PASSWORD)

    # Enable TLS for HiveMQ
    print("🔒 Enabling TLS/SSL encryption...")
    try:
        client.tls_set()
    except Exception as e:
        print(f"❌ TLS setup failed: {e}")
        sys.exit(1)

    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    try:
        # Connect to broker
        print(f"\n🔌 Connecting to {BROKER_HOST}:{BROKER_PORT}...")
        print("   (This may take a few seconds...)")
        client.connect(BROKER_HOST, BROKER_PORT, 60)

        # Start network loop in background
        client.loop_start()

        # Wait for connection and message exchange
        print("\n⏳ Waiting for results...")
        time.sleep(5)

        # Stop loop
        client.loop_stop()
        client.disconnect()

        # Print results
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS:")
        print("=" * 80)
        print(f"Connection:  {'✅ PASS' if test_results['connected'] else '❌ FAIL'}")
        print(f"Publish:     {'✅ PASS' if test_results['published'] else '❌ FAIL'}")
        print(f"Receive:     {'✅ PASS' if test_results['received'] else '❌ FAIL'}")
        print("=" * 80)

        if all(test_results.values()):
            print("\n🎉 ALL TESTS PASSED!")
            print("   Your HiveMQ connection is working correctly.")
            print("   ChemiSuite should be able to broadcast successfully.")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("\nTroubleshooting steps:")
            if not test_results['connected']:
                print("1. Verify your HiveMQ host URL (no https://, no trailing /)")
                print("2. Check username and password are correct")
                print("3. Make sure your HiveMQ cluster is running")
                print("4. Check your internet connection")
                print("5. Verify firewall allows port 8883")
            elif not test_results['published']:
                print("1. Check your HiveMQ access permissions")
                print("2. Verify you have publish rights on the topic")
            elif not test_results['received']:
                print("1. This might be a timing issue - try running again")
                print("2. Check your HiveMQ subscription permissions")

        print()

    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        client.disconnect()
    except ConnectionRefusedError:
        print("\n❌ CONNECTION REFUSED!")
        print("   The broker rejected the connection.")
        print("\nPossible causes:")
        print("   - Wrong host or port")
        print("   - Firewall blocking connection")
        print("   - HiveMQ cluster not running")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nCommon issues:")
        print("   - Check broker host format (e.g., 'abc123.s1.eu.hivemq.cloud')")
        print("   - No 'https://' or 'mqtt://' prefix needed")
        print("   - Username/password must match HiveMQ Access Management")
        print("   - Make sure HiveMQ cluster is active")

if __name__ == "__main__":
    main()
