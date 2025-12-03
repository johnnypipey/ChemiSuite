# devices/edwards_tic.py
from nicegui import ui
import os
# Import the webcam rendering function from ika_stirrer (shared utility)
from .ika_stirrer import render_device_webcam_section

def get_device_info():
    """Return basic device information"""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'pressure-gauge.png')
    image_path = os.path.join(os.path.dirname(__file__), 'images', 'tic_gauge.png')
    return {
        'display_name': 'Edwards TIC Pressure Gauge',
        'type': 'edwards_tic',
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
    with ui.column().style("width: 100%; gap: 0;"):
        # Sticky header with device name, COM port, and remove button
        with ui.row().style("position: sticky; top: 0; z-index: 10; width: 100%; justify-content: space-between; align-items: center; padding: 20px; background-color: #222222; border-bottom: 1px solid #444444;"):
            # Left: Device info
            with ui.row().style("gap: 15px; align-items: baseline;"):
                ui.label(f"{device['name']} Controls").style("color: white; font-size: 18px; font-weight: bold;")
                ui.label(f"COM Port: {device.get('com_port', 'N/A')}").style("color: #888888; font-size: 14px;")

            # Right: Remove button
            if on_remove:
                ui.button("Remove Device", icon="delete", on_click=on_remove).props("flat color=negative")

        # Content area (will scroll with outer container)
        with ui.column().style("padding: 20px; gap: 20px;"):
            # Row with device image and current pressure reading
            with ui.row().style("width: 100%; gap: 20px; align-items: center; margin-bottom: 20px;"):
                # Device image
                image_path = os.path.join(os.path.dirname(__file__), 'images', 'tic_gauge.png')
                ui.image(image_path).style("width: 300px; height: auto; border-radius: 8px;")

                # Column with current pressure reading
                with ui.column().style("gap: 20px;"):
                    # Current Pressure Indicator
                    with ui.card().style("background-color: #333333; padding: 15px; min-width: 200px;"):
                        ui.label("Current Pressure").style("color: white; font-size: 12px; font-weight: bold; margin-bottom: 5px;")
                        with ui.row().style("align-items: baseline; gap: 5px;"):
                            ui.label("1.0e-3").style("color: #66bb6a; font-size: 36px; font-weight: bold;")
                            ui.label("mbar").style("color: #66bb6a; font-size: 18px;")

            # Webcam Monitoring Section
            render_device_webcam_section(device)
