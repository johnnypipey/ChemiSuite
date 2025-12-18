import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Dict
import sys
import os
import importlib.util

# Import the motor controller (assumes motor_controller.py is in same directory)
try:
    from motor_controller import MotorController, MotorStatus
except ImportError:
    print("Error: motor_controller.py not found. Please ensure it's in the same directory.")
    sys.exit(1)


class MotorControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Four-Motor Schlenk Control System with Programmable Control")
        self.root.geometry("1400x1000")
        self.root.configure(bg='#2b2b2b')
        
        self.controller: Optional[MotorController] = None
        self.connected = False
        self.update_running = True
        
        # Program execution
        self.loaded_program = None
        self.program_running = False
        self.program_thread = None
        self.loaded_program_path = None
        
        # Multiple display connections - all 4 motors
        self.displays: Dict[str, dict] = {
            'A': {'serial': None, 'connected': False, 'port': None},
            'B': {'serial': None, 'connected': False, 'port': None},
            'C': {'serial': None, 'connected': False, 'port': None},
            'D': {'serial': None, 'connected': False, 'port': None},
        }
        
        # Color scheme
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'button': '#4a4a4a',
            'button_active': '#5a5a5a',
            'accent': '#00a8ff',
            'success': '#00d26a',
            'error': '#ff4757',
            'warning': '#ffa502',
            'purple': '#a55eea'
        }
        
        self.setup_ui()
        self.start_update_thread()
        
    def setup_ui(self):
        # Main container with two columns
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left column (existing controls)
        left_column = tk.Frame(main_frame, bg=self.colors['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right column (program control)
        right_column = tk.Frame(main_frame, bg=self.colors['bg'])
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # ===== LEFT COLUMN =====
        
        # ===== Connection Panel =====
        conn_frame = tk.LabelFrame(left_column, text="Arduino Connection", 
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Arial', 10, 'bold'))
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(conn_frame, text="Arduino Port:", bg=self.colors['bg'], 
                fg=self.colors['fg']).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, 
                                       width=15, state='readonly')
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(conn_frame, text="Refresh", command=self.refresh_ports,
                 bg=self.colors['button'], fg=self.colors['fg']).grid(
                     row=0, column=2, padx=5, pady=5)
        
        self.connect_btn = tk.Button(conn_frame, text="Connect", 
                                     command=self.toggle_connection,
                                     bg=self.colors['accent'], fg=self.colors['fg'],
                                     font=('Arial', 9, 'bold'), width=12)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.status_label = tk.Label(conn_frame, text="● Disconnected", 
                                     bg=self.colors['bg'], fg=self.colors['error'],
                                     font=('Arial', 9, 'bold'))
        self.status_label.grid(row=0, column=4, padx=10, pady=5)
        
        # ===== Display Connection Panel =====
        display_frame = tk.LabelFrame(left_column, text="LCD Display Connections", 
                                      bg=self.colors['bg'], fg=self.colors['fg'],
                                      font=('Arial', 10, 'bold'))
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Motor A Display
        tk.Label(display_frame, text="Motor A:", bg=self.colors['bg'], 
                fg=self.colors['fg']).grid(row=0, column=0, padx=5, pady=3, sticky='w')
        
        self.display_a_port_var = tk.StringVar()
        self.display_a_port_combo = ttk.Combobox(display_frame, textvariable=self.display_a_port_var, 
                                                 width=12, state='readonly')
        self.display_a_port_combo.grid(row=0, column=1, padx=5, pady=3)
        
        self.display_a_connect_btn = tk.Button(display_frame, text="Connect", 
                                              command=lambda: self.toggle_display_connection('A'),
                                              bg=self.colors['accent'], fg=self.colors['fg'],
                                              font=('Arial', 8), width=10)
        self.display_a_connect_btn.grid(row=0, column=2, padx=5, pady=3)
        
        self.display_a_status_label = tk.Label(display_frame, text="●", 
                                              bg=self.colors['bg'], fg=self.colors['error'],
                                              font=('Arial', 9, 'bold'))
        self.display_a_status_label.grid(row=0, column=3, padx=5, pady=3)
        
        # Motor B Display
        tk.Label(display_frame, text="Motor B:", bg=self.colors['bg'], 
                fg=self.colors['fg']).grid(row=1, column=0, padx=5, pady=3, sticky='w')
        
        self.display_b_port_var = tk.StringVar()
        self.display_b_port_combo = ttk.Combobox(display_frame, textvariable=self.display_b_port_var, 
                                                 width=12, state='readonly')
        self.display_b_port_combo.grid(row=1, column=1, padx=5, pady=3)
        
        self.display_b_connect_btn = tk.Button(display_frame, text="Connect", 
                                              command=lambda: self.toggle_display_connection('B'),
                                              bg=self.colors['accent'], fg=self.colors['fg'],
                                              font=('Arial', 8), width=10)
        self.display_b_connect_btn.grid(row=1, column=2, padx=5, pady=3)
        
        self.display_b_status_label = tk.Label(display_frame, text="●", 
                                              bg=self.colors['bg'], fg=self.colors['error'],
                                              font=('Arial', 9, 'bold'))
        self.display_b_status_label.grid(row=1, column=3, padx=5, pady=3)
        
        # Motor C Display
        tk.Label(display_frame, text="Motor C:", bg=self.colors['bg'], 
                fg=self.colors['fg']).grid(row=2, column=0, padx=5, pady=3, sticky='w')
        
        self.display_c_port_var = tk.StringVar()
        self.display_c_port_combo = ttk.Combobox(display_frame, textvariable=self.display_c_port_var, 
                                                 width=12, state='readonly')
        self.display_c_port_combo.grid(row=2, column=1, padx=5, pady=3)
        
        self.display_c_connect_btn = tk.Button(display_frame, text="Connect", 
                                              command=lambda: self.toggle_display_connection('C'),
                                              bg=self.colors['accent'], fg=self.colors['fg'],
                                              font=('Arial', 8), width=10)
        self.display_c_connect_btn.grid(row=2, column=2, padx=5, pady=3)
        
        self.display_c_status_label = tk.Label(display_frame, text="●", 
                                              bg=self.colors['bg'], fg=self.colors['error'],
                                              font=('Arial', 9, 'bold'))
        self.display_c_status_label.grid(row=2, column=3, padx=5, pady=3)
        
        # Motor D Display
        tk.Label(display_frame, text="Motor D:", bg=self.colors['bg'], 
                fg=self.colors['fg']).grid(row=3, column=0, padx=5, pady=3, sticky='w')
        
        self.display_d_port_var = tk.StringVar()
        self.display_d_port_combo = ttk.Combobox(display_frame, textvariable=self.display_d_port_var, 
                                                 width=12, state='readonly')
        self.display_d_port_combo.grid(row=3, column=1, padx=5, pady=3)
        
        self.display_d_connect_btn = tk.Button(display_frame, text="Connect", 
                                              command=lambda: self.toggle_display_connection('D'),
                                              bg=self.colors['accent'], fg=self.colors['fg'],
                                              font=('Arial', 8), width=10)
        self.display_d_connect_btn.grid(row=3, column=2, padx=5, pady=3)
        
        self.display_d_status_label = tk.Label(display_frame, text="●", 
                                              bg=self.colors['bg'], fg=self.colors['error'],
                                              font=('Arial', 9, 'bold'))
        self.display_d_status_label.grid(row=3, column=3, padx=5, pady=3)
        
        tk.Button(display_frame, text="Refresh Ports", command=self.refresh_ports,
                 bg=self.colors['button'], fg=self.colors['fg'], 
                 font=('Arial', 8)).grid(row=4, column=1, padx=5, pady=5)
        
        # Auto-send checkbox
        self.auto_send_var = tk.BooleanVar(value=True)
        tk.Checkbutton(display_frame, text="Auto-send data to displays", 
                      variable=self.auto_send_var,
                      bg=self.colors['bg'], fg=self.colors['fg'],
                      selectcolor=self.colors['button'], 
                      activebackground=self.colors['bg'],
                      activeforeground=self.colors['fg']).grid(row=5, column=0, columnspan=4, 
                                                               padx=5, pady=3, sticky='w')
        
        # ===== Motor Control Panels =====
        motors_frame = tk.Frame(left_column, bg=self.colors['bg'])
        motors_frame.pack(fill=tk.BOTH, expand=True)
        
        self.motor_panels = {}
        for i, motor in enumerate(['A', 'B', 'C', 'D']):
            row = i // 2
            col = i % 2
            panel = self.create_motor_panel(motors_frame, motor)
            panel.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            self.motor_panels[motor] = panel
        
        motors_frame.grid_rowconfigure(0, weight=1)
        motors_frame.grid_rowconfigure(1, weight=1)
        motors_frame.grid_columnconfigure(0, weight=1)
        motors_frame.grid_columnconfigure(1, weight=1)
        
        # ===== Emergency Stop =====
        emergency_frame = tk.Frame(left_column, bg=self.colors['bg'])
        emergency_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(emergency_frame, text="⚠ STOP ALL MOTORS ⚠", 
                 command=self.emergency_stop,
                 bg=self.colors['error'], fg=self.colors['fg'],
                 font=('Arial', 12, 'bold'), height=2).pack(fill=tk.X)
        
        # ===== RIGHT COLUMN - PROGRAM CONTROL =====
        
        # ===== Program Control Panel =====
        program_frame = tk.LabelFrame(right_column, text="Automated Program Control", 
                                      bg=self.colors['bg'], fg=self.colors['fg'],
                                      font=('Arial', 10, 'bold'))
        program_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Load program button
        tk.Button(program_frame, text="📁 Load Program", 
                 command=self.load_program,
                 bg=self.colors['purple'], fg=self.colors['fg'],
                 font=('Arial', 10, 'bold'), height=2).pack(fill=tk.X, padx=10, pady=10)
        
        # Program info
        self.program_label = tk.Label(program_frame, text="No program loaded", 
                                      bg=self.colors['bg'], fg=self.colors['fg'],
                                      font=('Arial', 9), wraplength=280, justify=tk.LEFT)
        self.program_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Program description
        desc_label = tk.Label(program_frame, text="Program Description:", 
                             bg=self.colors['bg'], fg=self.colors['fg'],
                             font=('Arial', 9, 'bold'))
        desc_label.pack(anchor='w', padx=10, pady=(10, 2))
        
        self.program_desc = scrolledtext.ScrolledText(program_frame, height=6,
                                                      bg='#1e1e1e', fg=self.colors['fg'],
                                                      font=('Arial', 9), wrap=tk.WORD)
        self.program_desc.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.program_desc.config(state=tk.DISABLED)
        self.program_desc.insert(tk.END, "Load a program to see its description here.")
        
        # Control buttons
        control_frame = tk.Frame(program_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.run_btn = tk.Button(control_frame, text="▶ RUN", 
                                command=self.run_program,
                                bg=self.colors['success'], fg=self.colors['fg'],
                                font=('Arial', 11, 'bold'), height=2,
                                state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(control_frame, text="■ STOP", 
                                 command=self.stop_program,
                                 bg=self.colors['error'], fg=self.colors['fg'],
                                 font=('Arial', 11, 'bold'), height=2,
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Program status
        self.program_status_label = tk.Label(program_frame, text="● Program Idle", 
                                            bg=self.colors['bg'], fg=self.colors['fg'],
                                            font=('Arial', 10, 'bold'))
        self.program_status_label.pack(pady=10)
        
        # ===== Console Log =====
        log_frame = tk.LabelFrame(right_column, text="Program Console", 
                                 bg=self.colors['bg'], fg=self.colors['fg'],
                                 font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(log_frame, height=15, 
                                                bg='#1e1e1e', fg='#00ff00',
                                                font=('Courier', 9))
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)
        
        self.refresh_ports()
        
    def create_motor_panel(self, parent, motor_name):
        panel_frame = tk.LabelFrame(parent, text=f"Motor {motor_name}", 
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Arial', 10, 'bold'))
        
        status_frame = tk.Frame(panel_frame, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X, padx=8, pady=8)
        
        angle_label = tk.Label(status_frame, text="---°", 
                              bg=self.colors['bg'], fg=self.colors['accent'],
                              font=('Arial', 20, 'bold'))
        angle_label.pack()
        
        state_frame = tk.Frame(status_frame, bg=self.colors['bg'])
        state_frame.pack(pady=3)
        
        moving_label = tk.Label(state_frame, text="● STOPPED", 
                               bg=self.colors['bg'], fg=self.colors['fg'],
                               font=('Arial', 8))
        moving_label.pack(side=tk.LEFT, padx=3)
        
        enabled_label = tk.Label(state_frame, text="● ENABLED", 
                                bg=self.colors['bg'], fg=self.colors['success'],
                                font=('Arial', 8))
        enabled_label.pack(side=tk.LEFT, padx=3)
        
        preset_frame = tk.LabelFrame(panel_frame, text="Presets",
                                    bg=self.colors['bg'], fg=self.colors['fg'],
                                    font=('Arial', 8, 'bold'))
        preset_frame.pack(fill=tk.X, padx=8, pady=3)
        
        btn_frame = tk.Frame(preset_frame, bg=self.colors['bg'])
        btn_frame.pack(pady=3)
        
        tk.Button(btn_frame, text="CLOSED\n(0°)", 
                 command=lambda: self.move_motor(motor_name, 'closed'),
                 bg=self.colors['button'], fg=self.colors['fg'],
                 width=8, height=2, font=('Arial', 8)).pack(side=tk.LEFT, padx=1)
        
        tk.Button(btn_frame, text="GAS\n(90°)", 
                 command=lambda: self.move_motor(motor_name, 'gas'),
                 bg=self.colors['button'], fg=self.colors['fg'],
                 width=8, height=2, font=('Arial', 8)).pack(side=tk.LEFT, padx=1)
        
        tk.Button(btn_frame, text="VACUUM\n(270°)", 
                 command=lambda: self.move_motor(motor_name, 'vacuum'),
                 bg=self.colors['button'], fg=self.colors['fg'],
                 width=8, height=2, font=('Arial', 8)).pack(side=tk.LEFT, padx=1)
        
        control_frame = tk.Frame(panel_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, padx=8, pady=3)
        
        tk.Button(control_frame, text="STOP", 
                 command=lambda: self.stop_motor(motor_name),
                 bg=self.colors['error'], fg=self.colors['fg'],
                 width=10, font=('Arial', 8)).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        
        enable_btn = tk.Button(control_frame, text="DISABLE", 
                              command=lambda: self.toggle_enable(motor_name),
                              bg=self.colors['button'], fg=self.colors['fg'],
                              width=10, font=('Arial', 8))
        enable_btn.pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        
        panel_frame.angle_label = angle_label
        panel_frame.moving_label = moving_label
        panel_frame.enabled_label = enabled_label
        panel_frame.enable_btn = enable_btn
        
        return panel_frame
    
    def load_program(self):
        """Load a Python program file"""
        filepath = filedialog.askopenfilename(
            title="Select Program File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location("loaded_program", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verify required function exists
            if not hasattr(module, 'run_program'):
                messagebox.showerror("Error", 
                    "Program must contain a 'run_program(controller, log_callback)' function")
                return
            
            self.loaded_program = module
            self.loaded_program_path = filepath
            program_name = os.path.basename(filepath)
            
            self.program_label.config(text=f"Loaded: {program_name}")
            self.run_btn.config(state=tk.NORMAL)
            
            # Get description if available
            description = getattr(module, 'DESCRIPTION', 'No description available.')
            self.program_desc.config(state=tk.NORMAL)
            self.program_desc.delete(1.0, tk.END)
            self.program_desc.insert(tk.END, description)
            self.program_desc.config(state=tk.DISABLED)
            
            self.log(f"✓ Program loaded: {program_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load program: {str(e)}")
            self.log(f"✗ Failed to load program: {str(e)}")
    
    def run_program(self):
        """Execute the loaded program"""
        if not self.connected:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
        
        if not self.loaded_program:
            messagebox.showerror("Error", "No program loaded")
            return
        
        if self.program_running:
            messagebox.showwarning("Warning", "Program is already running")
            return
        
        self.program_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.program_status_label.config(text="● Program Running", fg=self.colors['success'])
        
        self.log("=" * 50)
        self.log("▶ STARTING PROGRAM")
        self.log("=" * 50)
        
        # Run program in separate thread
        self.program_thread = threading.Thread(target=self._run_program_thread, daemon=True)
        self.program_thread.start()
    
    def _run_program_thread(self):
        """Thread function to run the program"""
        try:
            # Pass a check function that the program can use to see if it should stop
            self.loaded_program.run_program(self.controller, self.log, lambda: self.program_running)
            
            if self.program_running:  # Only log completion if not stopped
                self.log("=" * 50)
                self.log("✓ PROGRAM COMPLETED SUCCESSFULLY")
                self.log("=" * 50)
        except Exception as e:
            self.log(f"✗ PROGRAM ERROR: {str(e)}")
            self.log("=" * 50)
        finally:
            self.program_running = False
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.program_status_label.config(text="● Program Idle", fg=self.colors['fg'])
    
    def stop_program(self):
        """Stop the running program"""
        if not self.program_running:
            return
        
        self.program_running = False
        self.log("=" * 50)
        self.log("■ PROGRAM STOPPED BY USER")
        self.log("=" * 50)
        
        # Emergency stop all motors
        self.emergency_stop()
        
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.program_status_label.config(text="● Program Stopped", fg=self.colors['error'])
    
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_combo.current(0)
        
        self.display_a_port_combo['values'] = ports
        if ports and not self.display_a_port_var.get() and len(ports) > 1:
            self.display_a_port_combo.current(1)
        
        self.display_b_port_combo['values'] = ports
        if ports and not self.display_b_port_var.get() and len(ports) > 2:
            self.display_b_port_combo.current(2)
        
        self.display_c_port_combo['values'] = ports
        if ports and not self.display_c_port_var.get() and len(ports) > 3:
            self.display_c_port_combo.current(3)
        
        self.display_d_port_combo['values'] = ports
        if ports and not self.display_d_port_var.get() and len(ports) > 4:
            self.display_d_port_combo.current(4)
    
    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a port")
            return
        
        try:
            self.controller = MotorController(port)
            if self.controller.connect():
                self.controller.start_monitoring()
                self.connected = True
                self.connect_btn.config(text="Disconnect", bg=self.colors['error'])
                self.status_label.config(text="● Connected", fg=self.colors['success'])
                self.log("Connected to Arduino on " + port)
                
                self.start_arduino_monitor_thread()
            else:
                messagebox.showerror("Error", "Failed to connect")
                self.controller = None
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {str(e)}")
            self.controller = None
    
    def disconnect(self):
        if self.controller:
            self.controller.disconnect()
            self.controller = None
        self.connected = False
        self.connect_btn.config(text="Connect", bg=self.colors['accent'])
        self.status_label.config(text="● Disconnected", fg=self.colors['error'])
        self.log("Disconnected from Arduino")
    
    def toggle_display_connection(self, motor):
        if not self.displays[motor]['connected']:
            self.connect_display(motor)
        else:
            self.disconnect_display(motor)
    
    def connect_display(self, motor):
        port_vars = {'A': self.display_a_port_var, 'B': self.display_b_port_var,
                    'C': self.display_c_port_var, 'D': self.display_d_port_var}
        status_labels = {'A': self.display_a_status_label, 'B': self.display_b_status_label,
                        'C': self.display_c_status_label, 'D': self.display_d_status_label}
        connect_btns = {'A': self.display_a_connect_btn, 'B': self.display_b_connect_btn,
                       'C': self.display_c_connect_btn, 'D': self.display_d_connect_btn}
        
        port = port_vars[motor].get()
        status_label = status_labels[motor]
        connect_btn = connect_btns[motor]
        
        if not port:
            messagebox.showerror("Error", f"Please select a port for Motor {motor} display")
            return
        
        # Check if port is already in use
        if port == self.port_var.get():
            messagebox.showerror("Error", f"Motor {motor} display port must be different from Arduino port")
            return
        
        for other_motor, display_info in self.displays.items():
            if other_motor != motor and display_info['port'] == port:
                messagebox.showerror("Error", f"Port already in use by Motor {other_motor} display")
                return
        
        try:
            display_serial = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)
            self.displays[motor]['serial'] = display_serial
            self.displays[motor]['connected'] = True
            self.displays[motor]['port'] = port
            connect_btn.config(text="Disconnect", bg=self.colors['error'])
            status_label.config(text="●", fg=self.colors['success'])
            self.log(f"Connected to Motor {motor} LCD display on {port}")
            self.send_to_display(motor, "System Ready")
        except Exception as e:
            messagebox.showerror("Error", f"Motor {motor} display connection failed: {str(e)}")
            self.displays[motor]['serial'] = None
            self.displays[motor]['connected'] = False
    
    def disconnect_display(self, motor):
        if self.displays[motor]['serial']:
            try: 
                self.displays[motor]['serial'].close()
            except: 
                pass
            self.displays[motor]['serial'] = None
        
        self.displays[motor]['connected'] = False
        self.displays[motor]['port'] = None
        
        connect_btns = {'A': self.display_a_connect_btn, 'B': self.display_b_connect_btn,
                       'C': self.display_c_connect_btn, 'D': self.display_d_connect_btn}
        status_labels = {'A': self.display_a_status_label, 'B': self.display_b_status_label,
                        'C': self.display_c_status_label, 'D': self.display_d_status_label}
        
        connect_btns[motor].config(text="Connect", bg=self.colors['accent'])
        status_labels[motor].config(text="●", fg=self.colors['error'])
        
        self.log(f"Disconnected from Motor {motor} LCD display")
    
    def send_to_display(self, motor, message):
        if not self.displays[motor]['connected'] or not self.displays[motor]['serial']:
            return False
        try:
            if len(message) > 40:
                message = message[:37] + "..."
            self.displays[motor]['serial'].write((message + "\n").encode())
            self.displays[motor]['serial'].readline().decode().strip()
            return True
        except Exception:
            return False
    
    def arduino_monitor_loop(self):
        while self.update_running and self.connected:
            try:
                if not self.auto_send_var.get():
                    time.sleep(0.1)
                    continue
                
                # Get status for all motors
                status_parts = []
                for motor in ['A', 'B', 'C', 'D']:
                    status = self.controller.get_motor_status(motor)
                    if status and status.angle == status.angle:
                        status_parts.append(f"{motor}:{status.angle:.0f}°")
                
                if status_parts:
                    combined_data = " | ".join(status_parts)
                    
                    # Send to all connected displays
                    for motor in ['A', 'B', 'C', 'D']:
                        if self.displays[motor]['connected']:
                            self.send_to_display(motor, combined_data)
                        
            except:
                pass
            time.sleep(0.05)
    
    def start_arduino_monitor_thread(self):
        threading.Thread(target=self.arduino_monitor_loop, daemon=True).start()
    
    def move_motor(self, motor, position):
        if not self.connected:
            return
        
        try:
            position_angles = {'gas': '90°', 'closed': '0°', 'vacuum': '270°'}
            
            if position == 'gas':
                self.controller.move_to_gas(motor)
            elif position == 'closed':
                self.controller.move_to_closed(motor)
            elif position == 'vacuum':
                self.controller.move_to_vacuum(motor)
            
            self.log(f"Motor {motor} → {position.upper()}")
            
            # Send to specific motor display if connected
            if motor in ['A', 'B', 'C', 'D'] and self.displays[motor]['connected']:
                msg = f"M{motor}→{position_angles.get(position, position.upper())}"
                self.send_to_display(motor, msg)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def stop_motor(self, motor):
        if not self.connected:
            return
        try:
            self.controller.stop_motor(motor)
            self.log(f"Motor {motor} STOPPED")
            if motor in ['A', 'B', 'C', 'D'] and self.displays[motor]['connected']:
                self.send_to_display(motor, f"M{motor} STOP")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def toggle_enable(self, motor):
        if not self.connected:
            return
        
        try:
            status = self.controller.get_motor_status(motor)
            if status and status.enabled:
                self.controller.disable_motor(motor)
                self.log(f"Motor {motor} DISABLED")
            else:
                self.controller.enable_motor(motor)
                self.log(f"Motor {motor} ENABLED")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def emergency_stop(self):
        if not self.connected:
            return
        
        try:
            for motor in ['A', 'B', 'C', 'D']:
                self.controller.stop_motor(motor)
            
            self.log("⚠ EMERGENCY STOP - ALL MOTORS STOPPED ⚠")
            
            # Send to all connected displays
            for motor in ['A', 'B', 'C', 'D']:
                if self.displays[motor]['connected']:
                    self.send_to_display(motor, "EMERGENCY STOP!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_motor_display(self):
        if not self.connected or not self.controller:
            return
        
        for motor in ['A', 'B', 'C', 'D']:
            status = self.controller.get_motor_status(motor)
            if status:
                panel = self.motor_panels[motor]
                
                if status.angle != status.angle:
                    panel.angle_label.config(text="---°")
                else:
                    panel.angle_label.config(text=f"{status.angle:.1f}°")
                
                panel.moving_label.config(
                    text="● MOVING" if status.moving else "● STOPPED",
                    fg=self.colors['warning'] if status.moving else self.colors['fg']
                )
                
                if status.enabled:
                    panel.enabled_label.config(text="● ENABLED", fg=self.colors['success'])
                    panel.enable_btn.config(text="DISABLE")
                else:
                    panel.enabled_label.config(text="● DISABLED", fg=self.colors['error'])
                    panel.enable_btn.config(text="ENABLE")
    
    def update_loop(self):
        while self.update_running:
            try:
                self.update_motor_display()
            except:
                pass
            time.sleep(0.1)
    
    def start_update_thread(self):
        threading.Thread(target=self.update_loop, daemon=True).start()
    
    def log(self, message):
        self.console.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def on_closing(self):
        if self.program_running:
            if not messagebox.askyesno("Confirm", "A program is running. Stop and exit?"):
                return
            self.stop_program()
        
        self.update_running = False
        if self.connected:
            self.disconnect()
        for motor in ['A', 'B', 'C', 'D']:
            if self.displays[motor]['connected']:
                self.disconnect_display(motor)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MotorControlGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()