# pages/programming.py
from nicegui import ui
import sys
import os
import threading
from tkinter import Tk, filedialog

# Import devices module to access device list
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pages import devices as devices_page
from pages import fume_hood as fume_hood_page
from pages import roboschlenk as roboschlenk_page

# Store user scripts and current code (persist across page navigation)
user_scripts = []
current_code = "# Write your Python script here...\n# Example:\n# device_stirrer_1.set_temperature(50)\n# device_stirrer_1.set_speed(300)"

# Script execution state (persists across page navigation)
script_state = {
    'running': False,
    'thread': None,
    'stop_flag': False,
    'output_log': None,  # Reference to output log UI element
    'run_button': None,  # Reference to run button
    'stop_button': None,  # Reference to stop button
    'code_editor': None,  # Reference to code editor for persistence
    'log_content': [],  # Store log messages for persistence
    'badge_element': None  # Reference to programming badge on sidebar
}

def render_ika_stirrer_actions(device, code_editor):
    """Render quick action buttons for IKA Stirrer"""
    var_name = f"device_{device['name'].lower().replace(' ', '_')}"

    with ui.row().style("gap: 10px; flex-wrap: wrap;"):
        # Set Temperature action
        def show_set_temp_dialog():
            with ui.dialog() as temp_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Set Temperature").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                temp_input = ui.number(label="Temperature (°C)", value=25, min=0, max=400, step=1).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=temp_dialog.close).props("flat color=white")

                    def add_temp_code():
                        temp_value = temp_input.value
                        code_line = f"{var_name}.set_temperature({temp_value})"
                        # Add to end of current code
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        temp_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_temp_code).props("color=primary")

            temp_dialog.open()

        ui.button("Set Temperature", icon="thermostat", on_click=show_set_temp_dialog).props("size=sm")

        # Set Speed action
        def show_set_speed_dialog():
            with ui.dialog() as speed_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Set Stirring Speed").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                speed_input = ui.number(label="Speed (RPM)", value=300, min=0, max=1500, step=10).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=speed_dialog.close).props("flat color=white")

                    def add_speed_code():
                        speed_value = speed_input.value
                        code_line = f"{var_name}.set_speed({speed_value})"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        speed_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_speed_code).props("color=primary")

            speed_dialog.open()

        ui.button("Set Speed", icon="speed", on_click=show_set_speed_dialog).props("size=sm")

        # Get Current Temperature
        def add_get_temperature():
            code_line = f"temp = {var_name}.get_temperature(sensor_type=2)"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        # Get Current Speed
        def add_get_speed():
            code_line = f"speed = {var_name}.get_speed()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Get Temperature", icon="sensors", on_click=add_get_temperature).props("size=sm color=blue")
        ui.button("Get Speed", icon="speed", on_click=add_get_speed).props("size=sm color=blue")

        # Start/Stop Heating
        def add_start_heating():
            code_line = f"{var_name}.start_heating(sensor_type=2)"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        def add_stop_heating():
            code_line = f"{var_name}.stop_heating(sensor_type=2)"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Start Heating", icon="play_arrow", on_click=add_start_heating).props("size=sm color=green")
        ui.button("Stop Heating", icon="stop", on_click=add_stop_heating).props("size=sm color=red")

        # Start/Stop Stirring
        def add_start_stirring():
            code_line = f"{var_name}.start_stirring()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        def add_stop_stirring():
            code_line = f"{var_name}.stop_stirring()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Start Stirring", icon="play_arrow", on_click=add_start_stirring).props("size=sm color=green")
        ui.button("Stop Stirring", icon="stop", on_click=add_stop_stirring).props("size=sm color=red")

def render_azura_pump_actions(device, code_editor):
    """Render quick action buttons for Azura Pump"""
    var_name = f"device_{device['name'].lower().replace(' ', '_')}"

    with ui.row().style("gap: 10px; flex-wrap: wrap;"):
        # Set Flow Rate action
        def show_set_flow_dialog():
            with ui.dialog() as flow_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Set Flow Rate").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                flow_input = ui.number(label="Flow Rate (µL/min)", value=5000, min=0, max=50000, step=100).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=flow_dialog.close).props("flat color=white")

                    def add_flow_code():
                        flow_value = flow_input.value
                        code_line = f"{var_name}.set_flow({flow_value})"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        flow_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_flow_code).props("color=primary")

            flow_dialog.open()

        ui.button("Set Flow Rate", icon="water_drop", on_click=show_set_flow_dialog).props("size=sm")

        # Get Current Flow Rate
        def add_get_flow():
            code_line = f"flow = {var_name}.get_flow()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Get Flow Rate", icon="sensors", on_click=add_get_flow).props("size=sm color=blue")

        # Get Pressure
        def add_get_pressure():
            code_line = f"pressure = {var_name}.get_pressure()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Get Pressure", icon="speed", on_click=add_get_pressure).props("size=sm color=blue")

        # Start Pump
        def add_start_pump():
            code_line = f"{var_name}.start()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Start Pump", icon="play_arrow", on_click=add_start_pump).props("size=sm color=green")

        # Stop Pump
        def add_stop_pump():
            code_line = f"{var_name}.stop()"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Stop Pump", icon="stop", on_click=add_stop_pump).props("size=sm color=red")

        # Set Head Type action
        def show_set_head_dialog():
            with ui.dialog() as head_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Set Pump Head Type").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                head_options = ui.radio(['10 mL', '50 mL'], value='10 mL').props("dark").style("color: white; margin-bottom: 10px;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=head_dialog.close).props("flat color=white")

                    def add_head_code():
                        head_value = 10 if head_options.value == '10 mL' else 50
                        code_line = f"{var_name}.set_head_type({head_value})"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        head_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_head_code).props("color=primary")

            head_dialog.open()

        ui.button("Set Head Type", icon="settings", on_click=show_set_head_dialog).props("size=sm color=purple")

def render_fume_hood_actions(fume_hood, code_editor):
    """Render quick action buttons for Fume Hood"""
    var_name = f"fume_hood_{fume_hood['name'].lower().replace(' ', '_')}"

    with ui.row().style("gap: 10px; flex-wrap: wrap;"):
        # Check if Sash is Open
        def add_is_sash_open():
            code_line = f"sash_open = {var_name}['sash_open']"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_line + '\n')
            ui.notify(f"Added: {code_line}", type='positive')

        ui.button("Get Sash Status", icon="door_front", on_click=add_is_sash_open).props("size=sm color=blue")

        # If Sash is Open
        def add_if_sash_open():
            code_lines = f"if {var_name}['sash_open']:\n    # Sash is open\n    pass"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_lines + '\n')
            ui.notify("Added if sash is open condition", type='positive')

        ui.button("If Sash Open", icon="arrow_upward", on_click=add_if_sash_open).props("size=sm color=orange")

        # If Sash is Closed
        def add_if_sash_closed():
            code_lines = f"if not {var_name}['sash_open']:\n    # Sash is closed\n    pass"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_lines + '\n')
            ui.notify("Added if sash is closed condition", type='positive')

        ui.button("If Sash Closed", icon="arrow_downward", on_click=add_if_sash_closed).props("size=sm color=green")

        # While Sash is Open
        def add_while_sash_open():
            code_lines = f"while {var_name}['sash_open']:\n    # Loop while sash is open\n    pass"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_lines + '\n')
            ui.notify("Added while sash is open loop", type='positive')

        ui.button("While Sash Open", icon="loop", on_click=add_while_sash_open).props("size=sm color=purple")

        # While Sash is Closed
        def add_while_sash_closed():
            code_lines = f"while not {var_name}['sash_open']:\n    # Loop while sash is closed\n    pass"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_lines + '\n')
            ui.notify("Added while sash is closed loop", type='positive')

        ui.button("While Sash Closed", icon="loop", on_click=add_while_sash_closed).props("size=sm color=purple")

def render_roboschlenk_actions(code_editor):
    """Render quick action buttons for RoboSchlenk"""
    with ui.row().style("gap: 10px; flex-wrap: wrap;"):
        # Move to CLOSED
        def show_closed_dialog():
            with ui.dialog() as closed_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Move to CLOSED").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=closed_dialog.close).props("flat color=white")

                    def add_closed_code():
                        motor = motor_select.value
                        code_line = f"roboschlenk.move_to_closed('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        closed_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_closed_code).props("color=primary")

            closed_dialog.open()

        ui.button("Move to CLOSED", icon="lock", on_click=show_closed_dialog).props("size=sm").style("border: 2px solid #10b981; color: #10b981;")

        # Move to GAS
        def show_gas_dialog():
            with ui.dialog() as gas_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Move to GAS").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=gas_dialog.close).props("flat color=white")

                    def add_gas_code():
                        motor = motor_select.value
                        code_line = f"roboschlenk.move_to_gas('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        gas_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_gas_code).props("color=primary")

            gas_dialog.open()

        ui.button("Move to GAS", icon="air", on_click=show_gas_dialog).props("size=sm").style("border: 2px solid #3b82f6; color: #3b82f6;")

        # Move to VACUUM
        def show_vacuum_dialog():
            with ui.dialog() as vacuum_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Move to VACUUM").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=vacuum_dialog.close).props("flat color=white")

                    def add_vacuum_code():
                        motor = motor_select.value
                        code_line = f"roboschlenk.move_to_vacuum('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        vacuum_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_vacuum_code).props("color=primary")

            vacuum_dialog.open()

        ui.button("Move to VACUUM", icon="science", on_click=show_vacuum_dialog).props("size=sm").style("border: 2px solid #f97316; color: #f97316;")

        # Move to Custom Angle
        def show_angle_dialog():
            with ui.dialog() as angle_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Move to Custom Angle").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%; margin-bottom: 10px;")

                angle_input = ui.number(label="Angle (degrees)", value=45, min=0, max=360, step=1).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=angle_dialog.close).props("flat color=white")

                    def add_angle_code():
                        motor = motor_select.value
                        angle = angle_input.value
                        code_line = f"roboschlenk.move_to_angle('{motor}', {angle})"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        angle_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_angle_code).props("color=primary")

            angle_dialog.open()

        ui.button("Move to Angle", icon="rotate_90_degrees_ccw", on_click=show_angle_dialog).props("size=sm color=purple")

        # Get Motor Status
        def show_status_dialog():
            with ui.dialog() as status_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Get Motor Status").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=status_dialog.close).props("flat color=white")

                    def add_status_code():
                        motor = motor_select.value
                        code_line = f"status = roboschlenk.get_motor_status('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        status_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_status_code).props("color=primary")

            status_dialog.open()

        ui.button("Get Status", icon="info", on_click=show_status_dialog).props("size=sm color=blue")

        # Wait for Motor
        def show_wait_dialog():
            with ui.dialog() as wait_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Wait for Motor to Stop").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=wait_dialog.close).props("flat color=white")

                    def add_wait_code():
                        motor = motor_select.value
                        code_line = f"roboschlenk.wait_for_motor('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        wait_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_wait_code).props("color=primary")

            wait_dialog.open()

        ui.button("Wait for Motor", icon="hourglass_empty", on_click=show_wait_dialog).props("size=sm color=orange")

        # Enable/Disable Motor
        def show_enable_dialog():
            with ui.dialog() as enable_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Enable/Disable Motor").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%; margin-bottom: 10px;")

                action_select = ui.select(
                    options=['Enable', 'Disable'],
                    label="Action",
                    value='Enable'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=enable_dialog.close).props("flat color=white")

                    def add_enable_code():
                        motor = motor_select.value
                        action = 'enable_motor' if action_select.value == 'Enable' else 'disable_motor'
                        code_line = f"roboschlenk.{action}('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        enable_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_enable_code).props("color=primary")

            enable_dialog.open()

        ui.button("Enable/Disable", icon="power_settings_new", on_click=show_enable_dialog).props("size=sm color=grey")

        # Stop Motor
        def show_stop_dialog():
            with ui.dialog() as stop_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Stop Motor").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                motor_select = ui.select(
                    options=['A', 'B', 'C', 'D'],
                    label="Select Motor",
                    value='A'
                ).props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=stop_dialog.close).props("flat color=white")

                    def add_stop_code():
                        motor = motor_select.value
                        code_line = f"roboschlenk.stop_motor('{motor}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        stop_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_stop_code).props("color=primary")

            stop_dialog.open()

        ui.button("Stop Motor", icon="stop_circle", on_click=show_stop_dialog).props("size=sm color=red")

def render_python_basics_actions(code_editor):
    """Render quick action buttons for basic Python operations"""
    with ui.row().style("gap: 10px; flex-wrap: wrap;"):
        # Create Variable
        def show_create_variable_dialog():
            with ui.dialog() as var_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Create Variable").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                var_name_input = ui.input(label="Variable Name", placeholder="my_variable").props("dark outlined").style("width: 100%; margin-bottom: 10px;")
                var_value_input = ui.input(label="Value", placeholder="42 or 'text'").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=var_dialog.close).props("flat color=white")

                    def add_variable_code():
                        var_name = var_name_input.value
                        var_value = var_value_input.value
                        if not var_name:
                            ui.notify("Please enter a variable name", type='warning')
                            return
                        code_line = f"{var_name} = {var_value}"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        var_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_variable_code).props("color=primary")

            var_dialog.open()

        ui.button("Create Variable", icon="add_circle", on_click=show_create_variable_dialog).props("size=sm color=blue")

        # Print Statement
        def show_print_dialog():
            with ui.dialog() as print_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Print Statement").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                print_input = ui.input(label="Message", placeholder="Enter message or variable").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=print_dialog.close).props("flat color=white")

                    def add_print_code():
                        message = print_input.value
                        if not message:
                            ui.notify("Please enter a message", type='warning')
                            return
                        # Check if it's a variable (no quotes) or a string (add quotes)
                        if message.startswith('"') or message.startswith("'") or message.replace('_', '').isalnum():
                            code_line = f"print({message})"
                        else:
                            code_line = f"print('{message}')"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added: {code_line}", type='positive')
                        print_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_print_code).props("color=primary")

            print_dialog.open()

        ui.button("Print", icon="print", on_click=show_print_dialog).props("size=sm color=blue")

        # If Statement
        def show_if_dialog():
            with ui.dialog() as if_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("If Statement").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                condition_input = ui.input(label="Condition", placeholder="temp > 50").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=if_dialog.close).props("flat color=white")

                    def add_if_code():
                        condition = condition_input.value
                        if not condition:
                            ui.notify("Please enter a condition", type='warning')
                            return
                        code_lines = f"if {condition}:\n    # Add your code here\n    pass"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_lines + '\n')
                        ui.notify(f"Added if statement", type='positive')
                        if_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_if_code).props("color=primary")

            if_dialog.open()

        ui.button("If Statement", icon="compare_arrows", on_click=show_if_dialog).props("size=sm color=purple")

        # While Loop
        def show_while_dialog():
            with ui.dialog() as while_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("While Loop").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                condition_input = ui.input(label="Condition", placeholder="temp < 100").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=while_dialog.close).props("flat color=white")

                    def add_while_code():
                        condition = condition_input.value
                        if not condition:
                            ui.notify("Please enter a condition", type='warning')
                            return
                        code_lines = f"while {condition}:\n    # Add your code here\n    pass"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_lines + '\n')
                        ui.notify(f"Added while loop", type='positive')
                        while_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_while_code).props("color=primary")

            while_dialog.open()

        ui.button("While Loop", icon="loop", on_click=show_while_dialog).props("size=sm color=purple")

        # For Loop
        def show_for_dialog():
            with ui.dialog() as for_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("For Loop").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                var_input = ui.input(label="Variable Name", placeholder="i", value="i").props("dark outlined").style("width: 100%; margin-bottom: 10px;")
                range_input = ui.input(label="Range", placeholder="range(10) or [1, 2, 3]", value="range(10)").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=for_dialog.close).props("flat color=white")

                    def add_for_code():
                        var_name = var_input.value
                        range_val = range_input.value
                        if not var_name or not range_val:
                            ui.notify("Please fill all fields", type='warning')
                            return
                        code_lines = f"for {var_name} in {range_val}:\n    # Add your code here\n    pass"
                        current_code = code_editor.value if code_editor.value else ""
                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_editor.set_value(current_code + code_lines + '\n')
                        ui.notify(f"Added for loop", type='positive')
                        for_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_for_code).props("color=primary")

            for_dialog.open()

        ui.button("For Loop", icon="repeat", on_click=show_for_dialog).props("size=sm color=purple")

        # Wait/Delay
        def show_wait_dialog():
            with ui.dialog() as wait_dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 300px;"):
                ui.label("Wait/Delay").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                wait_input = ui.input(label="Wait Time (seconds)", placeholder="5", value="5").props("dark outlined").style("width: 100%;")

                with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 15px;"):
                    ui.button("Cancel", on_click=wait_dialog.close).props("flat color=white")

                    def add_wait_code():
                        wait_value = wait_input.value
                        if not wait_value:
                            ui.notify("Please enter a wait time", type='warning')
                            return

                        current_code = code_editor.value if code_editor.value else ""

                        # Check if import time already exists
                        if 'import time' not in current_code:
                            if current_code and not current_code.endswith('\n'):
                                current_code += '\n'
                            current_code += 'import time\n'

                        if current_code and not current_code.endswith('\n'):
                            current_code += '\n'
                        code_line = f"time.sleep({wait_value})  # Wait {wait_value} seconds"
                        code_editor.set_value(current_code + code_line + '\n')
                        ui.notify(f"Added wait: {wait_value} seconds", type='positive')
                        wait_dialog.close()

                    ui.button("Add Code", icon="add", on_click=add_wait_code).props("color=primary")

            wait_dialog.open()

        ui.button("Wait/Delay", icon="schedule", on_click=show_wait_dialog).props("size=sm color=orange")

        # Check Stop Request (for cooperative stopping in long loops)
        def add_stop_check():
            code_lines = "if script_stop_requested():\n    break  # Exit loop if stop was requested"
            current_code = code_editor.value if code_editor.value else ""
            if current_code and not current_code.endswith('\n'):
                current_code += '\n'
            code_editor.set_value(current_code + code_lines + '\n')
            ui.notify("Added stop check", type='positive')

        ui.button("Check Stop", icon="exit_to_app", on_click=add_stop_check).props("size=sm color=red").style("margin-left: 10px;")

def render():
    """Render the programming page content"""
    global current_code

    with ui.column().style("padding: 20px; padding-bottom: 80px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Introduction
        ui.label("Python Programming").style("color: white; font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        ui.label("Write Python scripts to control your devices. Click device actions to add code, or write manually.").style("color: #888888; font-size: 14px; margin-bottom: 20px;")

        # Script editor section (moved to top so we can reference it in quick actions)
        with ui.row().style("width: 100%; gap: 20px; align-items: flex-start;"):
            # Left side - Quick Actions
            with ui.column().style("flex: 1; gap: 20px;"):
                # Python Basics card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Python Basics").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                    ui.label("Add basic Python constructs").style("color: #888888; font-size: 13px; margin-bottom: 15px;")

                    # Create code editor reference placeholder (will be set below)
                    code_editor_ref = {'editor': None}

                    # Render Python basics actions with proxy
                    class EditorProxy:
                        @property
                        def value(self):
                            return code_editor_ref['editor'].value if code_editor_ref['editor'] else ""
                        def set_value(self, val):
                            if code_editor_ref['editor']:
                                code_editor_ref['editor'].set_value(val)

                    render_python_basics_actions(EditorProxy())

                # Device Actions card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Device Actions").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                    ui.label("Control your devices").style("color: #888888; font-size: 13px; margin-bottom: 15px;")

                    if devices_page.devices:
                        with ui.column().style("gap: 10px; width: 100%;"):
                            for device in devices_page.devices:
                                is_connected = device.get('connection_state', {}).get('connected', False)

                                with ui.expansion(f"{device['name']} ({device['type']})", icon="devices").props("dense").style("background-color: #444444; margin-bottom: 5px;"):
                                    with ui.column().style("gap: 10px; padding: 10px;"):
                                        # Connection status
                                        if is_connected:
                                            ui.label("✓ Connected").style("color: #66bb6a; font-size: 14px; font-weight: bold;")
                                        else:
                                            ui.label("✗ Not Connected").style("color: #ef5350; font-size: 14px; font-weight: bold;")

                                        ui.label(f"Variable: device_{device['name'].lower().replace(' ', '_')}").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                                        # Device-specific quick actions - pass reference
                                        if device['type'] == 'ika_stirrer':
                                            # Create wrapper that will use the editor when available
                                            def render_actions(dev=device, ref=code_editor_ref):
                                                class EditorProxy:
                                                    @property
                                                    def value(self):
                                                        return ref['editor'].value if ref['editor'] else ""
                                                    def set_value(self, val):
                                                        if ref['editor']:
                                                            ref['editor'].set_value(val)
                                                render_ika_stirrer_actions(dev, EditorProxy())
                                            render_actions()
                                        elif device['type'] == 'azura_pump':
                                            # Create wrapper that will use the editor when available
                                            def render_actions(dev=device, ref=code_editor_ref):
                                                class EditorProxy:
                                                    @property
                                                    def value(self):
                                                        return ref['editor'].value if ref['editor'] else ""
                                                    def set_value(self, val):
                                                        if ref['editor']:
                                                            ref['editor'].set_value(val)
                                                render_azura_pump_actions(dev, EditorProxy())
                                            render_actions()
                                        elif device['type'] == 'edwards_tic':
                                            ui.label("Edwards TIC controls coming soon...").style("color: #888888; font-size: 13px;")
                    else:
                        ui.label("No devices configured. Add devices from the Devices page first.").style("color: #888888; font-size: 14px;")

                # Fume Hood Actions card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Fume Hood Actions").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                    ui.label("Monitor sash status").style("color: #888888; font-size: 13px; margin-bottom: 15px;")

                    if fume_hood_page.fume_hoods:
                        with ui.column().style("gap: 10px; width: 100%;"):
                            for fume_hood in fume_hood_page.fume_hoods:
                                sash_status = "Open" if fume_hood.get('sash_open', False) else "Closed"
                                sash_color = "#ef5350" if fume_hood.get('sash_open', False) else "#66bb6a"

                                with ui.expansion(f"{fume_hood['name']} - Sash: {sash_status}", icon="window").props("dense").style("background-color: #444444; margin-bottom: 5px;"):
                                    with ui.column().style("gap: 10px; padding: 10px;"):
                                        # Sash status
                                        ui.label(f"Sash Status: {sash_status}").style(f"color: {sash_color}; font-size: 14px; font-weight: bold;")

                                        ui.label(f"Variable: fume_hood_{fume_hood['name'].lower().replace(' ', '_')}").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                                        # Fume hood-specific quick actions - pass reference
                                        def render_actions(hood=fume_hood, ref=code_editor_ref):
                                            class EditorProxy:
                                                @property
                                                def value(self):
                                                    return ref['editor'].value if ref['editor'] else ""
                                                def set_value(self, val):
                                                    if ref['editor']:
                                                        ref['editor'].set_value(val)
                                            render_fume_hood_actions(hood, EditorProxy())
                                        render_actions()
                    else:
                        ui.label("No fume hoods configured. Add fume hoods from the Fume Hood page first.").style("color: #888888; font-size: 14px;")

                # RoboSchlenk Actions card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("RoboSchlenk Actions").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
                    ui.label("Control Schlenk line taps").style("color: #888888; font-size: 13px; margin-bottom: 15px;")

                    if roboschlenk_page.roboschlenk_state['connected']:
                        with ui.column().style("gap: 10px; width: 100%;"):
                            # Connected status
                            ui.label("✓ Controller Connected").style("color: #66bb6a; font-size: 14px; font-weight: bold;")
                            ui.label("Variable: roboschlenk").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                            # RoboSchlenk quick actions
                            def render_actions(ref=code_editor_ref):
                                class EditorProxy:
                                    @property
                                    def value(self):
                                        return ref['editor'].value if ref['editor'] else ""
                                    def set_value(self, val):
                                        if ref['editor']:
                                            ref['editor'].set_value(val)
                                render_roboschlenk_actions(EditorProxy())
                            render_actions()
                    else:
                        ui.label("✗ Controller Not Connected").style("color: #ef5350; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
                        ui.label("Connect the RoboSchlenk controller from the RoboSchlenk page to use these actions.").style("color: #888888; font-size: 14px;")

            # Middle - Script editor and output log
            with ui.column().style("flex: 2; gap: 20px;"):
                # Script editor card
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; flex: 1;"):
                    ui.label("Script Editor").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                    # Save code from previous editor instance if it exists
                    global current_code
                    if script_state['code_editor'] is not None:
                        try:
                            # Try to get the value from the previous editor
                            current_code = script_state['code_editor'].value
                        except:
                            # If the previous editor is no longer accessible, use stored value
                            pass

                    # Code editor with syntax highlighting - use persisted code
                    code_editor = ui.codemirror(value=current_code,
                                               language="python",
                                               theme="dark").style("width: 100%; height: 500px;").props("outlined")

                    # Store reference for quick actions and global persistence
                    code_editor_ref['editor'] = code_editor
                    script_state['code_editor'] = code_editor

                    # Add change handler to persist code
                    def save_current_code():
                        global current_code
                        current_code = code_editor.value

                    code_editor.on('update:model-value', save_current_code)

                    # Control buttons
                    with ui.row().style("gap: 10px; margin-top: 10px;"):
                        # Create UI references for buttons
                        run_btn_ref = {'button': None}
                        stop_btn_ref = {'button': None}

                        def run_script():
                            if script_state['running']:
                                ui.notify("A script is already running", type='warning')
                                return

                            script_code = code_editor.value
                            if not script_code or script_code.strip() == "":
                                ui.notify("Please enter a script to run", type='warning')
                                return

                            # Reset stop flag
                            script_state['stop_flag'] = False
                            script_state['running'] = True

                            # Update button states
                            if run_btn_ref['button']:
                                run_btn_ref['button'].props("disable")
                            if stop_btn_ref['button']:
                                stop_btn_ref['button'].props(remove="disable")

                            # Show the badge on the Programming sidebar button
                            if script_state['badge_element']:
                                script_state['badge_element'].style("display: block;")

                            # Create execution environment with available devices
                            def script_print(*args, **kwargs):
                                """Custom print function that outputs to log"""
                                message = f"> {' '.join(map(str, args))}"
                                script_state['log_content'].append(message)
                                if script_state['output_log']:
                                    script_state['output_log'].push(message)

                            exec_globals = {
                                'ui': ui,
                                'print': script_print,
                                'script_stop_requested': lambda: script_state['stop_flag'],  # Allow scripts to check if stop was requested
                            }

                            # Add connected devices to environment
                            for device in devices_page.devices:
                                if device.get('connection_state', {}).get('connected', False) and 'driver' in device:
                                    var_name = f"device_{device['name'].lower().replace(' ', '_')}"
                                    exec_globals[var_name] = device['driver']

                            # Add fume hoods to environment (for sash monitoring)
                            for fume_hood in fume_hood_page.fume_hoods:
                                var_name = f"fume_hood_{fume_hood['name'].lower().replace(' ', '_')}"
                                exec_globals[var_name] = fume_hood

                            # Add RoboSchlenk controller to environment
                            if roboschlenk_page.roboschlenk_state['connected'] and roboschlenk_page.roboschlenk_state['controller']:
                                import io
                                import contextlib

                                class RoboSchlenk:
                                    """RoboSchlenk wrapper for programming interface"""
                                    def __init__(self):
                                        self.controller = roboschlenk_page.roboschlenk_state['controller']

                                    def _suppress_controller_output(self, func, *args, **kwargs):
                                        """Suppress stdout from controller operations to avoid cluttering script output"""
                                        # Capture stdout temporarily to filter out controller debug messages
                                        old_stdout = sys.stdout
                                        sys.stdout = io.StringIO()
                                        try:
                                            result = func(*args, **kwargs)
                                        finally:
                                            sys.stdout = old_stdout
                                        return result

                                    def move_to_closed(self, motor):
                                        """Move motor to CLOSED position (0°) and wait for completion"""
                                        result = self._suppress_controller_output(self.controller.move_to_closed, motor)
                                        if result:
                                            # Give motor time to start moving
                                            import time
                                            time.sleep(0.2)
                                            # Wait for movement to complete
                                            self.controller.wait_for_motor(motor, timeout=30.0)
                                        return result

                                    def move_to_gas(self, motor):
                                        """Move motor to GAS position (90°) and wait for completion"""
                                        result = self._suppress_controller_output(self.controller.move_to_gas, motor)
                                        if result:
                                            # Give motor time to start moving
                                            import time
                                            time.sleep(0.2)
                                            # Wait for movement to complete
                                            self.controller.wait_for_motor(motor, timeout=30.0)
                                        return result

                                    def move_to_vacuum(self, motor):
                                        """Move motor to VACUUM position (270°) and wait for completion"""
                                        result = self._suppress_controller_output(self.controller.move_to_vacuum, motor)
                                        if result:
                                            # Give motor time to start moving
                                            import time
                                            time.sleep(0.2)
                                            # Wait for movement to complete
                                            self.controller.wait_for_motor(motor, timeout=30.0)
                                        return result

                                    def move_to_angle(self, motor, angle):
                                        """Move motor to specific angle (0-360°) and wait for completion"""
                                        result = self._suppress_controller_output(self.controller.move_to_angle, motor, angle)
                                        if result:
                                            # Give motor time to start moving
                                            import time
                                            time.sleep(0.2)
                                            # Wait for movement to complete
                                            self.controller.wait_for_motor(motor, timeout=30.0)
                                        return result

                                    def get_motor_status(self, motor):
                                        """Get current motor status"""
                                        return self.controller.get_motor_status(motor)

                                    def wait_for_motor(self, motor, timeout=30.0):
                                        """Wait for motor to stop moving"""
                                        return self.controller.wait_for_motor(motor, timeout)

                                    def enable_motor(self, motor):
                                        """Enable motor driver"""
                                        return self._suppress_controller_output(self.controller.enable_motor, motor)

                                    def disable_motor(self, motor):
                                        """Disable motor driver"""
                                        return self._suppress_controller_output(self.controller.disable_motor, motor)

                                    def stop_motor(self, motor):
                                        """Stop motor immediately"""
                                        return self._suppress_controller_output(self.controller.stop_motor, motor)

                                exec_globals['roboschlenk'] = RoboSchlenk()

                            def execute_in_thread():
                                try:
                                    message = "--- Running script ---"
                                    script_state['log_content'].append(message)
                                    if script_state['output_log']:
                                        script_state['output_log'].push(message)

                                    # Wrap exec in a way that periodically checks stop flag
                                    import sys
                                    import time

                                    # Custom trace function to check stop flag
                                    def trace_function(frame, event, arg):
                                        if script_state['stop_flag']:
                                            raise KeyboardInterrupt("Script stopped by user")
                                        return trace_function

                                    # Set the trace function
                                    sys.settrace(trace_function)

                                    try:
                                        exec(script_code, exec_globals)
                                    finally:
                                        # Remove trace function
                                        sys.settrace(None)

                                    if script_state['stop_flag']:
                                        message = "--- Script stopped by user ---"
                                        script_state['log_content'].append(message)
                                        if script_state['output_log']:
                                            script_state['output_log'].push(message)
                                        ui.notify("Script stopped", type='warning')
                                    else:
                                        message = "--- Script completed successfully ---"
                                        script_state['log_content'].append(message)
                                        if script_state['output_log']:
                                            script_state['output_log'].push(message)
                                        ui.notify("Script executed successfully", type='positive')
                                except KeyboardInterrupt:
                                    message = "--- Script stopped by user ---"
                                    script_state['log_content'].append(message)
                                    if script_state['output_log']:
                                        script_state['output_log'].push(message)
                                    ui.notify("Script stopped", type='warning')
                                except Exception as e:
                                    message = f"ERROR: {str(e)}"
                                    script_state['log_content'].append(message)
                                    if script_state['output_log']:
                                        script_state['output_log'].push(message)
                                    ui.notify(f"Script error: {str(e)}", type='negative')
                                finally:
                                    script_state['running'] = False
                                    script_state['thread'] = None
                                    # Re-enable run button, disable stop button
                                    if script_state['run_button']:
                                        script_state['run_button'].props(remove="disable")
                                    if script_state['stop_button']:
                                        script_state['stop_button'].props("disable")
                                    # Hide the badge on the Programming sidebar button
                                    if script_state['badge_element']:
                                        script_state['badge_element'].style("display: none;")

                            # Start execution in background thread
                            script_state['thread'] = threading.Thread(target=execute_in_thread, daemon=True)
                            script_state['thread'].start()

                        def stop_script():
                            if not script_state['running']:
                                ui.notify("No script is running", type='warning')
                                return

                            script_state['stop_flag'] = True
                            message = "--- Stop requested, waiting for script to exit ---"
                            script_state['log_content'].append(message)
                            output_log.push(message)
                            ui.notify("Stopping script...", type='info')

                        def clear_script():
                            global current_code
                            code_editor.value = ""
                            current_code = ""
                            ui.notify("Script cleared", type='info')

                        def save_script_to_file():
                            """Save script to file using OS file explorer"""
                            script_code = code_editor.value
                            if not script_code or script_code.strip() == "":
                                ui.notify("Cannot save empty script", type='warning')
                                return

                            try:
                                # Create hidden Tkinter root window
                                root = Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)

                                # Show save file dialog
                                filepath = filedialog.asksaveasfilename(
                                    title="Save Python Script",
                                    defaultextension=".py",
                                    filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                                    initialdir=os.path.expanduser("~")
                                )

                                root.destroy()

                                if filepath:
                                    # Save the script to file
                                    with open(filepath, 'w', encoding='utf-8') as f:
                                        f.write(script_code)
                                    ui.notify(f"Script saved to {os.path.basename(filepath)}", type='positive')
                            except Exception as e:
                                ui.notify(f"Error saving file: {str(e)}", type='negative')

                        def load_script_from_file():
                            """Load script from file using OS file explorer"""
                            try:
                                # Create hidden Tkinter root window
                                root = Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)

                                # Show open file dialog
                                filepath = filedialog.askopenfilename(
                                    title="Load Python Script",
                                    filetypes=[("Python files", "*.py"), ("All files", "*.*")],
                                    initialdir=os.path.expanduser("~")
                                )

                                root.destroy()

                                if filepath:
                                    # Load the script from file
                                    with open(filepath, 'r', encoding='utf-8') as f:
                                        loaded_code = f.read()

                                    global current_code
                                    current_code = loaded_code
                                    code_editor.set_value(loaded_code)
                                    ui.notify(f"Script loaded from {os.path.basename(filepath)}", type='positive')
                            except Exception as e:
                                ui.notify(f"Error loading file: {str(e)}", type='negative')

                        # Create buttons and store in global state
                        run_btn_ref['button'] = ui.button("Run Script", icon="play_arrow", on_click=run_script).props("color=primary" + (" disable" if script_state['running'] else ""))
                        stop_btn_ref['button'] = ui.button("Stop Script", icon="stop", on_click=stop_script).props("color=negative" + ("" if script_state['running'] else " disable"))

                        # Store references globally for access from background thread
                        script_state['run_button'] = run_btn_ref['button']
                        script_state['stop_button'] = stop_btn_ref['button']

                        ui.button("Clear", icon="delete", on_click=clear_script).props("color=secondary")
                        ui.button("Save to File", icon="save", on_click=save_script_to_file).props("color=secondary")
                        ui.button("Load from File", icon="folder_open", on_click=load_script_from_file).props("color=secondary")

                # Output log (below script editor)
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
                    ui.label("Output Log").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                    output_log = ui.log(max_lines=50).style("width: 100%; height: 200px; background-color: #222222; color: #66bb6a; font-family: monospace; padding: 10px; border-radius: 5px;")

                    # Restore persisted log content
                    for message in script_state['log_content']:
                        output_log.push(message)

                    # Store output log reference globally for background thread access
                    script_state['output_log'] = output_log

                    def clear_log():
                        output_log.clear()
                        script_state['log_content'].clear()
                        ui.notify("Log cleared", type='info')

                    ui.button("Clear Log", icon="delete", on_click=clear_log).props("flat color=white").style("margin-top: 10px;")
