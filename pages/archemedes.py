# pages/archemedes.py
from nicegui import ui

def render():
    """Render the ARCHEMedes page content"""
    with ui.column().style("padding: 20px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Page header
        ui.label("ARCHEMedes").style("color: white; font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        ui.label("AI-powered chemistry assistant").style("color: #888888; font-size: 14px; margin-bottom: 20px;")

        # Placeholder content
        with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
            ui.label("Coming Soon").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
            ui.label("ARCHEMedes features will be available here.").style("color: #888888; font-size: 14px;")
