# pages/bench.py
from nicegui import ui
import cv2
import asyncio
from typing import Optional

# Store benches (in a real app, this would be in a database or state management)
benches = []

# Container reference for re-rendering
bench_container = None

# Dictionary to store active webcam captures and latest frames
active_webcam_captures = {}  # Format: {(bench_name, webcam_name): {'capture': cv2.VideoCapture, 'frame_base64': str, 'running': bool, 'images': []}}

def cleanup_all_webcams():
    """Disconnect all webcams and release resources - called on app shutdown"""
    global active_webcam_captures

    print("Cleaning up all bench webcams...")
    keys_to_remove = list(active_webcam_captures.keys())

    for key in keys_to_remove:
        try:
            # Stop the update loop
            active_webcam_captures[key]['running'] = False

            # Release the capture
            cap = active_webcam_captures[key]['capture']
            if cap.isOpened():
                cap.release()

            print(f"Released bench webcam: {key}")
        except Exception as e:
            print(f"Error releasing bench webcam {key}: {e}")

    # Clear the dictionary
    active_webcam_captures.clear()

    # Give OpenCV time to release resources
    cv2.destroyAllWindows()
    print("All bench webcams cleaned up")

def connect_webcam(bench, webcam):
    """Connect to a USB camera and start streaming"""
    key = (bench['name'], webcam['name'])

    # Check if already connected
    if key in active_webcam_captures:
        ui.notify(f"Webcam '{webcam['name']}' is already connected", type='warning')
        return False

    try:
        device_id = int(webcam['url'])
        # Use DirectShow backend to avoid MSMF conflicts when multiple cameras are used
        cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)

        if not cap.isOpened():
            ui.notify(f"Failed to open camera {device_id}", type='negative')
            return False

        # Store capture and frame data
        active_webcam_captures[key] = {
            'capture': cap,
            'frame_base64': None,
            'running': True,
            'images': []  # List of image elements to update
        }

        # Start async frame update
        asyncio.create_task(update_webcam_frame(key))

        ui.notify(f"Connected to webcam '{webcam['name']}'", type='positive')
        return True

    except Exception as e:
        ui.notify(f"Error connecting to webcam: {str(e)}", type='negative')
        return False

def disconnect_webcam(bench, webcam):
    """Disconnect from a USB camera and stop streaming"""
    key = (bench['name'], webcam['name'])

    if key not in active_webcam_captures:
        ui.notify(f"Webcam '{webcam['name']}' is not connected", type='warning')
        return False

    try:
        # Stop the update loop
        active_webcam_captures[key]['running'] = False

        # Release the capture
        cap = active_webcam_captures[key]['capture']
        cap.release()

        # Remove from active captures
        del active_webcam_captures[key]

        ui.notify(f"Disconnected webcam '{webcam['name']}'", type='info')
        return True

    except Exception as e:
        ui.notify(f"Error disconnecting webcam: {str(e)}", type='negative')
        return False

async def update_webcam_frame(key):
    """Async function to continuously update webcam frames"""
    import base64

    while key in active_webcam_captures and active_webcam_captures[key]['running']:
        try:
            cap = active_webcam_captures[key]['capture']

            ret, frame = cap.read()

            if ret:
                # Resize frame for display (640x480)
                frame = cv2.resize(frame, (640, 480))

                # Encode frame to JPEG (cv2.imencode expects BGR format)
                _, buffer = cv2.imencode('.jpg', frame)

                # Convert to base64
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                data_url = f'data:image/jpeg;base64,{img_base64}'

                # Store the frame
                active_webcam_captures[key]['frame_base64'] = data_url

                # Update all registered image elements
                for img_element in active_webcam_captures[key]['images']:
                    try:
                        img_element.set_source(data_url)
                    except:
                        pass  # Element might have been deleted

            # Wait before next frame (30 FPS)
            await asyncio.sleep(0.033)

        except Exception as e:
            print(f"Error updating bench webcam frame for {key}: {e}")
            break

    # Clean up if loop exits due to error
    if key in active_webcam_captures:
        try:
            active_webcam_captures[key]['capture'].release()
            del active_webcam_captures[key]
        except:
            pass

def register_webcam_image(bench, webcam, image_element):
    """Register an image element to receive webcam updates"""
    key = (bench['name'], webcam['name'])
    if key in active_webcam_captures:
        active_webcam_captures[key]['images'].append(image_element)
        # Set initial frame if available
        if active_webcam_captures[key]['frame_base64']:
            image_element.set_source(active_webcam_captures[key]['frame_base64'])

def show_add_bench_dialog():
    """Show dialog to add a new bench"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Add Bench").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        selected_bench = {'name': '', 'description': '', 'location': ''}

        # Bench name input
        ui.label("Bench Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(placeholder="e.g., Main Bench, Synthesis Bench").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            selected_bench['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Description input
        ui.label("Description (optional):").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        description_input = ui.input(placeholder="Brief description of bench").style("width: 100%;").props("dark outlined")

        def on_description_change(e):
            selected_bench['description'] = e.value

        description_input.on_value_change(on_description_change)

        # Location input
        ui.label("Location (optional):").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        location_input = ui.input(placeholder="e.g., Room 101, Lab A").style("width: 100%;").props("dark outlined")

        def on_location_change(e):
            selected_bench['location'] = e.value

        location_input.on_value_change(on_location_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def add_bench():
                if not selected_bench['name']:
                    ui.notify("Please enter a bench name", type='warning')
                    return

                # Check for duplicate names
                if any(b['name'] == selected_bench['name'] for b in benches):
                    ui.notify(f"A bench named '{selected_bench['name']}' already exists", type='negative')
                    return

                new_bench = {
                    'name': selected_bench['name'],
                    'description': selected_bench.get('description', ''),
                    'location': selected_bench.get('location', ''),
                    'webcams': [],  # List of webcams: [{'name': 'Front View', 'url': 'http://...', 'show_on_dashboard': False}, ...]
                    'dashboard_webcam': None  # Name of webcam to show on dashboard
                }

                benches.append(new_bench)
                ui.notify(f"Added bench: {selected_bench['name']}", type='positive')
                dialog.close()

                refresh_bench_list()

            ui.button("Add Bench", on_click=add_bench, icon="add").props("color=primary")

    dialog.open()

def refresh_bench_list():
    """Refresh the bench list display"""
    global bench_container

    if bench_container:
        bench_container.clear()
        with bench_container:
            render_bench_list()

def render_bench_list():
    """Render the list of benches"""
    if benches:
        with ui.tabs().props("dense").classes("text-white") as tabs:
            for bench in benches:
                ui.tab(bench['name']).classes("text-white")

        with ui.tab_panels(tabs, value=benches[0]['name'] if benches else None).style("background-color: transparent; width: 100%; height: calc(100vh - 310px); overflow-y: auto;"):
            for bench in benches:
                with ui.tab_panel(bench['name']):
                    render_bench_panel(bench)
    else:
        ui.label("No benches configured").style("color: #888888; font-size: 16px; margin-top: 20px;")

def render():
    """Render the bench page content"""
    global bench_container

    with ui.column().style("padding: 20px; width: 100%; gap: 20px;"):
        # Add bench button at top
        ui.button("Add Bench", icon="add", on_click=show_add_bench_dialog).props("color=primary")

        # Bench list container (for dynamic updates)
        bench_container = ui.column().style("width: 100%;")
        with bench_container:
            render_bench_list()

def remove_bench(bench_name):
    """Remove a bench by name"""
    global benches

    # Find the bench to remove
    bench_to_remove = None
    for b in benches:
        if b['name'] == bench_name:
            bench_to_remove = b
            break

    # Disconnect all webcams before removing
    if bench_to_remove and 'webcams' in bench_to_remove:
        for webcam in bench_to_remove['webcams']:
            key = (bench_name, webcam['name'])
            if key in active_webcam_captures:
                disconnect_webcam(bench_to_remove, webcam)

    # Remove the bench
    benches = [b for b in benches if b['name'] != bench_name]
    ui.notify(f"Removed bench: {bench_name}", type='positive')

    refresh_bench_list()

def edit_bench(bench):
    """Show dialog to edit bench name and description"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Edit Bench").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        edited_data = {
            'name': bench['name'],
            'description': bench.get('description', ''),
            'location': bench.get('location', '')
        }

        # Name input
        ui.label("Bench Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(value=bench['name']).style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            edited_data['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Description input
        ui.label("Description:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        description_input = ui.input(value=bench.get('description', '')).style("width: 100%;").props("dark outlined")

        def on_description_change(e):
            edited_data['description'] = e.value

        description_input.on_value_change(on_description_change)

        # Location input
        ui.label("Location:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        location_input = ui.input(value=bench.get('location', '')).style("width: 100%;").props("dark outlined")

        def on_location_change(e):
            edited_data['location'] = e.value

        location_input.on_value_change(on_location_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def save_changes():
                if not edited_data['name']:
                    ui.notify("Please enter a bench name", type='warning')
                    return

                # Check for duplicate names (excluding current bench)
                if edited_data['name'] != bench['name'] and any(b['name'] == edited_data['name'] for b in benches):
                    ui.notify(f"A bench named '{edited_data['name']}' already exists", type='negative')
                    return

                # Update bench data
                bench['name'] = edited_data['name']
                bench['description'] = edited_data['description']
                bench['location'] = edited_data['location']

                ui.notify(f"Updated bench: {edited_data['name']}", type='positive')
                dialog.close()
                refresh_bench_list()

            ui.button("Save Changes", on_click=save_changes, icon="save").props("color=primary")

    dialog.open()

def get_available_cameras():
    """Detect available USB cameras"""
    available_cameras = []

    # Test cameras 0-4 (most systems won't have more than 5 cameras)
    for i in range(5):
        try:
            # Use DirectShow on Windows to avoid Intel RealSense issues
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

            # Set a short timeout
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)

            if cap.isOpened():
                # Try to read a frame to confirm camera is working
                ret, _ = cap.read()
                if ret:
                    available_cameras.append({
                        'id': i,
                        'name': f"Camera {i}"
                    })
                cap.release()
        except Exception as e:
            print(f"Error checking camera {i}: {e}")
            continue

    return available_cameras

def show_add_webcam_dialog(bench):
    """Show dialog to add a webcam to a bench"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Add Webcam").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        webcam_data = {'name': '', 'url': ''}

        # Webcam name input
        ui.label("Webcam Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(placeholder="e.g., Front View, Top View").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            webcam_data['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Webcam Device ID dropdown (USB connection)
        ui.label("Select USB Camera:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")

        # Create placeholder for status and dropdown
        status_label = ui.label("Detecting cameras...").style("color: #888888; font-size: 14px; margin-bottom: 10px;")

        # Create camera dropdown (will be populated after detection)
        camera_select = ui.select([], value=None).style("width: 100%;").props("dark outlined disabled")

        def on_camera_change(e):
            if e.value and e.value != "No cameras detected":
                # Extract device ID from selection (e.g., "Camera 0 (Device 0)" -> "0")
                device_id = e.value.split("Device ")[1].rstrip(")")
                webcam_data['url'] = device_id

        camera_select.on_value_change(on_camera_change)

        # Detect cameras asynchronously after dialog opens
        async def detect_cameras():
            try:
                # Run detection in background
                available_cameras = await asyncio.get_event_loop().run_in_executor(None, get_available_cameras)

                # Update UI with results
                if available_cameras:
                    camera_options = [f"{cam['name']} (Device {cam['id']})" for cam in available_cameras]
                    status_label.set_text(f"Found {len(available_cameras)} camera(s)")
                    status_label.style("color: #66bb6a; font-size: 14px; margin-bottom: 10px;")
                else:
                    camera_options = ["No cameras detected"]
                    status_label.set_text("No cameras found")
                    status_label.style("color: #ef5350; font-size: 14px; margin-bottom: 10px;")

                # Update dropdown
                camera_select.options = camera_options
                camera_select.props(remove="disabled")
                camera_select.update()
            except Exception as e:
                status_label.set_text(f"Error detecting cameras: {str(e)}")
                status_label.style("color: #ef5350; font-size: 14px; margin-bottom: 10px;")
                camera_select.options = ["Error - try again"]
                camera_select.update()

        # Start detection
        ui.timer(0.1, lambda: asyncio.create_task(detect_cameras()), once=True)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def add_webcam():
                # Validate inputs
                if not webcam_data['name']:
                    ui.notify("Please enter a webcam name", type='warning')
                    return

                if not webcam_data['url']:
                    ui.notify("Please select a camera", type='warning')
                    return

                # Check for duplicate names
                if any(w['name'] == webcam_data['name'] for w in bench['webcams']):
                    ui.notify(f"A webcam named '{webcam_data['name']}' already exists for this bench", type='negative')
                    return

                # Add webcam to bench
                bench['webcams'].append({
                    'name': webcam_data['name'],
                    'url': webcam_data['url']
                })

                ui.notify(f"Added webcam: {webcam_data['name']}", type='positive')
                dialog.close()
                refresh_bench_list()

            ui.button("Add Webcam", on_click=add_webcam, icon="videocam").props("color=primary")

    dialog.open()

def remove_webcam(bench, webcam_name):
    """Remove a webcam from a bench"""
    if 'webcams' in bench:
        # Find the webcam to disconnect
        webcam_to_remove = None
        for cam in bench['webcams']:
            if cam['name'] == webcam_name:
                webcam_to_remove = cam
                break

        # Disconnect if connected
        if webcam_to_remove:
            key = (bench['name'], webcam_name)
            if key in active_webcam_captures:
                disconnect_webcam(bench, webcam_to_remove)

        # Remove from list
        bench['webcams'] = [cam for cam in bench['webcams'] if cam['name'] != webcam_name]

        # Clear dashboard webcam if it was the removed one
        if bench.get('dashboard_webcam') == webcam_name:
            bench['dashboard_webcam'] = None

        ui.notify(f"Removed webcam: {webcam_name}", type='positive')
        refresh_bench_list()

def set_dashboard_webcam(bench, webcam_name):
    """Set which webcam to show on the dashboard"""
    bench['dashboard_webcam'] = webcam_name
    ui.notify(f"Dashboard webcam set to: {webcam_name}", type='positive')
    refresh_bench_list()

def show_add_device_dialog(bench):
    """Show dialog to assign a device to a bench"""
    from pages import devices as devices_page

    # Get devices not already assigned to this bench
    assigned_device_names = [d['name'] for d in bench.get('assigned_devices', [])]
    available_devices = [d for d in devices_page.devices if d['name'] not in assigned_device_names]

    if not available_devices:
        ui.notify("No available devices to assign", type='warning')
        return

    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Assign Device to Bench").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        selected_device = {'device': None}

        # Device selection dropdown
        ui.label("Select Device:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        device_options = {d['name']: d for d in available_devices}
        device_select = ui.select(list(device_options.keys()), value=None).style("width: 100%;").props("dark outlined")

        def on_device_change(e):
            if e.value:
                selected_device['device'] = device_options[e.value]

        device_select.on_value_change(on_device_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def assign_device():
                if not selected_device['device']:
                    ui.notify("Please select a device", type='warning')
                    return

                # Initialize assigned_devices list if not exists
                if 'assigned_devices' not in bench:
                    bench['assigned_devices'] = []

                # Add device reference to bench
                bench['assigned_devices'].append(selected_device['device'])

                ui.notify(f"Assigned {selected_device['device']['name']} to {bench['name']}", type='positive')
                dialog.close()
                refresh_bench_list()

            ui.button("Assign Device", on_click=assign_device, icon="add").props("color=primary")

    dialog.open()

def render_bench_panel(bench):
    """Render the monitoring panel for a specific bench"""
    with ui.column().style("width: 100%; gap: 0;"):
        # Sticky header with bench name and remove button
        with ui.row().style("position: sticky; top: 0; z-index: 10; width: 100%; justify-content: space-between; align-items: center; padding: 20px; background-color: #222222; border-bottom: 1px solid #444444;"):
            # Left: Bench info
            with ui.column().style("gap: 5px;"):
                ui.label(f"{bench['name']}").style("color: white; font-size: 18px; font-weight: bold;")
                if bench.get('description'):
                    ui.label(bench['description']).style("color: #888888; font-size: 14px;")
                if bench.get('location'):
                    ui.label(f"Location: {bench['location']}").style("color: #666666; font-size: 12px;")

            # Right: Edit and Remove buttons
            with ui.row().style("gap: 10px;"):
                ui.button("Edit", icon="edit", on_click=lambda: edit_bench(bench)).props("flat color=primary")
                ui.button("Remove Bench", icon="delete", on_click=lambda: remove_bench(bench['name'])).props("flat color=negative")

        # Content area (will scroll with outer container) - 2 column layout
        with ui.row().style("padding: 20px; gap: 20px; width: 100%; align-items: flex-start;"):
            # Left column - Assigned Devices
            with ui.column().style("flex: 1; gap: 20px; min-width: 400px;"):
                # Assigned Devices section
                from pages import devices as devices_page

                # Only show "Add Device" button if devices exist on the Devices page
                if devices_page.devices:
                    with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
                            ui.label("Assigned Devices").style("color: white; font-size: 16px; font-weight: bold;")
                            ui.button("Add Device", icon="add_circle", on_click=lambda: show_add_device_dialog(bench)).props("color=primary")

                        # Initialize assigned_devices list if not exists
                        if 'assigned_devices' not in bench:
                            bench['assigned_devices'] = []

                        if bench['assigned_devices']:
                            # Display assigned devices
                            for device in bench['assigned_devices']:
                                with ui.card().style("background-color: #444444; padding: 15px; margin-bottom: 10px;"):
                                    with ui.row().style("width: 100%; gap: 15px; align-items: center;"):
                                        # Device image (not icon)
                                        import devices as device_modules
                                        device_module = device_modules.get_device_module(device['type'])
                                        device_info = device_module.get_device_info() if device_module else {}

                                        if device_info.get('image'):
                                            ui.image(device_info['image']).style("width: 100px; height: auto; border-radius: 8px;")

                                        # Device name and type
                                        with ui.column().style("flex: 1; gap: 5px;"):
                                            ui.label(device['name']).style("color: white; font-size: 16px; font-weight: bold;")
                                            ui.label(f"Type: {device.get('type', 'Unknown')}").style("color: #888888; font-size: 14px;")

                                        # Remove button
                                        def remove_device(dev=device):
                                            bench['assigned_devices'].remove(dev)
                                            ui.notify(f"Removed {dev['name']} from {bench['name']}", type='positive')
                                            refresh_bench_list()

                                        ui.button(icon="close", on_click=remove_device).props("flat dense color=negative")
                        else:
                            ui.label("No devices assigned yet").style("color: #888888; font-size: 14px; text-align: center;")

            # Right column - Webcam section
            with ui.column().style("flex: 1; gap: 20px; min-width: 500px;"):
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
                        ui.label("Webcam Monitoring").style("color: white; font-size: 16px; font-weight: bold;")
                        ui.button("Add Webcam", icon="videocam", on_click=lambda: show_add_webcam_dialog(bench)).props("color=primary")

                    # Initialize webcams list if not exists
                    if 'webcams' not in bench:
                        bench['webcams'] = []

                    if bench['webcams']:
                        # Display webcams
                        for webcam in bench['webcams']:
                            with ui.card().style("background-color: #444444; padding: 15px; margin-bottom: 10px;"):
                                with ui.row().style("width: 100%; justify-content: space-between; align-items: center;"):
                                    # Left: Webcam info
                                    with ui.column().style("gap: 5px; flex: 1;"):
                                        ui.label(webcam['name']).style("color: white; font-size: 16px; font-weight: bold;")
                                        ui.label(f"Source: Device {webcam['url']}").style("color: #888888; font-size: 14px;")

                                        # Show if this is the dashboard webcam
                                        if bench.get('dashboard_webcam') == webcam['name']:
                                            ui.badge("Shown on Dashboard", color="green").style("margin-top: 5px;")

                                    # Right: Actions
                                    with ui.row().style("gap: 10px;"):
                                        # Set as dashboard webcam button
                                        if bench.get('dashboard_webcam') != webcam['name']:
                                            ui.button("Set for Dashboard", icon="dashboard",
                                                    on_click=lambda w=webcam['name']: set_dashboard_webcam(bench, w)).props("flat color=primary")
                                        else:
                                            ui.button("Remove from Dashboard", icon="dashboard_customize",
                                                    on_click=lambda: set_dashboard_webcam(bench, None)).props("flat color=orange")

                                        # Remove webcam button
                                        ui.button("Remove", icon="delete",
                                                on_click=lambda w=webcam['name']: remove_webcam(bench, w)).props("flat color=negative")

                                # Webcam feed display
                                with ui.column().style("width: 100%; align-items: center; margin-top: 10px;"):
                                    # Check if this webcam is connected
                                    key = (bench['name'], webcam['name'])
                                    is_connected = key in active_webcam_captures

                                    # Create image element for video display
                                    if is_connected:
                                        # Show live feed
                                        webcam_image = ui.interactive_image().style("width: 100%; max-width: 640px; height: auto; border-radius: 8px;")
                                        register_webcam_image(bench, webcam, webcam_image)
                                    else:
                                        # Show placeholder with centered text
                                        with ui.card().style("width: 100%; max-width: 640px; height: 480px; background-color: #333333; border-radius: 8px; position: relative; display: flex; align-items: center; justify-content: center;"):
                                            with ui.column().style("align-items: center; gap: 10px;"):
                                                ui.label("📹").style("color: #666666; font-size: 48px;")
                                                ui.label("Camera Disconnected").style("color: #888888; font-size: 16px;")

                                    # Connection control buttons
                                    with ui.row().style("gap: 10px; margin-top: 10px;"):
                                        if is_connected:
                                            def disconnect_handler(b=bench, w=webcam):
                                                disconnect_webcam(b, w)
                                                refresh_bench_list()
                                            ui.button("Disconnect", icon="videocam_off", on_click=disconnect_handler).props("color=negative")
                                        else:
                                            def connect_handler(b=bench, w=webcam):
                                                if connect_webcam(b, w):
                                                    refresh_bench_list()
                                            ui.button("Connect", icon="videocam", on_click=connect_handler).props("color=primary")
                    else:
                        ui.label("No webcams configured. Click 'Add Webcam' to add a camera feed.").style("color: #888888; font-size: 14px;")
