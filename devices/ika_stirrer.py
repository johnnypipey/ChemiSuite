# devices/ika_stirrer.py
from nicegui import ui
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'drivers'))
from IKA_Hotplate_driver import IKAHotplateDriver

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

def render_control_panel(device, on_remove=None):
    """
    Render the control panel for this device

    Args:
        device: Dictionary containing device configuration (name, type, com_port, etc.)
        on_remove: Optional callback function to call when remove button is clicked
    """
    # Initialize driver only if it doesn't exist (persist across tab switches)
    if 'driver' not in device or device['driver'] is None:
        driver = IKAHotplateDriver(device.get('com_port', 'COM1'))
        device['driver'] = driver
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

            # Right: Remove button
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
