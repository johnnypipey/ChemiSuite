# pages/about.py
from nicegui import ui

def render():
    """Render the about page content"""
    with ui.column().style("padding: 20px; width: 100%;"):
        ui.label("ChemiSuite").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        ui.label("Version 0.01").style("color: #888888; font-size: 16px; margin-bottom: 5px;")
        ui.label("Laboratory automation and chemistry suite").style("color: #888888; font-size: 14px;")
