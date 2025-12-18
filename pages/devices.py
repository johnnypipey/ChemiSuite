# pages/devices.py
from nicegui import ui
import devices as device_modules
import serial.tools.list_ports
import cv2
import asyncio

# Store devices (in a real app, this would be in a database or state management)
devices = []

# Container reference for re-rendering
device_container = None

# Dictionary to store active device webcam captures and latest frames
active_device_webcam_captures = {}  # Format: {(device_name, webcam_name): {'capture': cv2.VideoCapture, 'frame_base64': str, 'running': bool, 'images': []}}

def cleanup_all_device_webcams():
    """Disconnect all device webcams and release resources - called on app shutdown"""
    global active_device_webcam_captures

    print("Cleaning up all device webcams...")
    keys_to_remove = list(active_device_webcam_captures.keys())

    for key in keys_to_remove:
        try:
            # Stop the update loop
            active_device_webcam_captures[key]['running'] = False

            # Release the capture
            cap = active_device_webcam_captures[key]['capture']
            if cap.isOpened():
                cap.release()

            print(f"Released device webcam: {key}")
        except Exception as e:
            print(f"Error releasing device webcam {key}: {e}")

    # Clear the dictionary
    active_device_webcam_captures.clear()

    # Give OpenCV time to release resources
    cv2.destroyAllWindows()
    print("All device webcams cleaned up")

def connect_device_webcam(device, webcam):
    """Connect to a USB camera for device monitoring and start streaming"""
    key = (device['name'], webcam['name'])

    # Check if already connected
    if key in active_device_webcam_captures:
        ui.notify(f"Webcam '{webcam['name']}' is already connected", type='warning')
        return False

    try:
        device_id = int(webcam['url'])
        # Use DirectShow backend to avoid MSMF conflicts when multiple cameras are used
        cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)

        if not cap.isOpened():
            ui.notify(f"Failed to open camera {device_id}", type='negative')
            return False

        # Store capture and frame data
        active_device_webcam_captures[key] = {
            'capture': cap,
            'frame_base64': None,
            'running': True,
            'images': []  # List of image elements to update
        }

        # Start async frame update
        asyncio.create_task(update_device_webcam_frame(key))

        ui.notify(f"Connected to webcam '{webcam['name']}'", type='positive')
        return True

    except Exception as e:
        ui.notify(f"Error connecting to webcam: {str(e)}", type='negative')
        return False

def disconnect_device_webcam(device, webcam):
    """Disconnect from a USB camera and stop streaming"""
    key = (device['name'], webcam['name'])

    if key not in active_device_webcam_captures:
        ui.notify(f"Webcam '{webcam['name']}' is not connected", type='warning')
        return False

    try:
        # Stop the update loop
        active_device_webcam_captures[key]['running'] = False

        # Release the capture
        cap = active_device_webcam_captures[key]['capture']
        cap.release()

        # Remove from active captures
        del active_device_webcam_captures[key]

        ui.notify(f"Disconnected webcam '{webcam['name']}'", type='info')
        return True

    except Exception as e:
        ui.notify(f"Error disconnecting webcam: {str(e)}", type='negative')
        return False

async def update_device_webcam_frame(key):
    """Async function to continuously update device webcam frames"""
    import base64

    while key in active_device_webcam_captures and active_device_webcam_captures[key]['running']:
        try:
            cap = active_device_webcam_captures[key]['capture']

            ret, frame = cap.read()

            if ret:
                # Resize frame for display (640x480)
                frame = cv2.resize(frame, (640, 480))

                # Encode frame to JPEG (cv2.imencode expects BGR format)
                _, buffer = cv2.imencode('.jpg', frame)

                # Convert to base64
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                data_url = f'data:image/jpeg;base64,{img_base64}'

                # Store the frame
                active_device_webcam_captures[key]['frame_base64'] = data_url

                # Update all registered image elements
                for img_element in active_device_webcam_captures[key]['images']:
                    try:
                        img_element.set_source(data_url)
                    except:
                        pass  # Element might have been deleted

            # Wait before next frame (30 FPS)
            await asyncio.sleep(0.033)

        except Exception as e:
            print(f"Error updating device webcam frame for {key}: {e}")
            break

    # Clean up if loop exits due to error
    if key in active_device_webcam_captures:
        try:
            active_device_webcam_captures[key]['capture'].release()
            del active_device_webcam_captures[key]
        except:
            pass

def register_device_webcam_image(device, webcam, image_element):
    """Register an image element to receive device webcam updates"""
    key = (device['name'], webcam['name'])
    if key in active_device_webcam_captures:
        active_device_webcam_captures[key]['images'].append(image_element)
        # Set initial frame if available
        if active_device_webcam_captures[key]['frame_base64']:
            image_element.set_source(active_device_webcam_captures[key]['frame_base64'])

def get_available_cameras():
    """Detect available USB cameras"""
    available_cameras = []

    # Test cameras 0-4 (most systems won't have more than 5 cameras)
    for i in range(5):
        try:
            # Use DirectShow on Windows to avoid Intel RealSense issues
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

            # Set a short timeout
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)

            if cap.isOpened():
                # Try to read a frame to confirm camera is working
                ret, _ = cap.read()
                if ret:
                    available_cameras.append({
                        'id': i,
                        'name': f"Camera {i}"
                    })
                cap.release()
        except Exception as e:
            print(f"Error checking camera {i}: {e}")
            continue

    return available_cameras

def show_add_device_dialog():
    """Show the add device wizard dialog"""
    with ui.dialog() as dialog, ui.card().style("min-width: 500px; background-color: #2a2a2a;"):
        ui.label("Add Device").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        # Device selection
        ui.label("Select Device Type:").style("color: white; font-size: 16px; margin-bottom: 10px;")

        # Build device options from registered devices
        available_devices = device_modules.get_all_devices()
        device_options = {module.get_device_info()['display_name']: module for module in available_devices}

        selected_device = {'type': None, 'name': '', 'module': None}

        # Get available COM ports from system
        ports = serial.tools.list_ports.comports()
        com_ports = []
        for port in ports:
            # Format: "COM3 - USB Serial Device (COM3)"
            com_ports.append(f"{port.device} - {port.description}")

        # If no ports found, add a message
        if not com_ports:
            com_ports = ["No COM ports detected"]

        def on_device_select(device_name):
            device_module = device_options[device_name]
            device_info = device_module.get_device_info()

            selected_device['type'] = device_info['type']
            selected_device['module'] = device_module
            device_name_input.set_value(device_name)

            # Clear and show device-specific fields
            device_fields_container.clear()
            with device_fields_container:
                device_module.show_wizard_fields(selected_device, com_ports)

        # Device type buttons in a grid (2 columns)
        with ui.grid(columns=2).style("gap: 10px; margin-bottom: 20px; width: 100%;"):
            for device_name, device_module in device_options.items():
                device_info = device_module.get_device_info()

                # Create button with image on top and name below
                with ui.button(on_click=lambda d=device_name: on_device_select(d)).props("outline").style("width: 100%; padding: 15px;"):
                    with ui.column().style("align-items: center; gap: 10px; width: 100%;"):
                        # Device image
                        if device_info.get('image'):
                            ui.image(device_info['image']).style("width: 80px; height: 80px; object-fit: contain;")
                        ui.label(device_name).style("color: white; font-size: 16px; text-align: center;")

        # Device name input
        ui.label("Device Name:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        device_name_input = ui.input(placeholder="Enter device name").style("width: 100%;").props("dark outlined")

        # Container for device-specific fields (initially empty)
        # This is placed AFTER the device name input so it appears below
        device_fields_container = ui.column().style("width: 100%; margin-top: 20px;")

        # Dialog buttons
        with ui.row().style("gap: 10px; margin-top: 30px; justify-content: flex-end; width: 100%;"):
            ui.button("Cancel", on_click=dialog.close).props("flat")

            def add_device():
                if not selected_device['type'] or not device_name_input.value:
                    ui.notify("Please select a device type and enter a name", type='warning')
                    return

                # Validate device-specific fields
                device_module = selected_device['module']
                if device_module:
                    is_valid, error_msg = device_module.validate_wizard_fields(selected_device)
                    if not is_valid:
                        ui.notify(error_msg, type='warning')
                        return

                # Check for duplicate names
                if any(d['name'] == device_name_input.value for d in devices):
                    ui.notify(f"A device named '{device_name_input.value}' already exists", type='negative')
                    return

                # Build device data from selected_device
                device_data = {
                    'type': selected_device['type'],
                    'name': device_name_input.value,
                    'icon': device_module.get_device_info()['icon'] if device_module else None,
                    'webcams': []  # Initialize empty webcams list
                }
                # Add any additional fields from selected_device (e.g., com_port)
                for key, value in selected_device.items():
                    if key not in ['type', 'name', 'module']:
                        device_data[key] = value

                # Add loggable parameters if device module provides them
                if device_module and hasattr(device_module, 'get_loggable_parameters'):
                    device_data['loggable_parameters'] = device_module.get_loggable_parameters()

                devices.append(device_data)
                dialog.close()

                # Create notification message
                notify_msg = f"Added device: {device_name_input.value}"
                if 'com_port' in device_data:
                    notify_msg += f" on {device_data['com_port']}"

                ui.notify(notify_msg, type='positive')

                # Re-render the device list
                refresh_device_list()

            ui.button("Add Device", on_click=add_device).props("color=primary")

    dialog.open()

def refresh_device_list():
    """Refresh the device list display"""
    global device_container
    if device_container:
        device_container.clear()
        with device_container:
            render_device_list()

def render_device_list():
    """Render the device tabs and panels"""
    if devices:
        with ui.tabs().props("dense").classes("text-white") as tabs:
            for i, device in enumerate(devices):
                # Use custom icon if available, otherwise use default
                if device.get('icon'):
                    with ui.tab(device['name']).classes("text-white"):
                        ui.image(device['icon']).style("width: 20px; height: 20px;")
                else:
                    ui.tab(device['name'], icon="devices").classes("text-white")

        with ui.tab_panels(tabs, value=devices[0]['name'] if devices else None).style("background-color: transparent; width: 100%; height: calc(100vh - 310px); overflow-y: auto;"):
            for device in devices:
                with ui.tab_panel(device['name']):
                    render_device_panel(device)
    else:
        ui.label("No devices connected").style("color: #888888; font-size: 16px; margin-top: 20px;")

def render():
    """Render the devices page content"""
    global device_container

    with ui.column().style("padding: 20px; width: 100%; gap: 20px;"):
        # Add device button at top
        ui.button("Add Device", icon="add", on_click=show_add_device_dialog).props("color=primary")

        # Device list container (for dynamic updates)
        device_container = ui.column().style("width: 100%;")
        with device_container:
            render_device_list()

def edit_device(device):
    """Show dialog to edit device name and COM port"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Edit Device").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        edited_data = {
            'name': device['name'],
            'com_port': device.get('com_port')
        }

        # Name input
        ui.label("Device Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(value=device['name'], placeholder="Enter device name").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            edited_data['name'] = e.value

        name_input.on_value_change(on_name_change)

        # COM port selection (if device has com_port field)
        if 'com_port' in device:
            ui.label("COM Port:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")

            # Get available COM ports
            ports = serial.tools.list_ports.comports()
            com_port_options = []
            for port in ports:
                com_port_options.append(f"{port.device} - {port.description}")

            if not com_port_options:
                com_port_options = ["No COM ports detected"]

            # Find current port in options
            current_port_display = None
            if device.get('com_port'):
                for option in com_port_options:
                    if option.startswith(device.get('com_port')):
                        current_port_display = option
                        break

            com_port_select = ui.select(com_port_options, value=current_port_display).style("width: 100%;").props("dark outlined")

            def on_com_port_change(e):
                if e.value and e.value != "No COM ports detected":
                    # Extract port name (e.g., "COM3" from "COM3 - USB Serial Device")
                    port_name = e.value.split(' - ')[0]
                    edited_data['com_port'] = port_name
                else:
                    edited_data['com_port'] = None

            com_port_select.on_value_change(on_com_port_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def save_changes():
                # Validate name
                if not edited_data['name']:
                    ui.notify("Please enter a device name", type='warning')
                    return

                # Check if new name conflicts with another device
                if edited_data['name'] != device['name']:
                    if any(d['name'] == edited_data['name'] for d in devices):
                        ui.notify("A device with this name already exists", type='warning')
                        return

                # Update device
                old_name = device['name']
                device['name'] = edited_data['name']
                if 'com_port' in edited_data:
                    device['com_port'] = edited_data['com_port']

                ui.notify(f"Device '{old_name}' updated successfully", type='positive')
                dialog.close()

                # Refresh the device list
                refresh_device_list()

            ui.button("Save Changes", icon="save", on_click=save_changes).props("color=primary")

    dialog.open()

def remove_device(device_name):
    """Remove a device by name"""
    global devices

    # Find the device
    device_to_remove = None
    for d in devices:
        if d['name'] == device_name:
            device_to_remove = d
            break

    # Disconnect all webcams before removing
    if device_to_remove and 'webcams' in device_to_remove:
        for webcam in device_to_remove['webcams']:
            key = (device_name, webcam['name'])
            if key in active_device_webcam_captures:
                disconnect_device_webcam(device_to_remove, webcam)

    # Cleanup before removal
    if device_to_remove and 'driver' in device_to_remove:
        driver = device_to_remove['driver']
        if driver and hasattr(driver, 'connected') and driver.connected:
            try:
                # Stop all operations for safety
                driver.set_temperature(0, sensor_type=2)
                driver.stop_heating(sensor_type=2)
                driver.set_speed(0)
                driver.stop_stirring()
                # Disconnect and close serial port
                driver.disconnect()
            except Exception as e:
                print(f"Error during device cleanup: {e}")

    # Remove from list
    devices = [d for d in devices if d['name'] != device_name]
    ui.notify(f"Removed device: {device_name}", type='positive')

    refresh_device_list()

def render_device_panel(device):
    """Render the control panel for a specific device"""
    # Get the device module
    device_module = device_modules.get_device_module(device['type'])

    if device_module:
        # Use the device module's render function with edit and remove callbacks
        device_module.render_control_panel(
            device,
            on_edit=lambda: edit_device(device),
            on_remove=lambda: remove_device(device['name'])
        )
    else:
        # Fallback if device module not found
        with ui.column().style("padding: 20px;"):
            ui.label(f"Unknown device type: {device['type']}").style("color: #ff0000; font-size: 16px;")
