# roboschlenk/config.py
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'roboschlenk_config.json')

def get_config():
    """Load RoboSchlenk configuration"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'motor_controller_port': None,
        'display_ports': {
            'A': None,
            'B': None,
            'C': None,
            'D': None
        },
        'configured': False
    }

def save_config(config):
    """Save RoboSchlenk configuration"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def is_configured():
    """Check if RoboSchlenk is configured"""
    config = get_config()
    return config.get('configured', False) and config.get('motor_controller_port') is not None
