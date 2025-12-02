# pages/settings.py
from nicegui import ui

def render():
    """Render the settings page content"""
    with ui.column().style("padding: 20px; width: 100%;"):
        ui.label("Application Settings").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        ui.label("Configure your preferences here").style("color: #888888; font-size: 16px;")
