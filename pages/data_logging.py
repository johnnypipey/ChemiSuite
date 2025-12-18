"""
Data Logging Page - Monitor and record device data over time
"""

from nicegui import ui
from data_logger import data_logger
from datetime import datetime
import os

def render():
    """Render the data logging page"""

    # Import devices_page to access devices list
    from pages import devices as devices_page

    # Storage for UI elements that need to be updated
    ui_refs = {
        'status_label': None,
        'elapsed_label': None,
        'data_points_label': None,
        'chart_container': None,
        'device_checkboxes': {},
        'parameter_checkboxes': {},
        'start_button': None,
        'stop_button': None,
        'pause_button': None,
        'session_name_input': None,
        'interval_input': None,
        'sessions_container': None
    }

    with ui.column().style("padding: 20px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Page header
        ui.label("Data Logging").style("color: white; font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        ui.label("Record sensor data from devices over time for analysis and reporting").style("color: #888888; font-size: 14px; margin-bottom: 20px;")

        # Main content - 2 column layout
        with ui.row().style("width: 100%; gap: 20px;"):
            # Left column - Session controls
            with ui.column().style("flex: 1; gap: 20px;"):
                # Current Session Card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Session Control").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                    # Session name input
                    ui_refs['session_name_input'] = ui.input(
                        label="Session Name",
                        placeholder=f"Experiment {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    ).props("dark outlined").style("width: 100%; margin-bottom: 15px;")

                    # Polling interval
                    ui_refs['interval_input'] = ui.number(
                        label="Polling Interval (seconds)",
                        value=5,
                        min=1,
                        max=300
                    ).props("dark outlined").style("width: 100%; margin-bottom: 15px;")

                    # Device selection
                    ui.label("Select Devices to Log:").style("color: white; font-size: 16px; margin-bottom: 10px; margin-top: 10px;")

                    device_selection_container = ui.column().style("gap: 10px; width: 100%; margin-bottom: 15px;")

                    def render_device_selection():
                        """Render device selection checkboxes"""
                        device_selection_container.clear()

                        with device_selection_container:
                            if devices_page.devices:
                                for device in devices_page.devices:
                                    # Only show devices that have loggable parameters
                                    if 'loggable_parameters' in device and device['loggable_parameters']:
                                        with ui.card().style("background-color: #444444; padding: 10px; width: 100%;"):
                                            # Device checkbox
                                            device_checkbox = ui.checkbox(
                                                text=f"{device['name']} ({device['type']})",
                                                value=False
                                            ).props("dark color=primary")

                                            ui_refs['device_checkboxes'][device['name']] = device_checkbox

                                            # Parameter selection (initially hidden)
                                            param_container = ui.column().style("margin-left: 30px; margin-top: 10px; gap: 5px;")

                                            with param_container:
                                                ui_refs['parameter_checkboxes'][device['name']] = {}

                                                for param_name, param_config in device['loggable_parameters'].items():
                                                    param_checkbox = ui.checkbox(
                                                        text=f"{param_config['display_name']} ({param_config['unit']})",
                                                        value=True
                                                    ).props("dark color=secondary dense")

                                                    ui_refs['parameter_checkboxes'][device['name']][param_name] = param_checkbox

                                            # Show/hide parameters based on device selection
                                            def toggle_params(e, container=param_container, checkbox=device_checkbox):
                                                container.set_visibility(checkbox.value)

                                            device_checkbox.on('update:model-value', toggle_params)
                                            param_container.set_visibility(False)
                            else:
                                ui.label("No devices with loggable parameters available").style("color: #888888; font-size: 14px;")

                    render_device_selection()

                    # Control buttons
                    with ui.row().style("gap: 10px; width: 100%; margin-top: 20px;"):
                        def start_logging():
                            """Start a new logging session"""
                            # Get selected devices and parameters
                            selected_devices = []
                            selected_parameters = {}

                            for device in devices_page.devices:
                                device_name = device['name']
                                if device_name in ui_refs['device_checkboxes']:
                                    if ui_refs['device_checkboxes'][device_name].value:
                                        selected_devices.append(device)

                                        # Get selected parameters for this device
                                        params = []
                                        if device_name in ui_refs['parameter_checkboxes']:
                                            for param_name, checkbox in ui_refs['parameter_checkboxes'][device_name].items():
                                                if checkbox.value:
                                                    params.append(param_name)

                                        selected_parameters[device_name] = params

                            if not selected_devices:
                                ui.notify("Please select at least one device", type='warning')
                                return

                            # Get session name
                            session_name = ui_refs['session_name_input'].value
                            if not session_name:
                                session_name = f"Experiment {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                            # Get interval
                            interval = int(ui_refs['interval_input'].value)

                            try:
                                # Start logging session
                                session_id = data_logger.start_session(
                                    session_name=session_name,
                                    devices=selected_devices,
                                    parameters=selected_parameters,
                                    interval_seconds=interval
                                )

                                ui.notify(f"Started logging session: {session_name}", type='positive')

                                # Update button states
                                ui_refs['start_button'].disable()
                                ui_refs['stop_button'].enable()
                                ui_refs['pause_button'].enable()

                            except Exception as e:
                                ui.notify(f"Error starting session: {str(e)}", type='negative')

                        def stop_logging():
                            """Stop the current logging session"""
                            data_logger.stop_session()
                            ui.notify("Stopped logging session", type='info')

                            # Update button states
                            ui_refs['start_button'].enable()
                            ui_refs['stop_button'].disable()
                            ui_refs['pause_button'].disable()

                            # Refresh sessions list
                            refresh_sessions_list()

                        def toggle_pause():
                            """Pause or resume logging"""
                            status = data_logger.get_session_status()

                            if status['active']:
                                if status['status'] == 'Running':
                                    data_logger.pause_session()
                                    ui.notify("Paused logging", type='info')
                                    ui_refs['pause_button'].props("icon=play_arrow")
                                else:
                                    data_logger.resume_session()
                                    ui.notify("Resumed logging", type='info')
                                    ui_refs['pause_button'].props("icon=pause")

                        ui_refs['start_button'] = ui.button("Start Logging", icon="play_arrow", on_click=start_logging).props("color=positive")
                        ui_refs['stop_button'] = ui.button("Stop", icon="stop", on_click=stop_logging).props("color=negative").style("display: none;")
                        ui_refs['pause_button'] = ui.button("Pause", icon="pause", on_click=toggle_pause).props("color=warning").style("display: none;")

                    # Session status display
                    ui.separator().style("margin-top: 20px; margin-bottom: 15px;")
                    ui.label("Session Status:").style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;")

                    ui_refs['status_label'] = ui.label("Not logging").style("color: #888888; font-size: 14px;")
                    ui_refs['elapsed_label'] = ui.label("Elapsed: 00:00:00").style("color: #888888; font-size: 14px;")
                    ui_refs['data_points_label'] = ui.label("Data points: 0").style("color: #888888; font-size: 14px;")

                # Previous Sessions Card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 15px;"):
                        ui.label("Previous Sessions").style("color: white; font-size: 18px; font-weight: bold;")

                        def show_import_dialog():
                            """Show file picker dialog to import CSV"""
                            selected_file = {'path': None}

                            with ui.dialog() as import_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
                                ui.label("Import Session from CSV").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                                file_label = ui.label("No file selected").style("color: #888888; font-size: 14px; margin-bottom: 15px;")

                                def handle_upload(e):
                                    """Handle file upload"""
                                    import shutil

                                    # Save uploaded file temporarily
                                    upload_path = f"data/logs/temp_import_{e.name}"
                                    os.makedirs('data/logs', exist_ok=True)

                                    # Write uploaded content to file
                                    with open(upload_path, 'wb') as f:
                                        f.write(e.content.read())

                                    selected_file['path'] = upload_path
                                    file_label.set_text(f"Selected: {e.name}")
                                    file_label.style("color: #66bb6a;")
                                    ui.notify(f"Loaded: {e.name}", type='positive')

                                ui.upload(
                                    label="Choose CSV File",
                                    on_upload=handle_upload,
                                    auto_upload=True
                                ).props("accept=.csv color=primary").style("width: 100%; margin-bottom: 15px;")

                                ui.separator().style("margin-bottom: 15px;")
                                ui.label("Or enter file path manually:").style("color: white; font-size: 14px; margin-bottom: 10px;")

                                file_path_input = ui.input(
                                    label="CSV File Path",
                                    placeholder="data/logs/Example_Hotplate_Test.csv"
                                ).props("dark outlined").style("width: 100%; margin-bottom: 15px;")

                                with ui.row().style("gap: 10px; width: 100%; justify-content: flex-end;"):
                                    ui.button("Cancel", on_click=import_dialog.close).props("flat color=white")

                                    def do_import():
                                        """Import the CSV file"""
                                        # Use uploaded file if available, otherwise use manual path
                                        filepath = selected_file['path'] if selected_file['path'] else file_path_input.value

                                        if not filepath:
                                            ui.notify("Please select a file or enter a path", type='warning')
                                            return

                                        try:
                                            session_id = data_logger.import_session_from_csv(filepath)
                                            ui.notify(f"Successfully imported session (ID: {session_id})", type='positive')

                                            # Clean up temp file if it was uploaded
                                            if selected_file['path'] and 'temp_import_' in selected_file['path']:
                                                try:
                                                    os.remove(selected_file['path'])
                                                except:
                                                    pass

                                            import_dialog.close()
                                            refresh_sessions_list()
                                        except FileNotFoundError:
                                            ui.notify(f"File not found: {filepath}", type='negative')
                                        except Exception as e:
                                            ui.notify(f"Import error: {str(e)}", type='negative')

                                    ui.button("Import", icon="upload", on_click=do_import).props("color=primary")

                            import_dialog.open()

                        ui.button("Import CSV", icon="upload_file", on_click=show_import_dialog).props("color=primary size=sm")

                    ui_refs['sessions_container'] = ui.column().style("gap: 10px; width: 100%;")

                    def refresh_sessions_list():
                        """Refresh the list of previous sessions"""
                        ui_refs['sessions_container'].clear()

                        with ui_refs['sessions_container']:
                            sessions = data_logger.get_all_sessions()

                            if sessions:
                                for session in sessions[:10]:  # Show last 10 sessions
                                    with ui.card().style("background-color: #444444; padding: 10px; width: 100%;"):
                                        with ui.row().style("width: 100%; justify-content: space-between; align-items: center;"):
                                            with ui.column().style("flex: 1;"):
                                                ui.label(session['name']).style("color: white; font-size: 14px; font-weight: bold;")
                                                ui.label(f"Started: {session['start_time']}").style("color: #888888; font-size: 12px;")

                                                status_color = "#66bb6a" if session['status'] == 'stopped' else "#ffa726"
                                                ui.label(f"Status: {session['status']}").style(f"color: {status_color}; font-size: 12px;")

                                            with ui.row().style("gap: 5px;"):
                                                def export_csv(sid=session['id'], sname=session['name']):
                                                    """Export session to CSV"""
                                                    try:
                                                        # Create exports directory if it doesn't exist
                                                        os.makedirs('data/logs', exist_ok=True)

                                                        # Generate filename
                                                        filename = f"data/logs/{sname.replace(' ', '_')}_{sid}.csv"

                                                        # Export
                                                        data_logger.export_session_to_csv(sid, filename)
                                                        ui.notify(f"Exported to {filename}", type='positive')
                                                    except Exception as e:
                                                        ui.notify(f"Export error: {str(e)}", type='negative')

                                                def view_session(sid=session['id']):
                                                    """View session data"""
                                                    ui.notify("Session viewer coming soon", type='info')

                                                def delete_session_confirm(sid=session['id'], sname=session['name']):
                                                    """Delete session with confirmation"""
                                                    with ui.dialog() as confirm_dialog, ui.card().style("background-color: #333333; padding: 20px;"):
                                                        ui.label(f"Delete session '{sname}'?").style("color: white; font-size: 16px; margin-bottom: 15px;")
                                                        ui.label("This will permanently delete all recorded data.").style("color: #888888; font-size: 14px; margin-bottom: 20px;")

                                                        with ui.row().style("gap: 10px; width: 100%; justify-content: flex-end;"):
                                                            ui.button("Cancel", on_click=confirm_dialog.close).props("flat color=white")

                                                            def do_delete():
                                                                try:
                                                                    data_logger.delete_session(sid)
                                                                    ui.notify(f"Deleted session: {sname}", type='info')
                                                                    confirm_dialog.close()
                                                                    refresh_sessions_list()
                                                                except Exception as e:
                                                                    ui.notify(f"Error deleting: {str(e)}", type='negative')

                                                            ui.button("Delete", icon="delete", on_click=do_delete).props("color=negative")

                                                    confirm_dialog.open()

                                                ui.button(icon="download", on_click=export_csv).props("flat dense color=primary").tooltip("Export to CSV")
                                                ui.button(icon="visibility", on_click=view_session).props("flat dense color=white").tooltip("View Data")
                                                ui.button(icon="delete", on_click=delete_session_confirm).props("flat dense color=negative").tooltip("Delete Session")
                            else:
                                ui.label("No previous sessions").style("color: #888888; font-size: 14px;")

                    refresh_sessions_list()

            # Right column - Live chart
            with ui.column().style("flex: 2; gap: 20px;"):
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; height: 600px;"):
                    ui.label("Live Data Chart").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                    ui_refs['chart_container'] = ui.column().style("width: 100%; height: 500px;")

                    with ui_refs['chart_container']:
                        ui.label("Start a logging session to see live data").style("color: #888888; font-size: 14px; text-align: center; margin-top: 200px;")

        # Status update timer
        def update_status():
            """Update session status display"""
            status = data_logger.get_session_status()

            if status['active']:
                # Update labels
                ui_refs['status_label'].set_text(f"Status: {status['status']}")
                ui_refs['status_label'].style("color: #66bb6a;" if status['status'] == 'Running' else "color: #ffa726;")
                ui_refs['elapsed_label'].set_text(f"Elapsed: {status['elapsed_formatted']}")
                ui_refs['data_points_label'].set_text(f"Data points: {status['data_points']}")

                # Update button visibility
                ui_refs['start_button'].style("display: none;")
                ui_refs['stop_button'].style("display: inline-flex;")
                ui_refs['pause_button'].style("display: inline-flex;")

                # Update pause button icon
                if status['status'] == 'Paused':
                    ui_refs['pause_button'].props("icon=play_arrow")
                else:
                    ui_refs['pause_button'].props("icon=pause")

                # Update chart
                update_chart()
            else:
                # No active session
                ui_refs['status_label'].set_text("Not logging")
                ui_refs['status_label'].style("color: #888888;")
                ui_refs['elapsed_label'].set_text("Elapsed: 00:00:00")
                ui_refs['data_points_label'].set_text("Data points: 0")

                # Update button visibility
                ui_refs['start_button'].style("display: inline-flex;")
                ui_refs['stop_button'].style("display: none;")
                ui_refs['pause_button'].style("display: none;")

        def update_chart():
            """Update the live data chart"""
            status = data_logger.get_session_status()

            if not status['active']:
                return

            # Get recent data (last 10 minutes)
            recent_data = data_logger.get_recent_data(status['session_id'], minutes=10)

            if not recent_data:
                return

            # Organize data by parameter
            data_by_param = {}
            for timestamp, device_name, parameter, value, unit in recent_data:
                key = f"{device_name} - {parameter}"
                if key not in data_by_param:
                    data_by_param[key] = {'timestamps': [], 'values': [], 'unit': unit}

                data_by_param[key]['timestamps'].append(timestamp)
                data_by_param[key]['values'].append(value)

            # Create Plotly chart
            ui_refs['chart_container'].clear()

            with ui_refs['chart_container']:
                if data_by_param:
                    import plotly.graph_objects as go

                    fig = go.Figure()

                    for param_key, param_data in data_by_param.items():
                        fig.add_trace(go.Scatter(
                            x=param_data['timestamps'],
                            y=param_data['values'],
                            mode='lines+markers',
                            name=param_key,
                            line=dict(width=2),
                            marker=dict(size=4)
                        ))

                    fig.update_layout(
                        template='plotly_dark',
                        plot_bgcolor='#333333',
                        paper_bgcolor='#333333',
                        font=dict(color='white'),
                        xaxis_title='Time',
                        yaxis_title='Value',
                        hovermode='x unified',
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        margin=dict(l=50, r=20, t=40, b=50),
                        height=450
                    )

                    ui.plotly(fig).classes('w-full h-full')
                else:
                    ui.label("Waiting for data...").style("color: #888888; font-size: 14px; text-align: center; margin-top: 200px;")

        # Update every 2 seconds
        ui.timer(2.0, update_status)
