# pages/fume_hood.py
from nicegui import ui
import cv2
import asyncio
from typing import Optional

# Store fume hoods (in a real app, this would be in a database or state management)
fume_hoods = []

# Container reference for re-rendering
fume_hood_container = None

# Dictionary to store active webcam captures and latest frames
active_webcam_captures = {}  # Format: {(fume_hood_name, webcam_name): {'capture': cv2.VideoCapture, 'frame_base64': str, 'running': bool, 'images': []}}

def cleanup_all_webcams():
    """Disconnect all webcams and release resources - called on app shutdown"""
    global active_webcam_captures

    print("Cleaning up all webcams...")
    keys_to_remove = list(active_webcam_captures.keys())

    for key in keys_to_remove:
        try:
            # Stop the update loop
            active_webcam_captures[key]['running'] = False

            # Release the capture
            cap = active_webcam_captures[key]['capture']
            if cap.isOpened():
                cap.release()

            print(f"Released webcam: {key}")
        except Exception as e:
            print(f"Error releasing webcam {key}: {e}")

    # Clear the dictionary
    active_webcam_captures.clear()

    # Give OpenCV time to release resources
    cv2.destroyAllWindows()
    print("All webcams cleaned up")

def connect_webcam(fume_hood, webcam):
    """Connect to a USB camera and start streaming"""
    key = (fume_hood['name'], webcam['name'])

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

def disconnect_webcam(fume_hood, webcam):
    """Disconnect from a USB camera and stop streaming"""
    key = (fume_hood['name'], webcam['name'])

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

                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Encode frame to JPEG
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
            print(f"Error updating webcam frame for {key}: {e}")
            break

    # Clean up if loop exits due to error
    if key in active_webcam_captures:
        try:
            active_webcam_captures[key]['capture'].release()
            del active_webcam_captures[key]
        except:
            pass

def register_webcam_image(fume_hood, webcam, image_element):
    """Register an image element to receive webcam updates"""
    key = (fume_hood['name'], webcam['name'])
    if key in active_webcam_captures:
        active_webcam_captures[key]['images'].append(image_element)
        # Set initial frame if available
        if active_webcam_captures[key]['frame_base64']:
            image_element.set_source(active_webcam_captures[key]['frame_base64'])

def show_add_fume_hood_dialog():
    """Show dialog to add a new fume hood"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Add Fume Hood").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        selected_fume_hood = {'name': '', 'description': '', 'assigned_person': '', 'contact_number': ''}

        # Fume Hood name input
        ui.label("Fume Hood Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(placeholder="e.g., Main Lab Fume Hood").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            selected_fume_hood['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Fume Hood description input
        ui.label("Description:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        description_input = ui.textarea(placeholder="e.g., Located in main chemistry lab, workspace A").style("width: 100%;").props("dark outlined")

        def on_description_change(e):
            selected_fume_hood['description'] = e.value

        description_input.on_value_change(on_description_change)

        # Assigned person input
        ui.label("Assigned Person:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        person_input = ui.input(placeholder="e.g., Dr. John Smith").style("width: 100%;").props("dark outlined")

        def on_person_change(e):
            selected_fume_hood['assigned_person'] = e.value

        person_input.on_value_change(on_person_change)

        # Contact number input
        ui.label("Contact Number:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        contact_input = ui.input(placeholder="e.g., +1-555-0123 or ext. 1234").style("width: 100%;").props("dark outlined")

        def on_contact_change(e):
            selected_fume_hood['contact_number'] = e.value

        contact_input.on_value_change(on_contact_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def add_fume_hood():
                # Validate inputs
                if not selected_fume_hood['name']:
                    ui.notify("Please enter a fume hood name", type='warning')
                    return

                # Check if name already exists
                if any(fh['name'] == selected_fume_hood['name'] for fh in fume_hoods):
                    ui.notify("A fume hood with this name already exists", type='warning')
                    return

                # Add fume hood with initial monitoring state
                new_fume_hood = {
                    'name': selected_fume_hood['name'],
                    'description': selected_fume_hood['description'],
                    'assigned_person': selected_fume_hood['assigned_person'],
                    'contact_number': selected_fume_hood['contact_number'],
                    'sash_open': False,  # True if sash is open, False if closed
                    'alarm_active': False,
                    'webcams': [],  # List of webcams: [{'name': 'Front View', 'url': 'http://...', 'show_on_dashboard': False}, ...]
                    'dashboard_webcam': None  # Name of webcam to show on dashboard
                }

                fume_hoods.append(new_fume_hood)
                ui.notify(f"Added fume hood: {selected_fume_hood['name']}", type='positive')
                dialog.close()

                refresh_fume_hood_list()

            ui.button("Add Fume Hood", on_click=add_fume_hood, icon="add").props("color=primary")

    dialog.open()

def refresh_fume_hood_list():
    """Refresh the fume hood list display"""
    global fume_hood_container

    if fume_hood_container:
        fume_hood_container.clear()
        with fume_hood_container:
            render_fume_hood_list()

def render_fume_hood_list():
    """Render the list of fume hoods"""
    if fume_hoods:
        # Use tabs for multiple fume hoods
        tabs = ui.tabs().props("dense align=left").style("background-color: #333333; width: 100%;")
        with tabs:
            for fume_hood in fume_hoods:
                ui.tab(fume_hood['name'], icon="air").classes("text-white")

        with ui.tab_panels(tabs, value=fume_hoods[0]['name'] if fume_hoods else None).style("background-color: transparent; width: 100%; height: calc(100vh - 310px); overflow-y: auto;"):
            for fume_hood in fume_hoods:
                with ui.tab_panel(fume_hood['name']):
                    render_fume_hood_panel(fume_hood)
    else:
        ui.label("No fume hoods configured").style("color: #888888; font-size: 16px; margin-top: 20px;")

def render():
    """Render the fume hood page content"""
    global fume_hood_container

    with ui.column().style("padding: 20px; width: 100%; gap: 20px;"):
        # Add fume hood button at top
        ui.button("Add Fume Hood", icon="add", on_click=show_add_fume_hood_dialog).props("color=primary")

        # Fume hood list container (for dynamic updates)
        fume_hood_container = ui.column().style("width: 100%;")
        with fume_hood_container:
            render_fume_hood_list()

def remove_fume_hood(fume_hood_name):
    """Remove a fume hood by name"""
    global fume_hoods

    # Find the fume hood to remove
    fume_hood_to_remove = None
    for fh in fume_hoods:
        if fh['name'] == fume_hood_name:
            fume_hood_to_remove = fh
            break

    # Disconnect all webcams before removing
    if fume_hood_to_remove and 'webcams' in fume_hood_to_remove:
        for webcam in fume_hood_to_remove['webcams']:
            key = (fume_hood_name, webcam['name'])
            if key in active_webcam_captures:
                disconnect_webcam(fume_hood_to_remove, webcam)

    # Remove the fume hood
    fume_hoods = [fh for fh in fume_hoods if fh['name'] != fume_hood_name]
    ui.notify(f"Removed fume hood: {fume_hood_name}", type='positive')

    refresh_fume_hood_list()

def edit_fume_hood(fume_hood):
    """Show dialog to edit fume hood name and description"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Edit Fume Hood").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        edited_data = {
            'name': fume_hood['name'],
            'description': fume_hood.get('description', ''),
            'assigned_person': fume_hood.get('assigned_person', ''),
            'contact_number': fume_hood.get('contact_number', '')
        }

        # Name input
        ui.label("Fume Hood Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(value=fume_hood['name'], placeholder="e.g., Main Lab Fume Hood").style("width: 100%;").props("dark outlined")

        def on_name_change(e):
            edited_data['name'] = e.value

        name_input.on_value_change(on_name_change)

        # Description input
        ui.label("Description:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        description_input = ui.textarea(value=fume_hood.get('description', ''), placeholder="e.g., Located in main chemistry lab, workspace A").style("width: 100%;").props("dark outlined")

        def on_description_change(e):
            edited_data['description'] = e.value

        description_input.on_value_change(on_description_change)

        # Assigned person input
        ui.label("Assigned Person:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        person_input = ui.input(value=fume_hood.get('assigned_person', ''), placeholder="e.g., Dr. John Smith").style("width: 100%;").props("dark outlined")

        def on_person_change(e):
            edited_data['assigned_person'] = e.value

        person_input.on_value_change(on_person_change)

        # Contact number input
        ui.label("Contact Number:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 20px;")
        contact_input = ui.input(value=fume_hood.get('contact_number', ''), placeholder="e.g., 07123456789").style("width: 100%;").props("dark outlined")

        def on_contact_change(e):
            edited_data['contact_number'] = e.value

        contact_input.on_value_change(on_contact_change)

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

            def save_changes():
                # Validate name
                if not edited_data['name']:
                    ui.notify("Please enter a fume hood name", type='warning')
                    return

                # Check if new name conflicts with another fume hood
                if edited_data['name'] != fume_hood['name']:
                    if any(fh['name'] == edited_data['name'] for fh in fume_hoods):
                        ui.notify("A fume hood with this name already exists", type='warning')
                        return

                # Update fume hood (preserve webcams and dashboard_webcam)
                fume_hood['name'] = edited_data['name']
                fume_hood['description'] = edited_data['description']
                fume_hood['assigned_person'] = edited_data['assigned_person']
                fume_hood['contact_number'] = edited_data['contact_number']

                ui.notify(f"Updated fume hood: {edited_data['name']}", type='positive')
                dialog.close()
                refresh_fume_hood_list()

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

def show_add_webcam_dialog(fume_hood):
    """Show dialog to add a webcam to a fume hood"""
    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Add Webcam").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

        webcam_data = {'name': '', 'url': ''}

        # Webcam name input
        ui.label("Webcam Name:").style("color: white; font-size: 16px; margin-bottom: 10px;")
        name_input = ui.input(placeholder="e.g., Front View, Side View").style("width: 100%;").props("dark outlined")

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
                    ui.notify("Please select a USB camera", type='warning')
                    return

                # Check if name already exists for this fume hood
                if 'webcams' not in fume_hood:
                    fume_hood['webcams'] = []

                if any(cam['name'] == webcam_data['name'] for cam in fume_hood['webcams']):
                    ui.notify("A webcam with this name already exists for this fume hood", type='warning')
                    return

                # Add webcam
                new_webcam = {
                    'name': webcam_data['name'],
                    'url': webcam_data['url']
                }

                fume_hood['webcams'].append(new_webcam)
                ui.notify(f"Added webcam: {webcam_data['name']}", type='positive')
                dialog.close()
                refresh_fume_hood_list()

            ui.button("Add Webcam", on_click=add_webcam, icon="videocam").props("color=primary")

    dialog.open()

def remove_webcam(fume_hood, webcam_name):
    """Remove a webcam from a fume hood"""
    if 'webcams' in fume_hood:
        # Find the webcam to disconnect
        webcam_to_remove = None
        for cam in fume_hood['webcams']:
            if cam['name'] == webcam_name:
                webcam_to_remove = cam
                break

        # Disconnect if connected
        if webcam_to_remove:
            key = (fume_hood['name'], webcam_name)
            if key in active_webcam_captures:
                disconnect_webcam(fume_hood, webcam_to_remove)

        # Remove from list
        fume_hood['webcams'] = [cam for cam in fume_hood['webcams'] if cam['name'] != webcam_name]

        # Clear dashboard webcam if it was the removed one
        if fume_hood.get('dashboard_webcam') == webcam_name:
            fume_hood['dashboard_webcam'] = None

        ui.notify(f"Removed webcam: {webcam_name}", type='positive')
        refresh_fume_hood_list()

def set_dashboard_webcam(fume_hood, webcam_name):
    """Set which webcam to show on the dashboard"""
    fume_hood['dashboard_webcam'] = webcam_name
    ui.notify(f"Dashboard webcam set to: {webcam_name}", type='positive')
    refresh_fume_hood_list()

def show_add_device_dialog(fume_hood):
    """Show dialog to assign a device to a fume hood"""
    from pages import devices as devices_page

    # Get devices not already assigned to this fume hood
    assigned_device_names = [d['name'] for d in fume_hood.get('assigned_devices', [])]
    available_devices = [d for d in devices_page.devices if d['name'] not in assigned_device_names]

    if not available_devices:
        ui.notify("No available devices to assign", type='warning')
        return

    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
        ui.label("Assign Device to Fume Hood").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

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
                if 'assigned_devices' not in fume_hood:
                    fume_hood['assigned_devices'] = []

                # Add device reference to fume hood
                fume_hood['assigned_devices'].append(selected_device['device'])

                ui.notify(f"Assigned {selected_device['device']['name']} to {fume_hood['name']}", type='positive')
                dialog.close()
                refresh_fume_hood_list()

            ui.button("Assign Device", on_click=assign_device, icon="add").props("color=primary")

    dialog.open()

def render_fume_hood_panel(fume_hood):
    """Render the monitoring panel for a specific fume hood"""
    with ui.column().style("width: 100%; gap: 0;"):
        # Sticky header with fume hood name and remove button
        with ui.row().style("position: sticky; top: 0; z-index: 10; width: 100%; justify-content: space-between; align-items: center; padding: 20px; background-color: #222222; border-bottom: 1px solid #444444;"):
            # Left: Fume hood info
            with ui.column().style("gap: 5px;"):
                ui.label(f"{fume_hood['name']}").style("color: white; font-size: 18px; font-weight: bold;")
                if fume_hood.get('description'):
                    ui.label(fume_hood['description']).style("color: #888888; font-size: 14px;")

            # Right: Edit and Remove buttons
            with ui.row().style("gap: 10px;"):
                ui.button("Edit", icon="edit", on_click=lambda: edit_fume_hood(fume_hood)).props("flat color=primary")
                ui.button("Remove Fume Hood", icon="delete", on_click=lambda: remove_fume_hood(fume_hood['name'])).props("flat color=negative")

        # Content area (will scroll with outer container) - 2 column layout
        with ui.row().style("padding: 20px; gap: 20px; width: 100%; align-items: flex-start;"):
            # Left column - Status and Controls
            with ui.column().style("flex: 1; gap: 20px; min-width: 400px;"):
                # Main monitoring row
                with ui.row().style("width: 100%; gap: 20px; align-items: stretch;"):
                    # Sash status card
                    with ui.card().style("background-color: #333333; padding: 20px; flex: 1;"):
                        ui.label("Sash Status").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 15px;")

                        # Large status indicator
                        sash_status = "OPEN" if fume_hood['sash_open'] else "CLOSED"
                        sash_color = "#ef5350" if fume_hood['sash_open'] else "#66bb6a"
                        sash_icon = "↑" if fume_hood['sash_open'] else "↓"

                        with ui.column().style("align-items: center; gap: 10px;"):
                            ui.label(sash_icon).style(f"color: {sash_color}; font-size: 48px; font-weight: bold;")
                            ui.badge(sash_status, color="red" if fume_hood['sash_open'] else "green").style("font-size: 16px; padding: 8px 16px;")

                            if fume_hood['sash_open']:
                                ui.label("⚠ Hood is in use").style("color: #ef5350; font-size: 14px; margin-top: 10px;")
                            else:
                                ui.label("✓ Hood is safe").style("color: #66bb6a; font-size: 14px; margin-top: 10px;")

                    # Alarm card
                    with ui.card().style("background-color: #333333; padding: 20px; flex: 1;"):
                        ui.label("Alarm Status").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 15px;")

                        alarm_status = "ACTIVE" if fume_hood['alarm_active'] else "CLEAR"
                        alarm_color = "red" if fume_hood['alarm_active'] else "green"
                        alarm_icon = "🔔" if fume_hood['alarm_active'] else "✓"

                        with ui.column().style("align-items: center; gap: 10px;"):
                            ui.label(alarm_icon).style(f"color: {'#ef5350' if fume_hood['alarm_active'] else '#66bb6a'}; font-size: 48px;")
                            ui.badge(alarm_status, color=alarm_color).style("font-size: 16px; padding: 8px 16px;")

                            if fume_hood['alarm_active']:
                                ui.label("⚠ Check fume hood").style("color: #ef5350; font-size: 14px; margin-top: 10px;")
                            else:
                                ui.label("✓ System normal").style("color: #66bb6a; font-size: 14px; margin-top: 10px;")

                # Control section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Monitoring Controls").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 15px;")

                    with ui.column().style("width: 100%; gap: 10px;"):
                        # Toggle sash button
                        def toggle_sash():
                            fume_hood['sash_open'] = not fume_hood['sash_open']
                            status = "opened" if fume_hood['sash_open'] else "closed"
                            ui.notify(f"Sash {status}", type='warning' if fume_hood['sash_open'] else 'positive')
                            refresh_fume_hood_list()

                        sash_btn_text = "Close Sash" if fume_hood['sash_open'] else "Open Sash"
                        sash_btn_icon = "arrow_downward" if fume_hood['sash_open'] else "arrow_upward"
                        ui.button(sash_btn_text, icon=sash_btn_icon, on_click=toggle_sash).props("color=primary").style("width: 100%;")

                        # Test alarm button
                        def test_alarm():
                            fume_hood['alarm_active'] = not fume_hood['alarm_active']
                            ui.notify("Alarm " + ("activated" if fume_hood['alarm_active'] else "cleared"),
                                    type='warning' if fume_hood['alarm_active'] else 'positive')
                            refresh_fume_hood_list()

                        ui.button("Toggle Alarm", icon="notifications_active", on_click=test_alarm).props("color=orange").style("width: 100%;")

                        # Check info button
                        def show_fume_hood_info():
                            with ui.dialog() as info_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 400px;"):
                                ui.label("Fume Hood Information").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")

                                # Hood name
                                ui.label("Name:").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                                ui.label(fume_hood['name']).style("color: white; font-size: 16px; margin-bottom: 15px;")

                                # Description
                                if fume_hood.get('description'):
                                    ui.label("Description:").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                                    ui.label(fume_hood['description']).style("color: white; font-size: 16px; margin-bottom: 15px;")

                                # Assigned person
                                ui.label("Assigned Person:").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                                assigned_person = fume_hood.get('assigned_person', 'Not assigned')
                                if not assigned_person:
                                    assigned_person = 'Not assigned'
                                ui.label(assigned_person).style("color: white; font-size: 16px; margin-bottom: 15px;")

                                # Contact number
                                ui.label("Contact Number:").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                                contact_number = fume_hood.get('contact_number', 'Not provided')
                                if not contact_number:
                                    contact_number = 'Not provided'
                                ui.label(contact_number).style("color: white; font-size: 16px; margin-bottom: 20px;")

                                # Close button
                                with ui.row().style("width: 100%; justify-content: flex-end;"):
                                    ui.button("Close", on_click=info_dialog.close).props("color=primary")

                            info_dialog.open()

                        ui.button("Check Info", icon="info", on_click=show_fume_hood_info).props("flat color=white").style("width: 100%;")

                        # Reset button
                        def reset_fume_hood():
                            fume_hood['sash_open'] = False
                            fume_hood['alarm_active'] = False
                            ui.notify("Fume hood reset", type='info')
                            refresh_fume_hood_list()

                        ui.button("Reset", icon="restart_alt", on_click=reset_fume_hood).props("flat color=white").style("width: 100%;")

                # Information section (moved to left column)
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Safety Information").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("• Keep sash closed when hood is not in use").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                    ui.label("• Sash should be at lowest practical height during operation").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                    ui.label("• Respond immediately to alarm conditions").style("color: #888888; font-size: 14px; margin-bottom: 5px;")
                    ui.label("• Regular monitoring ensures safe laboratory operation").style("color: #888888; font-size: 14px;")

                # Assigned Devices section
                from pages import devices as devices_page

                # Only show "Add Device" button if devices exist on the Devices page
                if devices_page.devices:
                    with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
                            ui.label("Assigned Devices").style("color: white; font-size: 16px; font-weight: bold;")
                            ui.button("Add Device", icon="add_circle", on_click=lambda: show_add_device_dialog(fume_hood)).props("color=primary")

                        # Initialize assigned_devices list if not exists
                        if 'assigned_devices' not in fume_hood:
                            fume_hood['assigned_devices'] = []

                        if fume_hood['assigned_devices']:
                            # Display assigned devices
                            for device in fume_hood['assigned_devices']:
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
                                            fume_hood['assigned_devices'].remove(dev)
                                            ui.notify(f"Removed {dev['name']} from {fume_hood['name']}", type='positive')
                                            refresh_fume_hood_list()

                                        ui.button(icon="close", on_click=remove_device).props("flat dense color=negative")
                        else:
                            ui.label("No devices assigned yet").style("color: #888888; font-size: 14px; text-align: center;")

            # Right column - Webcam section
            with ui.column().style("flex: 1; gap: 20px; min-width: 500px;"):
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
                        ui.label("Webcam Monitoring").style("color: white; font-size: 16px; font-weight: bold;")
                        ui.button("Add Webcam", icon="videocam", on_click=lambda: show_add_webcam_dialog(fume_hood)).props("color=primary")

                    # Initialize webcams list if not exists
                    if 'webcams' not in fume_hood:
                        fume_hood['webcams'] = []

                    if fume_hood['webcams']:
                        # Display webcams
                        for webcam in fume_hood['webcams']:
                            with ui.card().style("background-color: #444444; padding: 15px; margin-bottom: 10px;"):
                                with ui.row().style("width: 100%; justify-content: space-between; align-items: center;"):
                                    # Left: Webcam info
                                    with ui.column().style("gap: 5px; flex: 1;"):
                                        ui.label(webcam['name']).style("color: white; font-size: 16px; font-weight: bold;")
                                        ui.label(f"Source: Device {webcam['url']}").style("color: #888888; font-size: 14px;")

                                        # Show if this is the dashboard webcam
                                        if fume_hood.get('dashboard_webcam') == webcam['name']:
                                            ui.badge("Shown on Dashboard", color="green").style("margin-top: 5px;")

                                    # Right: Actions
                                    with ui.row().style("gap: 10px;"):
                                        # Set as dashboard webcam button
                                        if fume_hood.get('dashboard_webcam') != webcam['name']:
                                            ui.button("Set for Dashboard", icon="dashboard",
                                                    on_click=lambda w=webcam['name']: set_dashboard_webcam(fume_hood, w)).props("flat color=primary")
                                        else:
                                            ui.button("Remove from Dashboard", icon="dashboard_customize",
                                                    on_click=lambda: set_dashboard_webcam(fume_hood, None)).props("flat color=orange")

                                        # Remove webcam button
                                        ui.button("Remove", icon="delete",
                                                on_click=lambda w=webcam['name']: remove_webcam(fume_hood, w)).props("flat color=negative")

                                # Webcam feed display
                                with ui.column().style("width: 100%; align-items: center; margin-top: 10px;"):
                                    # Check if this webcam is connected
                                    key = (fume_hood['name'], webcam['name'])
                                    is_connected = key in active_webcam_captures

                                    # Create image element for video display
                                    if is_connected:
                                        # Show live feed
                                        webcam_image = ui.interactive_image().style("width: 100%; max-width: 640px; height: auto; border-radius: 8px;")
                                        register_webcam_image(fume_hood, webcam, webcam_image)
                                    else:
                                        # Show placeholder with centered text
                                        with ui.card().style("width: 100%; max-width: 640px; height: 480px; background-color: #333333; border-radius: 8px; position: relative; display: flex; align-items: center; justify-content: center;"):
                                            with ui.column().style("align-items: center; gap: 10px;"):
                                                ui.label("📹").style("color: #666666; font-size: 48px;")
                                                ui.label("Camera Disconnected").style("color: #888888; font-size: 16px;")

                                    # Connection control buttons
                                    with ui.row().style("gap: 10px; margin-top: 10px;"):
                                        if is_connected:
                                            def disconnect_handler(h=fume_hood, w=webcam):
                                                disconnect_webcam(h, w)
                                                refresh_fume_hood_list()
                                            ui.button("Disconnect", icon="videocam_off", on_click=disconnect_handler).props("color=negative")
                                        else:
                                            def connect_handler(h=fume_hood, w=webcam):
                                                if connect_webcam(h, w):
                                                    refresh_fume_hood_list()
                                            ui.button("Connect", icon="videocam", on_click=connect_handler).props("color=primary")
                    else:
                        ui.label("No webcams configured. Click 'Add Webcam' to add a camera feed.").style("color: #888888; font-size: 14px;")
