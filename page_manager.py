# page_manager.py
from nicegui import ui
from pages import home, status, devices, experiment, robot, settings, about, log, fume_hood, bench, programming, data_logging, archemedes, roboschlenk

class PageManager:
    def __init__(self, content_area, nav_buttons):
        self.content_area = content_area
        self.nav_buttons = nav_buttons
        self.current_page = None

    def _update_nav_highlight(self, active_button_key):
        """Update navigation button highlighting"""
        # Remove active class from all buttons
        for key, button in self.nav_buttons.items():
            button.classes(remove='sidebar-btn-active')

        # Add active class to the current button
        if active_button_key in self.nav_buttons:
            self.nav_buttons[active_button_key].classes(add='sidebar-btn-active')

    def show_page(self, page_name, page_module, button_key):
        """Clear the content area and show a new page with title bar"""
        self.current_page = page_name
        self._update_nav_highlight(button_key)
        self.content_area.clear()

        # Must be inside content_area context to add elements
        with self.content_area:
            # Title bar
            with ui.row().classes("w-full").style("background-color: #333333; padding: 15px 20px; margin: 0; align-items: center;"):
                ui.label(page_name).style("color: white; font-size: 20px; font-weight: bold;")

            # Page content
            page_module.render()

    def show_home(self):
        self.show_page("Home", home, "home")

    def show_status(self):
        self.show_page("Status", status, "status")

    def show_devices(self):
        self.show_page("Devices", devices, "devices")

    def show_experiment(self):
        self.show_page("Laboratory Notebook", experiment, "experiment")

    def show_robot(self):
        self.show_page("Robot", robot, "robot")

    def show_settings(self):
        self.show_page("Settings", settings, "settings")

    def show_about(self):
        self.show_page("About", about, "about")

    def show_log(self):
        self.show_page("Log", log, "log")

    def show_fume_hood(self):
        self.show_page("Fume Hood", fume_hood, "fume_hood")

    def show_bench(self):
        self.show_page("Bench", bench, "bench")

    def show_programming(self):
        # Pass the badge element to programming module
        if 'programming_badge' in self.nav_buttons:
            programming.script_state['badge_element'] = self.nav_buttons['programming_badge']
        self.show_page("Programming", programming, "programming")

    def show_data_logging(self):
        self.show_page("Data Logging", data_logging, "data_logging")

    def show_archemedes(self):
        self.show_page("ARCHEMedes", archemedes, "archemedes")

    def show_roboschlenk(self):
        self.show_page("RoboSchlenk", roboschlenk, "roboschlenk")
