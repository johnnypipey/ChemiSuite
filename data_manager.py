# data_manager.py
"""
Data persistence manager for ChemiSuite
Handles saving and loading of complete system configuration
"""

import json
import os
from typing import Dict, List, Any

# Data directory
DATA_DIR = "data"
CONFIGS_DIR = os.path.join(DATA_DIR, "configs")

def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")
    if not os.path.exists(CONFIGS_DIR):
        os.makedirs(CONFIGS_DIR)
        print(f"Created configs directory: {CONFIGS_DIR}")

def save_config(config_name: str, devices: List[Dict[str, Any]], fume_hoods: List[Dict[str, Any]]) -> bool:
    """
    Save complete system configuration to a named JSON file

    Args:
        config_name: Name for this configuration
        devices: List of device dictionaries
        fume_hoods: List of fume hood dictionaries

    Returns:
        True if save was successful, False otherwise
    """
    try:
        ensure_data_directory()

        # Sanitize config name for filename
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            print("Invalid configuration name")
            return False

        config_file = os.path.join(CONFIGS_DIR, f"{safe_name}.json")

        # Create a clean copy of devices without driver instances and connection state
        devices_to_save = []
        for device in devices:
            device_copy = {
                'name': device['name'],
                'type': device['type'],
                'com_port': device.get('com_port', ''),
                'show_on_dashboard': device.get('show_on_dashboard', False),
                'icon': device.get('icon', '')
            }
            devices_to_save.append(device_copy)

        # Create a clean copy of fume hoods without runtime data
        fume_hoods_to_save = []
        for fume_hood in fume_hoods:
            fume_hood_copy = {
                'name': fume_hood['name'],
                'description': fume_hood.get('description', ''),
                'assigned_person': fume_hood.get('assigned_person', ''),
                'contact_number': fume_hood.get('contact_number', ''),
                'sash_open': fume_hood.get('sash_open', False),
                'alarm_active': fume_hood.get('alarm_active', False),
                'webcams': fume_hood.get('webcams', []),
                'dashboard_webcam': fume_hood.get('dashboard_webcam', None),
            }

            # Save assigned device names (not the full device objects)
            if 'assigned_devices' in fume_hood:
                assigned_device_names = [d['name'] for d in fume_hood['assigned_devices']]
                fume_hood_copy['assigned_device_names'] = assigned_device_names

            fume_hoods_to_save.append(fume_hood_copy)

        # Save both to a single configuration file
        config = {
            'config_name': config_name,
            'devices': devices_to_save,
            'fume_hoods': fume_hoods_to_save
        }

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"Saved configuration '{config_name}': {len(devices_to_save)} devices, {len(fume_hoods_to_save)} fume hoods to {config_file}")
        return True

    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def load_config(config_name: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load complete system configuration from a named JSON file

    Args:
        config_name: Name of the configuration to load

    Returns:
        Tuple of (devices_list, fume_hoods_list), or ([], []) if file doesn't exist
    """
    try:
        # Sanitize config name for filename
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            print("Invalid configuration name")
            return [], []

        config_file = os.path.join(CONFIGS_DIR, f"{safe_name}.json")

        if not os.path.exists(config_file):
            print(f"No configuration file found at {config_file}")
            return [], []

        with open(config_file, 'r') as f:
            config = json.load(f)

        devices = config.get('devices', [])
        fume_hoods = config.get('fume_hoods', [])

        print(f"Loaded configuration '{config_name}': {len(devices)} devices, {len(fume_hoods)} fume hoods from {config_file}")
        return devices, fume_hoods

    except Exception as e:
        print(f"Error loading configuration: {e}")
        return [], []

def get_saved_configs() -> List[str]:
    """
    Get list of all saved configuration names

    Returns:
        List of configuration names (without .json extension)
    """
    try:
        ensure_data_directory()

        if not os.path.exists(CONFIGS_DIR):
            return []

        config_files = [f for f in os.listdir(CONFIGS_DIR) if f.endswith('.json')]
        config_names = [os.path.splitext(f)[0] for f in config_files]

        return sorted(config_names)

    except Exception as e:
        print(f"Error getting saved configs: {e}")
        return []

def delete_config(config_name: str) -> bool:
    """
    Delete a saved configuration

    Args:
        config_name: Name of the configuration to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        # Sanitize config name for filename
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            print("Invalid configuration name")
            return False

        config_file = os.path.join(CONFIGS_DIR, f"{safe_name}.json")

        if not os.path.exists(config_file):
            print(f"Configuration '{config_name}' not found")
            return False

        os.remove(config_file)
        print(f"Deleted configuration '{config_name}'")
        return True

    except Exception as e:
        print(f"Error deleting configuration: {e}")
        return False
