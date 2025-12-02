# pages/status.py
from nicegui import ui

def render():
    """Render the status page content"""
    with ui.column().style("padding: 20px; width: 100%;"):
        ui.label("System Status").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        ui.label("All systems operational").style("color: #888888; font-size: 16px;")
