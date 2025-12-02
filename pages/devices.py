# pages/devices.py
from nicegui import ui
import devices as device_modules
import serial.tools.list_ports

# Store devices (in a real app, this would be in a database or state management)
devices = []

# Container reference for re-rendering
device_container = None

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
                }
                # Add any additional fields from selected_device (e.g., com_port)
                for key, value in selected_device.items():
                    if key not in ['type', 'name', 'module']:
                        device_data[key] = value

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

def remove_device(device_name):
    """Remove a device by name"""
    global devices

    # Find the device
    device_to_remove = None
    for d in devices:
        if d['name'] == device_name:
            device_to_remove = d
            break

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
        # Use the device module's render function with remove callback
        device_module.render_control_panel(device, on_remove=lambda: remove_device(device['name']))
    else:
        # Fallback if device module not found
        with ui.column().style("padding: 20px;"):
            ui.label(f"Unknown device type: {device['type']}").style("color: #ff0000; font-size: 16px;")
