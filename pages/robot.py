# pages/robot.py
from nicegui import ui

def render():
    """Render the robot page content"""
    with ui.column().style("padding: 20px; width: 100%;"):
        ui.label("Robot Control").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        ui.label("No robot connected").style("color: #888888; font-size: 16px;")
