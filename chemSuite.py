from splashscreen import show_splash
from nicegui import app, ui, Client
from page_manager import PageManager


app.native.window_args['resizable'] = False
app.native.window_args['easy_drag'] = False
app.native.start_args["debug"] = False

if __name__ == "__main__":
    show_splash()

if __name__ in {"__main__", "__mp_main__"}:


    @ui.page("/")
    def main():
        ui.query("body").style("background-color: #222222; margin: 0; padding: 0; overflow: hidden;")
        ui.query(".q-page").style("padding: 0; margin: 0;")
        ui.query(".nicegui-content").style("padding: 0; margin: 0;")

        # Add hover effect for close button and disable uppercase text transform
        ui.add_head_html("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;700&display=swap');

            .close-button:hover {
                color: #ff0000 !important;
            }
            .q-btn {
                text-transform: none !important;
            }
            .sidebar-btn .q-btn__content {
                color: #cccccc !important;
            }
            .sidebar-btn-active {
                background-color: #444444 !important;
            }
            .sidebar-btn-active .q-btn__content {
                color: white !important;
            }
            .app-title {
                font-family: 'Instrument Sans', sans-serif;
                font-weight: 700;
            }
            /* Active tab styling */
            .q-tab--active {
                background-color: #444444 !important;
            }
            .q-tab--active .q-tab__label {
                color: white !important;
            }
            /* Move notifications up to avoid taskbar */
            .q-notifications__list--bottom {
                bottom: 60px !important;
            }
            /* Disable uppercase transform for device tabs */
            .q-tab__label {
                text-transform: none !important;
            }
            /* Custom scrollbar styling for dark theme */
            ::-webkit-scrollbar {
                width: 12px;
            }
            ::-webkit-scrollbar-track {
                background: #333333;
            }
            ::-webkit-scrollbar-thumb {
                background: #555555;
                border-radius: 6px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #666666;
            }
        </style>
        """)

        # Main container - use column layout
        with ui.column().classes("w-full").style("margin: 0; padding: 0; height: 100vh; gap: 0;"):
            # Custom title bar
            with ui.row().classes("w-full").style("background-color: #333333; height: 30px; margin: 0; padding: 0 5px; align-items: center; justify-content: space-between; gap: 0;"):
                # Left side (empty for now, could add app icon/title later)
                ui.label("")

                # Right side - window control buttons
                with ui.row().style("gap: 2px; align-items: center; margin: 0;"):
                    def close_app():
                        app.shutdown()

                    ui.button(icon="minimize", on_click=lambda: app.native.main_window.minimize()).props("flat dense color=white").style("min-width: 30px; width: 30px; height: 30px; font-size: 12px;")
                    ui.button(icon="fullscreen", on_click=lambda: app.native.main_window.toggle_fullscreen()).props("flat dense color=white").style("min-width: 30px; width: 30px; height: 30px; font-size: 12px;")
                    ui.button(icon="close", on_click=close_app).props("flat dense color=white").classes("close-button").style("min-width: 30px; width: 30px; height: 30px; font-size: 12px;")

            # Main layout with sidebar and content
            with ui.row().classes("w-full").style("margin: 0; padding: 0; flex-grow: 1; gap: 0;"):
                # Dictionary to store button references
                nav_buttons = {}

                # Left sidebar menu
                with ui.column().style("width: 300px; background-color: #333333; height: calc(100vh - 30px); padding: 20px; margin: 0; justify-content: space-between;"):
                    # Top section with menu items
                    with ui.column().style("width: 100%;"):
                        # Section 1: Dashboard
                        ui.label("Dashboard").style("color: white; font-size: 14px; font-weight: bold; margin-bottom: 10px; margin-top: 0;")
                        nav_buttons['home'] = ui.button("Home", icon="home").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['status'] = ui.button("Status", icon="analytics").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 20px; font-weight: normal;")

                        # Section 2: Laboratory
                        ui.label("Laboratory").style("color: white; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
                        nav_buttons['devices'] = ui.button("Devices", icon="devices").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['experiment'] = ui.button("Experiment", icon="science").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['robot'] = ui.button("Robot", icon="smart_toy").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['fume_hood'] = ui.button("Fume Hood", icon="air").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['bench'] = ui.button("Bench", icon="table_restaurant").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 20px; font-weight: normal;")

                        # Section 3: Configuration
                        ui.label("Configuration").style("color: white; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
                        nav_buttons['settings'] = ui.button("Settings", icon="settings").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['about'] = ui.button("About", icon="info").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; margin-bottom: 5px; font-weight: normal;")
                        nav_buttons['log'] = ui.button("Log", icon="description").props("flat align=left").classes("w-full sidebar-btn").style("justify-content: flex-start; font-weight: normal;")

                    # Bottom section with app title
                    with ui.column().style("width: 100%; display: flex; justify-content: flex-end; align-items: center; flex-grow: 1; padding-bottom: 20px;"):
                        ui.label("ChemiSuite").classes("app-title").style("color: white; font-size: 32px; text-align: center; width: 100%;")

                # Main content area
                with ui.column().style("flex: 1; background-color: #222222;") as content_area:
                    pass

        # Create page manager with button references
        page_mgr = PageManager(content_area, nav_buttons)

        # Set up button click handlers
        nav_buttons['home'].on_click(lambda: page_mgr.show_home())
        nav_buttons['status'].on_click(lambda: page_mgr.show_status())
        nav_buttons['devices'].on_click(lambda: page_mgr.show_devices())
        nav_buttons['experiment'].on_click(lambda: page_mgr.show_experiment())
        nav_buttons['robot'].on_click(lambda: page_mgr.show_robot())
        nav_buttons['fume_hood'].on_click(lambda: page_mgr.show_fume_hood())
        nav_buttons['bench'].on_click(lambda: page_mgr.show_bench())
        nav_buttons['settings'].on_click(lambda: page_mgr.show_settings())
        nav_buttons['about'].on_click(lambda: page_mgr.show_about())
        nav_buttons['log'].on_click(lambda: page_mgr.show_log())

        # Show home page by default - use timer to ensure UI is ready
        ui.timer(0.1, lambda: page_mgr.show_home(), once=True)

    def on_startup():
        app.native.main_window.move(0, 0)
        # Close splash screen after NiceGUI window is ready
        import splashscreen
        if hasattr(splashscreen, 'close_splash'):
            splashscreen.close_splash()

    def on_shutdown():
        """Cleanup resources when app closes"""
        # Cleanup all webcam connections (fume hoods)
        from pages import fume_hood
        fume_hood.cleanup_all_webcams()

        # Cleanup all Arduino connections (fume hoods)
        fume_hood.cleanup_all_arduino_connections()

        # Cleanup all bench webcam connections
        from pages import bench
        bench.cleanup_all_webcams()

        # Cleanup all device webcam connections
        from pages import devices as devices_page
        devices_page.cleanup_all_device_webcams()

        # Cleanup device connections
        for device in devices_page.devices:
            if 'driver' in device and device['driver'] is not None:
                driver = device['driver']
                if hasattr(driver, 'connected') and driver.connected:
                    try:
                        # Stop all operations for safety
                        if hasattr(driver, 'set_temperature'):
                            driver.set_temperature(0, sensor_type=2)
                            driver.stop_heating(sensor_type=2)
                        if hasattr(driver, 'set_speed'):
                            driver.set_speed(0)
                            driver.stop_stirring()
                        # Disconnect
                        driver.disconnect()
                        print(f"Disconnected device: {device['name']}")
                    except Exception as e:
                        print(f"Error during device cleanup: {e}")

    app.on_startup(on_startup)
    app.on_shutdown(on_shutdown)
    ui.run(native=True, window_size=(1920, 1080), frameless=True)