# devices/wpi_syringe_pump.py
"""
WPI Syringe Pump device module for ChemiSuite
"""
from nicegui import ui
import os


def get_device_info():
    """Return basic device information"""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'syringe-outline.png')
    image_path = os.path.join(os.path.dirname(__file__), 'images', 'syringe_pump.png')
    return {
        'display_name': 'WPI Syringe Pump',
        'type': 'wpi_syringe_pump',
        'icon': icon_path,
        'image': image_path
    }


def get_loggable_parameters():
    """Return parameters that can be logged for this device"""
    return {
        'flow_rate': {
            'method': 'get_flow_rate',
            'unit': 'µL/min',
            'args': {},
            'display_name': 'Flow Rate'
        },
        'volume_dispensed': {
            'method': 'get_volume_dispensed',
            'unit': 'µL',
            'args': {},
            'display_name': 'Volume Dispensed'
        },
        'pump_status': {
            'method': 'get_pump_status',
            'unit': '',
            'args': {},
            'display_name': 'Pump Status'
        }
    }


def show_wizard_fields(selected_device, com_ports):
    """
    Show device-specific wizard configuration fields

    Args:
        selected_device: Dictionary to store device configuration
        com_ports: List of available COM ports

    Returns:
        List of UI elements created (for cleanup if needed)
    """
    elements = []

    # COM port selection
    com_port_container = ui.column().style("width: 100%; margin-top: 20px;")
    with com_port_container:
        ui.label("Select COM Port:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        com_port_select = ui.select(com_ports, value=None).style("width: 100%;").props("dark outlined")

        def on_port_change(e):
            # Extract just the COM port name (e.g., "COM3" from "COM3 - USB Serial Device")
            port_value = e.value
            if port_value and ' - ' in port_value:
                com_port = port_value.split(' - ')[0]
            else:
                com_port = port_value
            selected_device.update({'com_port': com_port})

        com_port_select.on_value_change(on_port_change)

    elements.append(com_port_container)
    return elements


def validate_wizard_fields(selected_device):
    """
    Validate the device configuration from wizard

    Args:
        selected_device: Dictionary with device configuration

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if 'com_port' not in selected_device or not selected_device['com_port']:
        return False, "Please select a COM port"

    return True, ""


def render_control_panel(device, on_edit=None, on_remove=None):
    """
    Render the device control panel

    Args:
        device: Device dictionary containing name, com_port, driver, etc.
        on_edit: Callback function for editing device
        on_remove: Callback function for removing device
    """
    # Initialize driver placeholder (will be implemented later)
    if 'driver' not in device or device['driver'] is None:
        device['driver'] = None  # Placeholder for actual driver

    # Connection state
    connection_state = device.setdefault('connection_state', {
        'connected': False,
        'status_label': None,
        'connect_button': None
    })

    # Device header
    with ui.card().style("background-color: #444444; padding: 20px; width: 100%; margin-bottom: 20px;"):
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center;"):
            # Left: Device name and COM port
            with ui.column().style("gap: 5px;"):
                ui.label(device['name']).style("color: white; font-size: 20px; font-weight: bold;")
                ui.label(f"COM Port: {device.get('com_port', 'N/A')}").style("color: #888888; font-size: 14px;")

            # Right: Edit and Remove buttons
            with ui.row().style("gap: 10px;"):
                if on_edit:
                    ui.button("Edit", icon="edit", on_click=on_edit).props("flat color=white")
                if on_remove:
                    ui.button("Remove Device", icon="delete", on_click=on_remove).props("flat color=negative")

    # Three column layout
    with ui.row().style("width: 100%; gap: 20px; margin-bottom: 20px;"):
        # Left column - Device Image
        with ui.column().style("flex: 0 0 300px; gap: 20px;"):
            with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                ui.label("Device").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                # Display device image
                device_info = get_device_info()
                if os.path.exists(device_info['image']):
                    ui.image(device_info['image']).style("width: 100%; border-radius: 8px;")
                else:
                    ui.label("No image available").style("color: #888888; font-size: 14px;")

        # Middle column - Connection and Status
        with ui.column().style("flex: 1; gap: 20px;"):
            # Connection control card
            with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                ui.label("Connection").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                with ui.row().style("gap: 15px; align-items: center;"):
                    def toggle_connection():
                        """Toggle connection to pump (placeholder)"""
                        if not connection_state['connected']:
                            # Connect (placeholder)
                            connection_state['connected'] = True
                            connection_state['status_label'].set_text("Connected")
                            connection_state['status_label'].style("color: #66bb6a; font-weight: bold;")
                            connection_state['connect_button'].props("color=negative")
                            connection_state['connect_button'].set_text("Disconnect")
                            ui.notify(f"Connected to {device['name']} (driver not implemented)", type='info')
                        else:
                            # Disconnect (placeholder)
                            connection_state['connected'] = False
                            connection_state['status_label'].set_text("Disconnected")
                            connection_state['status_label'].style("color: #ef5350; font-weight: bold;")
                            connection_state['connect_button'].props("color=positive")
                            connection_state['connect_button'].set_text("Connect")
                            ui.notify(f"Disconnected from {device['name']}", type='info')

                    connection_state['connect_button'] = ui.button("Connect", icon="power", on_click=toggle_connection).props("color=positive")
                    connection_state['status_label'] = ui.label("Disconnected").style("color: #ef5350; font-size: 16px; font-weight: bold;")

            # Status display card
            with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                ui.label("Pump Status").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                status_labels = {}

                # Create status display grid
                with ui.grid(columns=2).style("gap: 15px; width: 100%;"):
                    status_items = [
                        ('Flow Rate:', 'flow', '-- µL/min'),
                        ('Volume Dispensed:', 'volume', '-- µL'),
                        ('Syringe Volume:', 'syringe', '-- mL'),
                        ('Status:', 'status', 'Idle')
                    ]

                    for label_text, key, default_value in status_items:
                        ui.label(label_text).style("color: #888888; font-size: 14px;")
                        status_labels[key] = ui.label(default_value).style("color: white; font-size: 16px; font-weight: bold;")

        # Right column - Pump Control
        with ui.column().style("flex: 1; gap: 20px;"):
            # Pump control card
            with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                ui.label("Pump Control").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                # Syringe size configuration
                with ui.row().style("gap: 10px; align-items: center; margin-bottom: 15px;"):
                    ui.label("Syringe Size:").style("color: white; font-size: 14px;")
                    syringe_select = ui.select(options=['1 mL', '5 mL', '10 mL', '20 mL', '50 mL'], value='10 mL').props("dark outlined").style("width: 150px;")

                    def set_syringe():
                        """Set syringe size (placeholder)"""
                        ui.notify(f"Syringe size set to {syringe_select.value} (driver not implemented)", type='info')

                    ui.button("Set Size", icon="settings", on_click=set_syringe).props("color=blue")

                # Flow rate control
                with ui.row().style("gap: 10px; align-items: center; margin-bottom: 15px;"):
                    ui.label("Flow Rate:").style("color: white; font-size: 14px;")
                    flow_input = ui.number(label="µL/min", value=100, min=0, max=10000, step=10).props("dark outlined").style("width: 150px;")

                    def set_flow():
                        """Set flow rate (placeholder)"""
                        ui.notify(f"Flow rate set to {flow_input.value} µL/min (driver not implemented)", type='info')

                    ui.button("Set Flow", icon="speed", on_click=set_flow).props("color=blue")

                # Volume to dispense
                with ui.row().style("gap: 10px; align-items: center; margin-bottom: 15px;"):
                    ui.label("Volume:").style("color: white; font-size: 14px;")
                    volume_input = ui.number(label="µL", value=1000, min=0, max=50000, step=100).props("dark outlined").style("width: 150px;")

                # Start/Stop buttons
                with ui.row().style("gap: 10px;"):
                    def start_pump():
                        """Start pump (placeholder)"""
                        ui.notify("Pump started (driver not implemented)", type='info')

                    def stop_pump():
                        """Stop pump (placeholder)"""
                        ui.notify("Pump stopped (driver not implemented)", type='info')

                    ui.button("START", icon="play_arrow", on_click=start_pump).props("size=lg color=positive")
                    ui.button("STOP", icon="stop", on_click=stop_pump).props("size=lg color=negative")

    # Webcam monitoring section
    render_device_webcam_section(device)


def render_device_webcam_section(device):
    """Render webcam monitoring section for a device"""
    # Import here to avoid circular imports
    from pages import devices as devices_page

    # Initialize webcams list if not exists
    if 'webcams' not in device:
        device['webcams'] = []

    with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-top: 20px;"):
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
            ui.label("Webcam Monitoring").style("color: white; font-size: 16px; font-weight: bold;")
            ui.button("Add Webcam", icon="videocam", on_click=lambda: show_add_device_webcam_dialog(device)).props("color=primary")

        if device['webcams']:
            # Display webcams
            for webcam in device['webcams']:
                with ui.card().style("background-color: #444444; padding: 15px; margin-bottom: 10px;"):
                    with ui.row().style("width: 100%; justify-content: space-between; align-items: center;"):
                        # Left: Webcam info
                        with ui.column().style("gap: 5px; flex: 1;"):
                            ui.label(webcam['name']).style("color: white; font-size: 16px; font-weight: bold;")
                            ui.label(f"Source: Device {webcam['url']}").style("color: #888888; font-size: 14px;")

                        # Right: Remove button
                        ui.button("Remove", icon="delete",
                                on_click=lambda w=webcam['name']: remove_device_webcam(device, w)).props("flat color=negative")

                    # Webcam feed display
                    with ui.column().style("width: 100%; align-items: center; margin-top: 10px;"):
                        # Check if this webcam is connected
                        key = (device['name'], webcam['name'])
                        is_connected = key in devices_page.active_device_webcam_captures

                        # Create image element for video display
                        if is_connected:
                            # Show live feed
                            webcam_image = ui.interactive_image().style("width: 100%; max-width: 640px; height: auto; border-radius: 8px;")
                            devices_page.register_device_webcam_image(device, webcam, webcam_image)
                        else:
                            # Show placeholder with centered text
                            with ui.card().style("width: 100%; max-width: 640px; height: 480px; background-color: #333333; border-radius: 8px; position: relative; display: flex; align-items: center; justify-content: center;"):
                                with ui.column().style("align-items: center; gap: 10px;"):
                                    ui.label("📹").style("color: #666666; font-size: 48px;")
                                    ui.label("Camera Disconnected").style("color: #888888; font-size: 16px;")

                        # Connection control buttons
                        with ui.row().style("gap: 10px; margin-top: 10px;"):
                            if is_connected:
                                def disconnect_handler(d=device, w=webcam):
                                    devices_page.disconnect_device_webcam(d, w)
                                    devices_page.refresh_device_list()
                                ui.button("Disconnect", icon="videocam_off", on_click=disconnect_handler).props("color=negative")
                            else:
                                def connect_handler(d=device, w=webcam):
                                    if devices_page.connect_device_webcam(d, w):
                                        devices_page.refresh_device_list()
                                ui.button("Connect", icon="videocam", on_click=connect_handler).props("color=primary")
        else:
            ui.label("No webcams configured. Click 'Add Webcam' to add a camera feed.").style("color: #888888; font-size: 14px;")


def show_add_device_webcam_dialog(device):
    """Show dialog to add a webcam to a device"""
    from pages import devices as devices_page
    import asyncio

    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Add Webcam").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        webcam_data = {'name': '', 'url': ''}

        # Webcam name input
        ui.label("Webcam Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(placeholder="e.g., Front View, Top View").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            webcam_data['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Webcam Device ID dropdown (USB connection)
        ui.label("Select USB Camera:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")

        # Create placeholder for status and dropdown
        status_label = ui.label("Detecting cameras...").style("color: #888888; font-size: 14px; margin-bottom: 10px;")

        # Create camera dropdown (will be populated after detection)
        camera_select = ui.select([], value=None).style("width: 100%;").props("dark outlined disabled")

        def on_camera_change(e):
            if e.value and e.value != "No cameras detected":
                # Extract device ID from selection (e.g., "Camera 0 (Device 0)" -> "0")
                device_id = e.value.split("Device ")[1].rstrip(")")
                webcam_data['url'] = device_id

        camera_select.on_value_change(on_camera_change)

        # Detect cameras asynchronously after dialog opens
        async def detect_cameras():
            try:
                # Run detection in background
                available_cameras = await asyncio.get_event_loop().run_in_executor(None, devices_page.get_available_cameras)

                # Update UI with results
                if available_cameras:
                    camera_options = [f"{cam['name']} (Device {cam['id']})" for cam in available_cameras]
                    status_label.set_text(f"Found {len(available_cameras)} camera(s)")
                    status_label.style("color: #66bb6a; font-size: 14px; margin-bottom: 10px;")
                else:
                    camera_options = ["No cameras detected"]
                    status_label.set_text("No cameras found")
                    status_label.style("color: #ef5350; font-size: 14px; margin-bottom: 10px;")

                # Update dropdown
                camera_select.options = camera_options
                camera_select.props(remove="disabled")
                camera_select.update()
            except Exception as e:
                status_label.set_text(f"Error detecting cameras: {str(e)}")
                status_label.style("color: #ef5350; font-size: 14px; margin-bottom: 10px;")
                camera_select.options = ["Error - try again"]
                camera_select.update()

        # Start detection
        ui.timer(0.1, lambda: asyncio.create_task(detect_cameras()), once=True)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def add_webcam():
                # Validate inputs
                if not webcam_data['name']:
                    ui.notify("Please enter a webcam name", type='warning')
                    return

                if not webcam_data['url']:
                    ui.notify("Please select a camera", type='warning')
                    return

                # Check for duplicate names
                if any(w['name'] == webcam_data['name'] for w in device['webcams']):
                    ui.notify(f"A webcam named '{webcam_data['name']}' already exists for this device", type='negative')
                    return

                # Add webcam to device
                device['webcams'].append({
                    'name': webcam_data['name'],
                    'url': webcam_data['url']
                })

                ui.notify(f"Added webcam: {webcam_data['name']}", type='positive')
                dialog.close()
                devices_page.refresh_device_list()

            ui.button("Add Webcam", on_click=add_webcam, icon="videocam").props("color=primary")

    dialog.open()


def remove_device_webcam(device, webcam_name):
    """Remove a webcam from a device"""
    from pages import devices as devices_page

    if 'webcams' in device:
        # Find the webcam to disconnect
        webcam_to_remove = None
        for cam in device['webcams']:
            if cam['name'] == webcam_name:
                webcam_to_remove = cam
                break

        # Disconnect if connected
        if webcam_to_remove:
            key = (device['name'], webcam_name)
            if key in devices_page.active_device_webcam_captures:
                devices_page.disconnect_device_webcam(device, webcam_to_remove)

        # Remove from list
        device['webcams'] = [cam for cam in device['webcams'] if cam['name'] != webcam_name]

        ui.notify(f"Removed webcam: {webcam_name}", type='positive')
        devices_page.refresh_device_list()
