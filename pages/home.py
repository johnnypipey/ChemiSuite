# pages/home.py
from nicegui import ui
import sys
import os

# Import devices and fume_hood modules to access their lists
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pages import devices as devices_page
from pages import fume_hood as fume_hood_page
import data_manager

def render():
    """Render the home page content"""
    with ui.column().style("padding: 20px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Header row with title and save/load buttons
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 10px;"):
            ui.label("Dashboard").style("color: white; font-size: 24px; font-weight: bold;")

            # Save and Load buttons
            with ui.row().style("gap: 10px;"):
                def show_save_dialog():
                    """Show dialog to save configuration with a name"""
                    with ui.dialog() as save_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 400px;"):
                        ui.label("Save Configuration").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

                        ui.label("Configuration Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
                        config_name_input = ui.input(placeholder="Enter configuration name").style("width: 100%;").props("dark outlined")

                        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 20px;"):
                            ui.button("Cancel", on_click=save_dialog.close).props("flat color=white")

                            def save_config():
                                if not config_name_input.value:
                                    ui.notify("Please enter a configuration name", type='warning')
                                    return

                                success = data_manager.save_config(config_name_input.value, devices_page.devices, fume_hood_page.fume_hoods)
                                if success:
                                    ui.notify(f"Configuration '{config_name_input.value}' saved successfully", type='positive')
                                    save_dialog.close()
                                else:
                                    ui.notify("Failed to save configuration", type='negative')

                            ui.button("Save", icon="save", on_click=save_config).props("color=primary")

                    save_dialog.open()

                def show_load_dialog():
                    """Show dialog to select and load a configuration"""
                    # Get list of saved configurations
                    saved_configs = data_manager.get_saved_configs()

                    if not saved_configs:
                        ui.notify("No saved configurations found", type='warning')
                        return

                    with ui.dialog() as load_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 400px;"):
                        ui.label("Load Configuration").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

                        ui.label("Select Configuration:").style("color: white; font-size: 16px; margin-bottom: 10px;")
                        config_select = ui.select(saved_configs, value=saved_configs[0] if saved_configs else None).style("width: 100%;").props("dark outlined")

                        with ui.row().style("width: 100%; justify-content: space-between; gap: 10px; margin-top: 20px;"):
                            # Delete button on the left
                            def delete_config():
                                if not config_select.value:
                                    ui.notify("Please select a configuration", type='warning')
                                    return

                                # Confirm deletion
                                with ui.dialog() as confirm_dialog, ui.card().style("background-color: #333333; padding: 20px;"):
                                    ui.label(f"Delete '{config_select.value}'?").style("color: white; font-size: 16px; margin-bottom: 20px;")
                                    ui.label("This action cannot be undone.").style("color: #888888; font-size: 14px; margin-bottom: 20px;")

                                    with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px;"):
                                        ui.button("Cancel", on_click=confirm_dialog.close).props("flat color=white")

                                        def do_delete():
                                            success = data_manager.delete_config(config_select.value)
                                            if success:
                                                ui.notify(f"Deleted configuration '{config_select.value}'", type='positive')
                                                confirm_dialog.close()
                                                load_dialog.close()
                                                # Reopen load dialog with updated list
                                                show_load_dialog()
                                            else:
                                                ui.notify("Failed to delete configuration", type='negative')

                                        ui.button("Delete", icon="delete", on_click=do_delete).props("color=negative")

                                confirm_dialog.open()

                            ui.button("Delete", icon="delete", on_click=delete_config).props("flat color=negative")

                            # Load and Cancel buttons on the right
                            with ui.row().style("gap: 10px;"):
                                ui.button("Cancel", on_click=load_dialog.close).props("flat color=white")

                                def load_config():
                                    if not config_select.value:
                                        ui.notify("Please select a configuration", type='warning')
                                        return

                                    devices_data, fume_hoods_data = data_manager.load_config(config_select.value)

                                    if not devices_data and not fume_hoods_data:
                                        ui.notify("Configuration is empty or corrupted", type='warning')
                                        return

                                    # Clear existing data
                                    devices_page.devices.clear()
                                    fume_hood_page.fume_hoods.clear()

                                    # Load devices
                                    for device_data in devices_data:
                                        device = {
                                            'name': device_data['name'],
                                            'type': device_data['type'],
                                            'com_port': device_data.get('com_port', ''),
                                            'show_on_dashboard': device_data.get('show_on_dashboard', False),
                                            'icon': device_data.get('icon', '')
                                        }
                                        devices_page.devices.append(device)

                                    # Load fume hoods
                                    for fume_hood_data in fume_hoods_data:
                                        fume_hood = {
                                            'name': fume_hood_data['name'],
                                            'description': fume_hood_data.get('description', ''),
                                            'assigned_person': fume_hood_data.get('assigned_person', ''),
                                            'contact_number': fume_hood_data.get('contact_number', ''),
                                            'sash_open': fume_hood_data.get('sash_open', False),
                                            'alarm_active': fume_hood_data.get('alarm_active', False),
                                            'webcams': fume_hood_data.get('webcams', []),
                                            'dashboard_webcam': fume_hood_data.get('dashboard_webcam', None),
                                        }

                                        # Restore assigned devices by finding them by name
                                        if 'assigned_device_names' in fume_hood_data:
                                            assigned_devices = []
                                            for device_name in fume_hood_data['assigned_device_names']:
                                                # Find the device in the devices list
                                                for device in devices_page.devices:
                                                    if device['name'] == device_name:
                                                        assigned_devices.append(device)
                                                        break
                                            fume_hood['assigned_devices'] = assigned_devices

                                        fume_hood_page.fume_hoods.append(fume_hood)

                                    ui.notify(f"Loaded '{config_select.value}': {len(devices_data)} device(s), {len(fume_hoods_data)} fume hood(s)", type='positive')
                                    load_dialog.close()

                                    # Refresh the current page to show loaded data
                                    from nicegui import ui as ui_refresh
                                    ui_refresh.run_javascript('location.reload()')

                                ui.button("Load", icon="upload", on_click=load_config).props("color=primary")

                    load_dialog.open()

                ui.button("Save Configuration", icon="save", on_click=show_save_dialog).props("color=primary")
                ui.button("Load Configuration", icon="upload", on_click=show_load_dialog).props("color=secondary")

        # Get all fume hoods (they're always shown on dashboard)
        dashboard_fume_hoods = fume_hood_page.fume_hoods

        # Get all device names that are assigned to any fume hood
        assigned_device_names = set()
        for fume_hood in dashboard_fume_hoods:
            if fume_hood.get('assigned_devices'):
                for device in fume_hood['assigned_devices']:
                    assigned_device_names.add(device['name'])

        # Get devices that should be shown on dashboard AND are not assigned to any fume hood
        dashboard_devices = [d for d in devices_page.devices
                           if d.get('show_on_dashboard', False) and d['name'] not in assigned_device_names]

        if dashboard_devices or dashboard_fume_hoods:
            # Display devices and fume hoods in a grid
            with ui.grid(columns=2).style("gap: 20px; width: 100%;"):
                # Render devices
                for device in dashboard_devices:
                    render_device_card(device)

                # Render fume hoods - each spans 2 columns
                for fume_hood in dashboard_fume_hoods:
                    # Container that spans 2 columns
                    with ui.column().style("grid-column: span 2; width: 100%;"):
                        render_fume_hood_card(fume_hood)
        else:
            ui.label("No devices or fume hoods configured for dashboard display.").style("color: #888888; font-size: 16px; margin-top: 10px;")
            ui.label("Add devices from the Devices page or fume hoods from the Fume Hood page to see them here.").style("color: #888888; font-size: 14px; margin-top: 5px;")

def render_device_card(device):
    """Render a dashboard card for a device"""
    # Get device module to access image path
    import devices as device_modules
    device_module = device_modules.get_device_module(device['type'])
    device_info = device_module.get_device_info() if device_module else {}

    with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
        # Device header with name and status
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
            ui.label(device['name']).style("color: white; font-size: 18px; font-weight: bold;")

            # Connection status badge
            if 'connection_state' in device and device['connection_state'].get('connected', False):
                ui.badge("Connected", color="green")
            else:
                ui.badge("Disconnected", color="red")

        # Row with device image and info/data
        with ui.row().style("width: 100%; gap: 20px; align-items: flex-start;"):
            # Device image from images folder
            if device_info.get('image'):
                ui.image(device_info['image']).style("width: 150px; height: auto; border-radius: 8px;")

            # Column with device info and data
            with ui.column().style("flex: 1; gap: 15px;"):
                # Device type and COM port info
                ui.label(f"Type: {device.get('type', 'Unknown')}").style("color: #888888; font-size: 14px;")
                ui.label(f"COM Port: {device.get('com_port', 'N/A')}").style("color: #888888; font-size: 14px;")

                # Device-specific data display
                if device['type'] == 'ika_stirrer':
                    render_ika_stirrer_data(device)
                elif device['type'] == 'edwards_tic':
                    render_edwards_tic_data(device)

def render_ika_stirrer_data(device):
    """Render IKA Stirrer specific data"""
    with ui.row().style("width: 100%; gap: 20px;"):
        # Temperature display
        with ui.column().style("gap: 5px;"):
            ui.label("Temperature").style("color: white; font-size: 12px; font-weight: bold;")
            if 'driver' in device and device.get('connection_state', {}).get('connected', False):
                try:
                    temp = device['driver'].get_temperature(sensor_type=2)
                    temp_label = ui.label(f"{temp:.1f} °C").style("color: #ef5350; font-size: 24px; font-weight: bold;")
                except:
                    temp_label = ui.label("-- °C").style("color: #ef5350; font-size: 24px; font-weight: bold;")
            else:
                temp_label = ui.label("-- °C").style("color: #ef5350; font-size: 24px; font-weight: bold;")

        # Speed display
        with ui.column().style("gap: 5px;"):
            ui.label("Stirrer Speed").style("color: white; font-size: 12px; font-weight: bold;")
            if 'driver' in device and device.get('connection_state', {}).get('connected', False):
                try:
                    speed = device['driver'].get_speed()
                    speed_label = ui.label(f"{speed:.0f} RPM").style("color: #42a5f5; font-size: 24px; font-weight: bold;")
                except:
                    speed_label = ui.label("-- RPM").style("color: #42a5f5; font-size: 24px; font-weight: bold;")
            else:
                speed_label = ui.label("-- RPM").style("color: #42a5f5; font-size: 24px; font-weight: bold;")

    # Start periodic update for connected devices
    if 'driver' in device and device.get('connection_state', {}).get('connected', False):
        def update_standalone_device_data():
            if device.get('connection_state', {}).get('connected', False):
                try:
                    temp = device['driver'].get_temperature(sensor_type=2)
                    temp_label.set_text(f"{temp:.1f} °C")
                except:
                    temp_label.set_text("-- °C")
                try:
                    speed = device['driver'].get_speed()
                    speed_label.set_text(f"{speed:.0f} RPM")
                except:
                    speed_label.set_text("-- RPM")
                # Schedule next update
                ui.timer(2.0, update_standalone_device_data, once=True)

        # Start the update timer
        ui.timer(2.0, update_standalone_device_data, once=True)

def render_edwards_tic_data(device):
    """Render Edwards TIC specific data"""
    with ui.column().style("gap: 5px;"):
        ui.label("Pressure").style("color: white; font-size: 12px; font-weight: bold;")
        # Placeholder data - will need actual driver implementation
        ui.label("1.0e-3 mbar").style("color: #66bb6a; font-size: 24px; font-weight: bold;")

def render_fume_hood_card(fume_hood):
    """Render a dashboard card for a fume hood"""
    with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
        # Fume hood header with name
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
            ui.label(fume_hood['name']).style("color: white; font-size: 18px; font-weight: bold;")

            # Alarm status badge
            if fume_hood.get('alarm_active', False):
                ui.badge("ALARM", color="red")
            else:
                ui.badge("Normal", color="green")

        # 2-column layout for compact display
        with ui.row().style("width: 100%; gap: 20px; align-items: flex-start;"):
            # Left column - Fume hood status
            with ui.column().style("flex: 1; gap: 15px;"):
                # Row with icon and status data
                with ui.row().style("width: 100%; gap: 20px; align-items: flex-start;"):
                    # Fume hood icon/visual
                    with ui.column().style("align-items: center; justify-content: center; min-width: 100px;"):
                        # Large sash status icon
                        sash_icon = "↑" if fume_hood.get('sash_open', False) else "↓"
                        sash_color = "#ef5350" if fume_hood.get('sash_open', False) else "#66bb6a"
                        ui.label(sash_icon).style(f"color: {sash_color}; font-size: 48px; font-weight: bold;")

                    # Column with fume hood info and data
                    with ui.column().style("flex: 1; gap: 10px;"):
                        # Description if available
                        if fume_hood.get('description'):
                            ui.label(fume_hood['description']).style("color: #888888; font-size: 14px;")

                        # Sash status
                        with ui.row().style("gap: 20px;"):
                            with ui.column().style("gap: 5px;"):
                                ui.label("Sash Status").style("color: white; font-size: 12px; font-weight: bold;")
                                sash_status = "OPEN" if fume_hood.get('sash_open', False) else "CLOSED"
                                sash_badge_color = "red" if fume_hood.get('sash_open', False) else "green"
                                ui.badge(sash_status, color=sash_badge_color).style("font-size: 14px;")

                            with ui.column().style("gap: 5px;"):
                                ui.label("Safety Status").style("color: white; font-size: 12px; font-weight: bold;")
                                if fume_hood.get('sash_open', False):
                                    ui.label("⚠ In Use").style("color: #ef5350; font-size: 14px; font-weight: bold;")
                                else:
                                    ui.label("✓ Safe").style("color: #66bb6a; font-size: 14px; font-weight: bold;")

                # Assigned Devices section (in left column)
                if fume_hood.get('assigned_devices'):
                    with ui.column().style("width: 100%; margin-top: 15px; padding-top: 15px; border-top: 1px solid #444444; gap: 10px;"):
                        ui.label("Assigned Devices").style("color: white; font-size: 14px; font-weight: bold;")

                        # Display each assigned device
                        for device in fume_hood['assigned_devices']:
                            with ui.card().style("background-color: #444444; padding: 10px; width: 100%;"):
                                # Row with device image and info/data
                                with ui.row().style("width: 100%; gap: 15px; align-items: flex-start;"):
                                    # Device image from images folder
                                    import devices as device_modules
                                    device_module = device_modules.get_device_module(device['type'])
                                    device_info = device_module.get_device_info() if device_module else {}

                                    if device_info.get('image'):
                                        ui.image(device_info['image']).style("width: 80px; height: auto; border-radius: 8px;")

                                    # Column with device info and data
                                    with ui.column().style("flex: 1; gap: 5px;"):
                                        # Device name
                                        ui.label(device['name']).style("color: white; font-size: 14px; font-weight: bold;")
                                        ui.label(f"Type: {device.get('type', 'Unknown')}").style("color: #888888; font-size: 12px;")

                                        # Device-specific data display (compact)
                                        if device['type'] == 'ika_stirrer':
                                            with ui.row().style("gap: 15px;"):
                                                if 'driver' in device and device.get('connection_state', {}).get('connected', False):
                                                    # Create updateable labels
                                                    try:
                                                        temp = device['driver'].get_temperature(sensor_type=2)
                                                        temp_label = ui.label(f"🌡 {temp:.1f}°C").style("color: #ef5350; font-size: 12px; font-weight: bold;")
                                                    except:
                                                        temp_label = ui.label("🌡 --°C").style("color: #ef5350; font-size: 12px;")
                                                    try:
                                                        speed = device['driver'].get_speed()
                                                        speed_label = ui.label(f"⚙ {speed:.0f} RPM").style("color: #42a5f5; font-size: 12px; font-weight: bold;")
                                                    except:
                                                        speed_label = ui.label("⚙ -- RPM").style("color: #42a5f5; font-size: 12px;")

                                                    # Start periodic update for this device
                                                    def update_dashboard_device_data():
                                                        if device.get('connection_state', {}).get('connected', False):
                                                            try:
                                                                temp = device['driver'].get_temperature(sensor_type=2)
                                                                temp_label.set_text(f"🌡 {temp:.1f}°C")
                                                            except:
                                                                temp_label.set_text("🌡 --°C")
                                                            try:
                                                                speed = device['driver'].get_speed()
                                                                speed_label.set_text(f"⚙ {speed:.0f} RPM")
                                                            except:
                                                                speed_label.set_text("⚙ -- RPM")
                                                            # Schedule next update
                                                            ui.timer(2.0, update_dashboard_device_data, once=True)

                                                    # Start the update timer
                                                    ui.timer(2.0, update_dashboard_device_data, once=True)
                                                else:
                                                    ui.label("Disconnected").style("color: #888888; font-size: 12px;")
                                        elif device['type'] == 'edwards_tic':
                                            ui.label("P: 1.0e-3 mbar").style("color: #66bb6a; font-size: 12px; font-weight: bold;")

            # Right column - Webcam section
            with ui.column().style("flex: 1; gap: 15px;"):
                # Webcam section - show if a dashboard webcam is selected
                if fume_hood.get('dashboard_webcam'):
                    dashboard_webcam_name = fume_hood.get('dashboard_webcam')
                    # Find the webcam details
                    webcam = None
                    if 'webcams' in fume_hood:
                        for cam in fume_hood['webcams']:
                            if cam['name'] == dashboard_webcam_name:
                                webcam = cam
                                break

                    if webcam:
                        with ui.column().style("width: 100%; gap: 10px;"):
                            ui.label(f"Webcam: {webcam['name']}").style("color: white; font-size: 14px; font-weight: bold;")

                            # Check if webcam is connected
                            key = (fume_hood['name'], webcam['name'])
                            is_connected = key in fume_hood_page.active_webcam_captures

                            # Display webcam feed
                            if is_connected:
                                # Show live feed
                                ui.label(f"📹 Live Feed - Device {webcam['url']}").style("color: #66bb6a; font-size: 14px; margin-bottom: 10px;")
                                dashboard_image = ui.interactive_image().style("width: 100%; max-width: 400px; height: auto; border-radius: 8px;")
                                fume_hood_page.register_webcam_image(fume_hood, webcam, dashboard_image)
                            else:
                                # Show disconnected message
                                with ui.card().style("background-color: #444444; padding: 30px; width: 100%; max-width: 400px; height: 300px; display: flex; align-items: center; justify-content: center;"):
                                    with ui.column().style("align-items: center; gap: 10px;"):
                                        ui.label("📹").style("color: #666666; font-size: 36px;")
                                        ui.label("Camera Disconnected").style("color: #888888; font-size: 14px;")
                                        ui.label(f"Device {webcam['url']}").style("color: #666666; font-size: 12px;")
