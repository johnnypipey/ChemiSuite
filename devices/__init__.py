# devices/__init__.py
"""
Device management package for ChemiSuite

Each device module should provide:
- get_device_info(): Returns dict with 'display_name', 'type', and 'icon'
- show_wizard_fields(selected_device, com_ports): Shows device-specific wizard fields
- validate_wizard_fields(selected_device): Validates the wizard fields
- render_control_panel(device): Renders the device control panel
"""

from . import ika_stirrer
from . import edwards_tic
from . import azura_pump
from . import wpi_syringe_pump

# Registry of all available devices
AVAILABLE_DEVICES = [
    ika_stirrer,
    edwards_tic,
    azura_pump,
    wpi_syringe_pump,
]

def get_all_devices():
    """Get list of all available device modules"""
    return AVAILABLE_DEVICES

def get_device_module(device_type):
    """
    Get device module by device type

    Args:
        device_type: String identifier for the device type (e.g., 'ika_stirrer')

    Returns:
        Device module or None if not found
    """
    for device_module in AVAILABLE_DEVICES:
        if device_module.get_device_info()['type'] == device_type:
            return device_module
    return None
