# devices/ika_stirrer.py
from nicegui import ui
import os
import sys
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'drivers'))
from IKA_Hotplate_driver import IKAHotplateDriver

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

def get_device_info():
    """Return basic device information"""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'hotplate.png')
    image_path = os.path.join(os.path.dirname(__file__), 'images', 'IKA_hotplate.png')
    return {
        'display_name': 'IKA Stirrer Hotplate',
        'type': 'ika_stirrer',
        'icon': icon_path,
        'image': image_path
    }

def get_loggable_parameters():
    """Return parameters that can be logged for this device"""
    return {
        'temperature': {
            'method': 'get_temperature',
            'unit': '°C',
            'args': {'sensor_type': 2},
            'display_name': 'Temperature'
        },
        'speed': {
            'method': 'get_speed',
            'unit': 'RPM',
            'args': {},
            'display_name': 'Stirring Speed'
        }
    }

def show_wizard_fields(selected_device, com_ports):
    """
    Show device-specific wizard fields (COM port selection, etc.)

    Args:
        selected_device: Dictionary to store selected device configuration
        com_ports: List of available COM ports (formatted as "COMx - Description")

    Returns:
        List of UI elements that were created (for reference if needed)
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

    # Dashboard display option
    dashboard_container = ui.column().style("width: 100%; margin-top: 20px;")
    with dashboard_container:
        ui.label("Dashboard Settings:").style("color: white; font-size: 16px; margin-bottom: 10px;")

        def on_dashboard_change(e):
            selected_device.update({'show_on_dashboard': e.value})

        dashboard_checkbox = ui.checkbox("Show on Dashboard").style("color: white;")
        dashboard_checkbox.on_value_change(on_dashboard_change)
        dashboard_checkbox.value = True  # Default to showing on dashboard
        selected_device.update({'show_on_dashboard': True})

    elements.append(dashboard_container)
    return elements

def validate_wizard_fields(selected_device):
    """
    Validate device-specific wizard fields

    Args:
        selected_device: Dictionary containing selected device configuration

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not selected_device.get('com_port'):
        return False, "Please select a COM port"

    return True, ""

def render_control_panel(device, on_edit=None, on_remove=None):
    """
    Render the control panel for this device

    Args:
        device: Dictionary containing device configuration (name, type, com_port, etc.)
        on_edit: Optional callback function to call when edit button is clicked
        on_remove: Optional callback function to call when remove button is clicked
    """
    # Initialize driver only if it doesn't exist OR if COM port has changed (persist across tab switches)
    if 'driver' not in device or device['driver'] is None:
        driver = IKAHotplateDriver(device.get('com_port', 'COM1'))
        device['driver'] = driver
        device['driver_com_port'] = device.get('com_port', 'COM1')
    else:
        # Check if COM port has changed
        if device.get('com_port') != device.get('driver_com_port'):
            # COM port changed, recreate driver
            driver = IKAHotplateDriver(device.get('com_port', 'COM1'))
            device['driver'] = driver
            device['driver_com_port'] = device.get('com_port', 'COM1')
            # Reset connection state since we have a new driver
            if 'connection_state' in device:
                device['connection_state']['connected'] = False
        else:
            driver = device['driver']

    # Connection state - persist across tab switches
    if 'connection_state' not in device:
        device['connection_state'] = {'connected': False, 'heating': False, 'stirring': False}
    connection_state = device['connection_state']

    with ui.column().style("width: 100%; gap: 0;"):
        # Sticky header with device name, COM port, and remove button
        with ui.row().style("position: sticky; top: 0; z-index: 10; width: 100%; justify-content: space-between; align-items: center; padding: 20px; background-color: #222222; border-bottom: 1px solid #444444;"):
            # Left: Device info
            with ui.row().style("gap: 15px; align-items: baseline;"):
                ui.label(f"{device['name']} Controls").style("color: white; font-size: 18px; font-weight: bold;")
                ui.label(f"COM Port: {device.get('com_port', 'N/A')}").style("color: #888888; font-size: 14px;")
                # Set badge based on current connection state
                badge_text = "Connected" if connection_state['connected'] else "Disconnected"
                badge_color = "green" if connection_state['connected'] else "red"
                connection_badge = ui.badge(badge_text, color=badge_color).style("margin-left: 10px;")

            # Right: Edit and Remove buttons
            with ui.row().style("gap: 10px;"):
                if on_edit:
                    ui.button("Edit", icon="edit", on_click=on_edit).props("flat color=white")
                if on_remove:
                    ui.button("Remove Device", icon="delete", on_click=on_remove).props("flat color=negative")

        # Content area (will scroll with outer container)
        with ui.column().style("padding: 20px; gap: 20px;"):
            # Connection control
            with ui.card().style("background-color: #333333; padding: 15px; width: 100%;"):
                with ui.row().style("gap: 10px; align-items: center;"):
                    def toggle_connection():
                        if connection_state['connected']:
                            # Safety: Stop heating and stirring before disconnecting
                            try:
                                driver.set_temperature(0, sensor_type=2)
                                driver.stop_heating(sensor_type=2)
                                driver.set_speed(0)
                                driver.stop_stirring()
                                connection_state['heating'] = False
                                connection_state['stirring'] = False
                            except Exception as e:
                                print(f"Error stopping device during disconnect: {e}")

                            # Disconnect
                            driver.disconnect()
                            connection_state['connected'] = False
                            connection_badge.set_text("Disconnected")
                            connection_badge.props(f"color=red")
                            connect_btn.set_text("Connect")
                            connect_btn.props("color=primary icon=power_settings_new")
                            ui.notify("Device stopped and disconnected", type='info')
                        else:
                            # Connect
                            success, message = driver.connect()
                            if success:
                                connection_state['connected'] = True
                                connection_badge.set_text("Connected")
                                connection_badge.props(f"color=green")
                                connect_btn.set_text("Disconnect")
                                connect_btn.props("color=negative icon=power_off")
                                ui.notify(message, type='positive')
                                # Start update timer
                                update_readings()
                            else:
                                ui.notify(message, type='negative')

                    # Set button text and icon based on current connection state
                    btn_text = "Disconnect" if connection_state['connected'] else "Connect"
                    btn_icon = "power_off" if connection_state['connected'] else "power_settings_new"
                    btn_color = "negative" if connection_state['connected'] else "primary"
                    connect_btn = ui.button(btn_text, icon=btn_icon, on_click=toggle_connection).props(f"color={btn_color}")
                    ui.label("Connect to device to begin control").style("color: #888888; font-size: 14px;")

            # Row with image and indicators
            with ui.row().style("width: 100%; gap: 20px; align-items: center; margin-bottom: 20px;"):
                # Device image
                image_path = os.path.join(os.path.dirname(__file__), 'images', 'IKA_hotplate.png')
                ui.image(image_path).style("width: 300px; height: auto; border-radius: 8px;")

                # Column with current readings indicators
                with ui.column().style("gap: 20px;"):
                    # Current Temperature Indicator with Stop button
                    with ui.card().style("background-color: #333333; padding: 15px; min-width: 350px; width: 350px;"):
                        ui.label("Current Temp").style("color: white; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
                        with ui.row().style("align-items: center; gap: 10px; flex-wrap: nowrap;"):
                            with ui.row().style("align-items: baseline; gap: 3px;"):
                                temp_value_label = ui.label("--").style("color: #ef5350; font-size: 36px; font-weight: bold;")
                                ui.label("°C").style("color: #ef5350; font-size: 18px;")

                            def stop_heating():
                                if not connection_state['connected']:
                                    ui.notify("Please connect to device first", type='warning')
                                    return

                                driver.set_temperature(0, sensor_type=2)
                                driver.stop_heating(sensor_type=2)
                                connection_state['heating'] = False
                                ui.notify("Heating stopped", type='info')

                            ui.button("Stop Heating", icon="stop", on_click=stop_heating).props("flat color=red").style("font-weight: bold; font-size: 14px; white-space: nowrap;")

                    # Current Speed Indicator with Stop button
                    with ui.card().style("background-color: #333333; padding: 15px; min-width: 350px; width: 350px;"):
                        ui.label("Current Speed").style("color: white; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
                        with ui.row().style("align-items: center; gap: 10px; flex-wrap: nowrap;"):
                            with ui.row().style("align-items: baseline; gap: 3px;"):
                                speed_value_label = ui.label("--").style("color: #42a5f5; font-size: 36px; font-weight: bold;")
                                ui.label("RPM").style("color: #42a5f5; font-size: 18px;")

                            def stop_stirring():
                                if not connection_state['connected']:
                                    ui.notify("Please connect to device first", type='warning')
                                    return

                                driver.set_speed(0)
                                driver.stop_stirring()
                                connection_state['stirring'] = False
                                ui.notify("Stirring stopped", type='info')

                            ui.button("Stop Stirring", icon="stop", on_click=stop_stirring).props("flat color=blue").style("font-weight: bold; font-size: 14px; white-space: nowrap;")

            # Controls row that spans full width below image and indicators
            with ui.row().style("width: 100%; gap: 20px;"):
                # Temperature Control
                with ui.card().style("background-color: #333333; padding: 20px; flex: 1;"):
                    ui.label("Temperature Control").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
                    temp_slider = ui.slider(min=20, max=340, value=25, step=5).props("label-always color=red-6").style("width: 100%;")

                    def set_temperature():
                        if not connection_state['connected']:
                            ui.notify("Please connect to device first", type='warning')
                            return

                        # Set temperature
                        temp_value = temp_slider.value
                        temp_success = driver.set_temperature(temp_value, sensor_type=2)

                        # Only start heating if temp > minimum (25°C), otherwise stop
                        if temp_value > 25:
                            heat_success = driver.start_heating(sensor_type=2)
                            if temp_success and heat_success:
                                connection_state['heating'] = True
                                ui.notify(f"Setting temperature to {temp_value}°C", type='positive')
                            else:
                                ui.notify("Failed to set temperature", type='negative')
                        else:
                            # Stop heating when at minimum temperature
                            driver.stop_heating(sensor_type=2)
                            connection_state['heating'] = False
                            ui.notify("Heating stopped", type='info')

                    ui.button("Set Temp", icon="thermostat", on_click=set_temperature).props("color=red-6").style("margin-top: 15px; width: 100%;")

                # Stirrer Speed Control
                with ui.card().style("background-color: #333333; padding: 20px; flex: 1;"):
                    ui.label("Stirrer Speed").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
                    speed_slider = ui.slider(min=0, max=1700, value=0, step=50).props("label-always color=blue-6").style("width: 100%;")

                    def set_speed():
                        if not connection_state['connected']:
                            ui.notify("Please connect to device first", type='warning')
                            return

                        # Set speed
                        speed_value = int(speed_slider.value)
                        speed_success = driver.set_speed(speed_value)

                        # Only start stirring if speed > 0, otherwise stop
                        if speed_value > 0:
                            stir_success = driver.start_stirring()
                            if speed_success and stir_success:
                                connection_state['stirring'] = True
                                ui.notify(f"Setting stirrer speed to {speed_value} RPM", type='positive')
                            else:
                                ui.notify("Failed to set speed", type='negative')
                        else:
                            # Stop stirring when speed is 0
                            driver.stop_stirring()
                            connection_state['stirring'] = False
                            ui.notify("Stirring stopped", type='info')

                    ui.button("Set Speed", icon="speed", on_click=set_speed).props("color=blue-6").style("margin-top: 15px; width: 100%;")

            # Webcam Monitoring Section
            render_device_webcam_section(device)

    # Update function to read values from device
    def update_readings():
        if connection_state['connected']:
            try:
                temp = driver.get_temperature(sensor_type=2)
                speed = driver.get_speed()

                temp_value_label.set_text(f"{temp:.1f}" if temp > 0 else "--")
                speed_value_label.set_text(f"{speed:.0f}" if speed >= 0 else "--")
            except Exception as e:
                print(f"Error updating readings: {e}")

        # Schedule next update if still connected
        if connection_state['connected']:
            ui.timer(2.0, update_readings, once=True)

    # Start update timer if already connected (for when switching back to this tab)
    if connection_state['connected']:
        update_readings()
