# pages/experiment.py
from nicegui import ui

def render():
    """Render the experiment page content"""
    with ui.column().style("padding: 20px; width: 100%;"):
        ui.label("No experiments running").style("color: #888888; font-size: 16px; margin-bottom: 20px;")
        ui.button("New Experiment", icon="add").props("color=primary")
