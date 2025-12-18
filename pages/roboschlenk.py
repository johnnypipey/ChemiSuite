# pages/roboschlenk.py
from nicegui import ui
import sys
import os
import importlib.util

# Import config module
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'roboschlenk', 'config.py')
spec = importlib.util.spec_from_file_location("roboschlenk_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
get_config = config_module.get_config
save_config = config_module.save_config
is_configured = config_module.is_configured

# Import motor_controller module
motor_controller_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'roboschlenk', 'motor_controller.py')
spec = importlib.util.spec_from_file_location("roboschlenk_motor_controller", motor_controller_path)
motor_controller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motor_controller_module)
MotorController = motor_controller_module.MotorController

import serial.tools.list_ports
import asyncio
from typing import Optional, Dict

# Global state
roboschlenk_state = {
    'controller': None,
    'connected': False,
    'displays': {
        'A': {'serial': None, 'connected': False},
        'B': {'serial': None, 'connected': False},
        'C': {'serial': None, 'connected': False},
        'D': {'serial': None, 'connected': False},
    },
    'motor_panels': {},
    'status_timer': None,
    'auto_send': True,
    'content_container': None,
}

def get_available_com_ports():
    """Get list of available COM ports"""
    ports = serial.tools.list_ports.comports()
    return [f"{port.device} - {port.description}" for port in ports]

def show_setup_wizard():
    """Show configuration wizard dialog"""
    config = get_config()
    com_ports = get_available_com_ports()

    # Create a container for the wizard content that can be refreshed
    wizard_state = {
        'container': None,
        'motor_controller_port': config.get('motor_controller_port'),
        'display_ports': config.get('display_ports', {}).copy()
    }

    def render_wizard_content():
        """Render the wizard content (can be called to refresh)"""
        # Motor Controller Port
        with ui.card().style("background-color: #444444; padding: 20px; margin-bottom: 20px;"):
            ui.label("Motor Controller").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
            ui.label("Select the COM port for the ESP32 motor controller:").style("color: #cccccc; font-size: 14px; margin-bottom: 10px;")

            motor_port_select = ui.select(
                options=com_ports,
                value=None,
                label="Motor Controller Port"
            ).style("width: 100%;").props("dark outlined")

            if wizard_state['motor_controller_port']:
                # Try to find matching port in list
                for port in com_ports:
                    if port.startswith(wizard_state['motor_controller_port']):
                        motor_port_select.value = port
                        break

            def on_motor_port_change(e):
                if e.value:
                    wizard_state['motor_controller_port'] = e.value.split(' - ')[0]
                else:
                    wizard_state['motor_controller_port'] = None

            motor_port_select.on_value_change(on_motor_port_change)
            if motor_port_select.value:
                wizard_state['motor_controller_port'] = motor_port_select.value.split(' - ')[0]

        # LCD Display Ports
        with ui.card().style("background-color: #444444; padding: 20px;"):
            ui.label("LCD Displays").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")
            ui.label("Select COM ports for each motor's LCD display (optional):").style("color: #cccccc; font-size: 14px; margin-bottom: 15px;")

            display_selects = {}
            for motor in ['A', 'B', 'C', 'D']:
                with ui.row().style("width: 100%; align-items: center; margin-bottom: 10px; gap: 10px;"):
                    ui.label(f"Motor {motor}:").style("color: white; font-size: 14px; min-width: 80px;")

                    display_select = ui.select(
                        options=['None'] + com_ports,
                        value='None',
                        label=f"Display {motor} Port"
                    ).style("flex: 1;").props("dark outlined")

                    display_selects[motor] = display_select

                    # Set current value if exists
                    if wizard_state['display_ports'].get(motor):
                        for port in com_ports:
                            if port.startswith(wizard_state['display_ports'][motor]):
                                display_select.value = port
                                break

                    def on_display_port_change(e, m=motor):
                        if e.value and e.value != 'None':
                            wizard_state['display_ports'][m] = e.value.split(' - ')[0]
                        else:
                            wizard_state['display_ports'][m] = None

                    display_select.on_value_change(on_display_port_change)

                    # Add connect/disconnect button if controller is connected
                    if roboschlenk_state['connected'] and wizard_state['display_ports'].get(motor):
                        if roboschlenk_state['displays'][motor]['connected']:
                            def make_disconnect_handler(m):
                                def handler():
                                    disconnect_display(m)
                                    # Refresh wizard content
                                    wizard_state['container'].clear()
                                    with wizard_state['container']:
                                        render_wizard_content()
                                return handler

                            ui.button("", icon="link_off", on_click=make_disconnect_handler(motor)).props("flat color=negative dense").style("min-width: 40px;").tooltip("Disconnect display")
                            ui.label("●").style("color: #00d26a; font-size: 16px;")
                        else:
                            def make_connect_handler(m):
                                def handler():
                                    connect_display(m)
                                    # Refresh wizard content
                                    wizard_state['container'].clear()
                                    with wizard_state['container']:
                                        render_wizard_content()
                                return handler

                            ui.button("", icon="link", on_click=make_connect_handler(motor)).props("flat color=primary dense").style("min-width: 40px;").tooltip("Connect display")
                            ui.label("●").style("color: #ff4757; font-size: 16px;")

    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 30px; min-width: 600px; max-width: 800px;"):
        ui.label("RoboSchlenk Setup Wizard").style("color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        ui.label("Configure COM ports for motor controller and LCD displays").style("color: #888888; font-size: 14px; margin-bottom: 30px;")

        # Create container for wizard content
        wizard_state['container'] = ui.column().style("width: 100%; gap: 0px;")
        with wizard_state['container']:
            render_wizard_content()

        # Buttons
        with ui.row().style("width: 100%; justify-content: flex-end; gap: 10px; margin-top: 30px;"):
            ui.button("Cancel", on_click=dialog.close).props("flat color=grey")

            def save_and_close():
                # Validate motor controller port
                if not wizard_state['motor_controller_port']:
                    ui.notify("Please select a motor controller port", type='negative')
                    return

                # Save configuration
                new_config = {
                    'motor_controller_port': wizard_state['motor_controller_port'],
                    'display_ports': wizard_state['display_ports'],
                    'configured': True
                }

                if save_config(new_config):
                    ui.notify("Configuration saved successfully", type='positive')
                    dialog.close()
                    # Refresh the content
                    if roboschlenk_state.get('content_container'):
                        roboschlenk_state['content_container'].clear()
                        with roboschlenk_state['content_container']:
                            render_content()
                else:
                    ui.notify("Failed to save configuration", type='negative')

            ui.button("Save Configuration", on_click=save_and_close).props("color=primary")

    dialog.open()

def connect_to_controller():
    """Connect to the motor controller"""
    config = get_config()
    port = config.get('motor_controller_port')

    if not port:
        ui.notify("No motor controller port configured", type='negative')
        return False

    try:
        roboschlenk_state['controller'] = MotorController(port)
        if roboschlenk_state['controller'].connect():
            roboschlenk_state['controller'].start_monitoring()
            roboschlenk_state['connected'] = True
            ui.notify(f"Connected to motor controller on {port}", type='positive')
            # Refresh the content
            if roboschlenk_state.get('content_container'):
                roboschlenk_state['content_container'].clear()
                with roboschlenk_state['content_container']:
                    render_content()
            return True
        else:
            ui.notify("Failed to connect to motor controller", type='negative')
            roboschlenk_state['controller'] = None
            return False
    except Exception as e:
        ui.notify(f"Connection error: {str(e)}", type='negative')
        roboschlenk_state['controller'] = None
        return False

def disconnect_from_controller():
    """Disconnect from the motor controller"""
    if roboschlenk_state['controller']:
        roboschlenk_state['controller'].disconnect()
        roboschlenk_state['controller'] = None
    roboschlenk_state['connected'] = False
    ui.notify("Disconnected from motor controller", type='info')
    # Refresh the content
    if roboschlenk_state.get('content_container'):
        roboschlenk_state['content_container'].clear()
        with roboschlenk_state['content_container']:
            render_content()

def connect_display(motor):
    """Connect to a motor's LCD display"""
    config = get_config()
    port = config.get('display_ports', {}).get(motor)

    if not port:
        ui.notify(f"No display port configured for Motor {motor}", type='warning')
        return False

    try:
        import serial
        import time
        display_serial = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
        roboschlenk_state['displays'][motor]['serial'] = display_serial
        roboschlenk_state['displays'][motor]['connected'] = True
        ui.notify(f"Connected to Motor {motor} display", type='positive')
        return True
    except Exception as e:
        ui.notify(f"Display connection error: {str(e)}", type='negative')
        return False

def disconnect_display(motor):
    """Disconnect from a motor's LCD display"""
    if roboschlenk_state['displays'][motor]['serial']:
        try:
            roboschlenk_state['displays'][motor]['serial'].close()
        except:
            pass
        roboschlenk_state['displays'][motor]['serial'] = None
    roboschlenk_state['displays'][motor]['connected'] = False
    ui.notify(f"Disconnected from Motor {motor} display", type='info')

def send_to_display(motor, message):
    """Send message to motor's LCD display"""
    if not roboschlenk_state['displays'][motor]['connected']:
        return False
    try:
        if len(message) > 40:
            message = message[:37] + "..."
        roboschlenk_state['displays'][motor]['serial'].write((message + "\n").encode())
        return True
    except:
        return False

def move_motor(motor, position):
    """Move motor to a position"""
    if not roboschlenk_state['connected']:
        ui.notify("Not connected to motor controller", type='warning')
        return

    controller = roboschlenk_state['controller']
    try:
        if position == 'gas':
            controller.move_to_gas(motor)
            ui.notify(f"Motor {motor} moving to GAS (90°)", type='info')
        elif position == 'closed':
            controller.move_to_closed(motor)
            ui.notify(f"Motor {motor} moving to CLOSED (0°)", type='info')
        elif position == 'vacuum':
            controller.move_to_vacuum(motor)
            ui.notify(f"Motor {motor} moving to VACUUM (270°)", type='info')

        # Send to display if connected
        position_angles = {'gas': '90°', 'closed': '0°', 'vacuum': '270°'}
        if roboschlenk_state['displays'][motor]['connected']:
            send_to_display(motor, f"M{motor}→{position_angles[position]}")
    except Exception as e:
        ui.notify(f"Move error: {str(e)}", type='negative')

def stop_motor(motor):
    """Stop a motor"""
    if not roboschlenk_state['connected']:
        return

    try:
        roboschlenk_state['controller'].stop_motor(motor)
        ui.notify(f"Motor {motor} stopped", type='info')
        if roboschlenk_state['displays'][motor]['connected']:
            send_to_display(motor, f"M{motor} STOP")
    except Exception as e:
        ui.notify(f"Stop error: {str(e)}", type='negative')

def toggle_motor_enable(motor):
    """Toggle motor enable/disable"""
    if not roboschlenk_state['connected']:
        return

    try:
        status = roboschlenk_state['controller'].get_motor_status(motor)
        if status and status.enabled:
            roboschlenk_state['controller'].disable_motor(motor)
            ui.notify(f"Motor {motor} disabled", type='info')
        else:
            roboschlenk_state['controller'].enable_motor(motor)
            ui.notify(f"Motor {motor} enabled", type='info')
    except Exception as e:
        ui.notify(f"Enable/disable error: {str(e)}", type='negative')

def emergency_stop():
    """Emergency stop all motors"""
    if not roboschlenk_state['connected']:
        return

    try:
        for motor in ['A', 'B', 'C', 'D']:
            roboschlenk_state['controller'].stop_motor(motor)
        ui.notify("⚠ EMERGENCY STOP - ALL MOTORS STOPPED", type='warning')

        # Send to all displays
        for motor in ['A', 'B', 'C', 'D']:
            if roboschlenk_state['displays'][motor]['connected']:
                send_to_display(motor, "EMERGENCY STOP!")
    except Exception as e:
        ui.notify(f"Emergency stop error: {str(e)}", type='negative')

def create_motor_panel(motor_name):
    """Create a motor control panel with circular display"""
    with ui.card().style("background-color: #2a2a2a; padding: 15px; width: 100%; border-radius: 12px;") as panel:
        # Header with motor name
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 12px;"):
            ui.label(f"Tap {motor_name}").style("color: white; font-size: 18px; font-weight: bold;")

            # Status indicators in header
            with ui.row().style("gap: 8px; align-items: center;"):
                moving_label = ui.label("STOPPED").style("color: #888888; font-size: 10px; font-weight: bold;")
                enabled_label = ui.label("ENABLED").style("color: #00d26a; font-size: 10px; font-weight: bold;")

        # Circular angle display
        with ui.column().style("width: 100%; align-items: center; margin-bottom: 12px;"):
            # Create circular container with gradient background
            circle_outer = ui.element('div').style(
                "width: 140px; height: 140px; border-radius: 50%; "
                "background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); "
                "display: flex; align-items: center; justify-content: center; "
                "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                "border: 3px solid #60a5fa; "
                "position: relative; transition: all 0.3s ease;"
            )

            with circle_outer:
                # Inner circle
                with ui.element('div').style(
                    "width: 124px; height: 124px; border-radius: 50%; "
                    "background-color: #1a1a1a; "
                    "display: flex; flex-direction: column; align-items: center; justify-content: center; "
                    "border: 2px solid #2563eb;"
                ):
                    angle_label = ui.label("---°").style(
                        "color: #60a5fa; font-size: 28px; font-weight: bold; "
                        "text-shadow: 0 2px 6px rgba(96, 165, 250, 0.5);"
                    )
                    position_label = ui.label("UNKNOWN").style(
                        "color: #888888; font-size: 10px; font-weight: bold; "
                        "margin-top: 3px; letter-spacing: 1px;"
                    )

        # Position preset buttons in a grid
        with ui.row().style("width: 100%; gap: 6px; margin-bottom: 10px;"):
            ui.button("CLOSED", icon="lock", on_click=lambda: move_motor(motor_name, 'closed')).props("outline").style(
                "flex: 1; height: 42px; font-weight: bold; border: 2px solid #10b981; "
                "color: #10b981; border-radius: 8px; font-size: 11px;"
            ).tooltip("Move to 0°")

            ui.button("GAS", icon="air", on_click=lambda: move_motor(motor_name, 'gas')).props("outline").style(
                "flex: 1; height: 42px; font-weight: bold; border: 2px solid #3b82f6; "
                "color: #3b82f6; border-radius: 8px; font-size: 11px;"
            ).tooltip("Move to 90°")

            ui.button("VACUUM", icon="science", on_click=lambda: move_motor(motor_name, 'vacuum')).props("outline").style(
                "flex: 1; height: 42px; font-weight: bold; border: 2px solid #f97316; "
                "color: #f97316; border-radius: 8px; font-size: 11px;"
            ).tooltip("Move to 270°")

        # Control buttons
        with ui.row().style("width: 100%; gap: 6px;"):
            ui.button("STOP", icon="stop_circle", on_click=lambda: stop_motor(motor_name)).props("color=negative").style(
                "flex: 1; height: 38px; font-weight: bold; border-radius: 8px; font-size: 11px;"
            )
            enable_btn = ui.button("DISABLE", icon="power_settings_new", on_click=lambda: toggle_motor_enable(motor_name)).props("outline").style(
                "flex: 1; height: 38px; font-weight: bold; border-radius: 8px; font-size: 11px;"
            )

        # Store references
        roboschlenk_state['motor_panels'][motor_name] = {
            'angle_label': angle_label,
            'position_label': position_label,
            'moving_label': moving_label,
            'enabled_label': enabled_label,
            'enable_btn': enable_btn,
            'circle_outer': circle_outer
        }

async def update_motor_status():
    """Update motor status displays"""
    while True:
        if roboschlenk_state['connected'] and roboschlenk_state['controller']:
            try:
                for motor in ['A', 'B', 'C', 'D']:
                    status = roboschlenk_state['controller'].get_motor_status(motor)
                    if status and motor in roboschlenk_state['motor_panels']:
                        panel = roboschlenk_state['motor_panels'][motor]

                        # Update angle and position label
                        if status.angle == status.angle:  # Check for NaN
                            panel['angle_label'].text = f"{status.angle:.1f}°"

                            # Determine position based on angle and update colors
                            angle = status.angle
                            # CLOSED - Green (0° or 180°, threshold ±10°)
                            if abs(angle - 0) < 10 or abs(angle - 180) < 10:
                                panel['position_label'].text = "CLOSED"
                                panel['position_label'].style("color: #10b981;")
                                panel['angle_label'].style("color: #10b981; text-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);")
                                panel['circle_outer'].style(
                                    "width: 140px; height: 140px; border-radius: 50%; "
                                    "background: linear-gradient(135deg, #065f46 0%, #10b981 100%); "
                                    "display: flex; align-items: center; justify-content: center; "
                                    "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                                    "border: 3px solid #10b981; position: relative; transition: all 0.3s ease;"
                                )
                            # GAS - Blue (90°, threshold ±10°)
                            elif abs(angle - 90) < 10:
                                panel['position_label'].text = "GAS"
                                panel['position_label'].style("color: #3b82f6;")
                                panel['angle_label'].style("color: #3b82f6; text-shadow: 0 2px 6px rgba(59, 130, 246, 0.5);")
                                panel['circle_outer'].style(
                                    "width: 140px; height: 140px; border-radius: 50%; "
                                    "background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); "
                                    "display: flex; align-items: center; justify-content: center; "
                                    "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                                    "border: 3px solid #3b82f6; position: relative; transition: all 0.3s ease;"
                                )
                            # VACUUM - Orange (270°, threshold ±10°)
                            elif abs(angle - 270) < 10:
                                panel['position_label'].text = "VACUUM"
                                panel['position_label'].style("color: #f97316;")
                                panel['angle_label'].style("color: #f97316; text-shadow: 0 2px 6px rgba(249, 115, 22, 0.5);")
                                panel['circle_outer'].style(
                                    "width: 140px; height: 140px; border-radius: 50%; "
                                    "background: linear-gradient(135deg, #9a3412 0%, #f97316 100%); "
                                    "display: flex; align-items: center; justify-content: center; "
                                    "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                                    "border: 3px solid #f97316; position: relative; transition: all 0.3s ease;"
                                )
                            else:
                                # CUSTOM - Gray
                                panel['position_label'].text = f"CUSTOM"
                                panel['position_label'].style("color: #9ca3af;")
                                panel['angle_label'].style("color: #9ca3af; text-shadow: 0 2px 6px rgba(156, 163, 175, 0.5);")
                                panel['circle_outer'].style(
                                    "width: 140px; height: 140px; border-radius: 50%; "
                                    "background: linear-gradient(135deg, #374151 0%, #6b7280 100%); "
                                    "display: flex; align-items: center; justify-content: center; "
                                    "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                                    "border: 3px solid #6b7280; position: relative; transition: all 0.3s ease;"
                                )
                        else:
                            panel['angle_label'].text = "---°"
                            panel['position_label'].text = "UNKNOWN"
                            panel['position_label'].style("color: #888888;")
                            panel['angle_label'].style("color: #888888; text-shadow: none;")
                            panel['circle_outer'].style(
                                "width: 140px; height: 140px; border-radius: 50%; "
                                "background: linear-gradient(135deg, #1f2937 0%, #4b5563 100%); "
                                "display: flex; align-items: center; justify-content: center; "
                                "box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); "
                                "border: 3px solid #4b5563; position: relative; transition: all 0.3s ease;"
                            )

                        # Update moving status
                        if status.moving:
                            panel['moving_label'].text = "MOVING"
                            panel['moving_label'].style("color: #ffa502;")
                        else:
                            panel['moving_label'].text = "STOPPED"
                            panel['moving_label'].style("color: #888888;")

                        # Update enabled status
                        if status.enabled:
                            panel['enabled_label'].text = "ENABLED"
                            panel['enabled_label'].style("color: #00d26a;")
                            panel['enable_btn'].text = "DISABLE"
                        else:
                            panel['enabled_label'].text = "DISABLED"
                            panel['enabled_label'].style("color: #ff4757;")
                            panel['enable_btn'].text = "ENABLE"

                # Auto-send to displays if enabled
                if roboschlenk_state['auto_send']:
                    status_parts = []
                    for motor in ['A', 'B', 'C', 'D']:
                        status = roboschlenk_state['controller'].get_motor_status(motor)
                        if status and status.angle == status.angle:
                            status_parts.append(f"{motor}:{status.angle:.0f}°")

                    if status_parts:
                        combined_data = " | ".join(status_parts)
                        for motor in ['A', 'B', 'C', 'D']:
                            if roboschlenk_state['displays'][motor]['connected']:
                                send_to_display(motor, combined_data)
            except:
                pass

        await asyncio.sleep(0.1)

def render_content():
    """Render the main content (called by render and for refreshing)"""
    config = get_config()
    configured = is_configured()

    if not configured:
        # Show configuration prompt
        with ui.card().style("background-color: #333333; padding: 40px; width: 100%; text-align: center;"):
            ui.label("⚙").style("color: #888888; font-size: 48px; margin-bottom: 20px;")
            ui.label("RoboSchlenk Not Configured").style("color: white; font-size: 20px; font-weight: bold; margin-bottom: 15px;")
            ui.label("Please configure the motor controller and display COM ports to get started.").style("color: #888888; font-size: 14px; margin-bottom: 30px;")
    else:
        # Connection panel
        with ui.card().style("background-color: #333333; padding: 20px; width: 100%;"):
            ui.label("Controller Connection").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

            with ui.row().style("width: 100%; align-items: center; gap: 20px;"):
                ui.label(f"Port: {config['motor_controller_port']}").style("color: #cccccc; font-size: 14px;")

                if not roboschlenk_state['connected']:
                    ui.button("Connect", icon="power", on_click=connect_to_controller).props("color=primary")
                    status_label = ui.label("● Disconnected").style("color: #ff4757; font-size: 14px; font-weight: bold;")
                else:
                    ui.button("Disconnect", icon="power_off", on_click=disconnect_from_controller).props("color=negative")
                    status_label = ui.label("● Connected").style("color: #00d26a; font-size: 14px; font-weight: bold;")

        if roboschlenk_state['connected']:
            # Motor control panels
            ui.label("Motor Controls").style("color: white; font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")

            # Create 2x2 grid of motor panels
            with ui.row().style("width: 100%; gap: 20px;"):
                with ui.column().style("flex: 1; gap: 20px;"):
                    create_motor_panel('A')
                    create_motor_panel('C')
                with ui.column().style("flex: 1; gap: 20px;"):
                    create_motor_panel('B')
                    create_motor_panel('D')

            # Emergency stop
            with ui.card().style("background-color: #ff4757; padding: 20px; width: 100%; margin-top: 20px;"):
                ui.button("⚠ EMERGENCY STOP ALL MOTORS ⚠", on_click=emergency_stop).props("color=white text-color=negative size=lg").style("width: 100%; height: 60px; font-size: 18px; font-weight: bold;")

            # Start status update timer
            if roboschlenk_state['status_timer'] is None:
                roboschlenk_state['status_timer'] = ui.timer(0.1, update_motor_status)

def render():
    """Render the RoboSchlenk page content"""
    with ui.column().style("padding: 20px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Page header
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 20px;"):
            with ui.column().style("gap: 5px;"):
                ui.label("RoboSchlenk").style("color: white; font-size: 24px; font-weight: bold;")
                ui.label("Automated Schlenk line control").style("color: #888888; font-size: 14px;")

            ui.button("⚙ Setup", icon="settings", on_click=show_setup_wizard).props("outline")

        # Content container that can be refreshed
        roboschlenk_state['content_container'] = ui.column().style("width: 100%; gap: 20px;")
        with roboschlenk_state['content_container']:
            render_content()
