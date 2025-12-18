"""
AZURA Pump P 2.1S/P 4.1S - Complete Control Program
Single file with GUI, connection testing, and full pump control

Based on AZURA Pump Instructions V6870
RS-232 specs: 9600 baud, 8 bit, 1 stop bit, no parity
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional


class AzuraPump:
    """Control interface for AZURA Pump P 2.1S/P 4.1S"""
    
    HEAD_10ML = 10
    HEAD_50ML = 50
    
    def __init__(self, port: str, timeout: float = 1.0):
        self.port = port
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """Establish connection to pump"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            time.sleep(0.1)
            return True
        except serial.SerialException:
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def _send_command(self, command: str) -> Optional[str]:
        """Send command and return response"""
        if not self.ser or not self.ser.is_open:
            return None
        
        try:
            self.ser.reset_input_buffer()
            cmd = command.strip() + '\r'  # FIXED: Use \r only, not \r\n
            self.ser.write(cmd.encode('ascii'))
            time.sleep(0.1)  # Slightly longer delay
            # Read all available data instead of readline
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore').strip()
                return response
            return None
        except Exception:
            return None
    
    def start(self) -> bool:
        """Start pump flow"""
        return self._send_command("ON") is not None
    
    def stop(self) -> bool:
        """Stop pump flow"""
        return self._send_command("OFF") is not None
    
    def set_flow(self, flow_ul_min: float) -> bool:
        """Set flow rate in µL/min (0-50000)"""
        if not 0 <= flow_ul_min <= 50000:
            return False
        response = self._send_command(f"FLOW:{int(flow_ul_min)}")
        return response is not None
    
    def get_flow(self) -> Optional[float]:
        """Read current flow rate in µL/min"""
        response = self._send_command("FLOW?")
        if response:
            try:
                # Handle "FLOW:2000" format
                if ':' in response:
                    response = response.split(':')[1]
                return float(response)
            except ValueError:
                pass
        return None
    
    def get_pressure(self) -> Optional[float]:
        """Read pressure in MPa (only for P 4.1S)"""
        response = self._send_command("PRESSURE?")
        if response:
            try:
                # Handle "PRESSURE:xxx" format
                if ':' in response:
                    response = response.split(':')[1]
                return float(response) / 10.0  # Convert from 0.1 MPa units
            except ValueError:
                pass
        return None
    
    def set_head_type(self, head_type: int) -> bool:
        """Set pump head type (10 or 50)"""
        if head_type not in [10, 50]:
            return False
        response = self._send_command(f"HEADTYPE:{head_type}")
        return response is not None
    
    def get_head_type(self) -> Optional[int]:
        """Read current pump head type"""
        response = self._send_command("HEADTYPE?")
        if response:
            try:
                # Handle "HEADTYPE:10" format
                if ':' in response:
                    response = response.split(':')[1]
                # Remove "mL" if present
                response = response.replace('mL', '').strip()
                return int(response)
            except ValueError:
                pass
        return None
    
    def set_remote_mode(self) -> bool:
        """Enable remote control mode"""
        return self._send_command("REMOTE") is not None
    
    def set_local_mode(self) -> bool:
        """Enable local control mode"""
        return self._send_command("LOCAL") is not None
    
    def get_motor_current(self) -> Optional[int]:
        """Read motor current (0-100)"""
        response = self._send_command("IMOTOR?")
        if response:
            try:
                # Handle "IMOTOR:xx" format
                if ':' in response:
                    response = response.split(':')[1]
                return int(response)
            except ValueError:
                pass
        return None
    
    def get_errors(self) -> Optional[str]:
        """Read last 5 error codes"""
        return self._send_command("ERRORS?")
    
    def get_status(self) -> dict:
        """Get comprehensive pump status"""
        status = {}
        
        flow = self.get_flow()
        if flow is not None:
            status['flow_ul_min'] = flow
            status['flow_ml_min'] = flow / 1000.0
        
        pressure = self.get_pressure()
        if pressure is not None:
            status['pressure_mpa'] = pressure
        
        current = self.get_motor_current()
        if current is not None:
            status['motor_current'] = current
        
        head = self.get_head_type()
        if head is not None:
            status['head_type_ml'] = head
        
        return status


class AzuraPumpGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AZURA Pump Control")
        self.root.geometry("650x600")
        
        self.pump = None
        self.monitoring = False
        self.monitor_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding=10)
        conn_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, sticky="w", padx=5)
        
        # Auto-detect port button
        ttk.Button(conn_frame, text="Scan Ports", 
                  command=self.scan_ports).grid(row=0, column=1, padx=5)
        
        self.port_var = tk.StringVar(value="Select port...")
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=25)
        self.port_combo.grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", 
                                       command=self.toggle_connection, width=12)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="● Disconnected", 
                                     foreground="red", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=4, padx=10)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=10)
        config_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(config_frame, text="Pump Head:").grid(row=0, column=0, sticky="w", padx=5)
        self.head_var = tk.StringVar(value="10")
        head_combo = ttk.Combobox(config_frame, textvariable=self.head_var, 
                                  values=["10", "50"], state="readonly", width=10)
        head_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Button(config_frame, text="Set Head Type", 
                  command=self.set_head_type).grid(row=0, column=2, padx=5)
        
        ttk.Button(config_frame, text="Remote Mode", 
                  command=self.set_remote).grid(row=0, column=3, padx=5)
        
        ttk.Button(config_frame, text="Local Mode", 
                  command=self.set_local).grid(row=0, column=4, padx=5)
        
        # Flow control frame
        flow_frame = ttk.LabelFrame(main_frame, text="Flow Control", padding=10)
        flow_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(flow_frame, text="Flow Rate (mL/min):").grid(row=0, column=0, 
                                                                sticky="w", padx=5)
        self.flow_var = tk.StringVar(value="5.0")
        flow_entry = ttk.Entry(flow_frame, textvariable=self.flow_var, width=15)
        flow_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(flow_frame, text="Set Flow", 
                  command=self.set_flow).grid(row=0, column=2, padx=5)
        
        # Quick flow buttons
        quick_frame = ttk.Frame(flow_frame)
        quick_frame.grid(row=1, column=0, columnspan=3, pady=5)
        
        for flow in [1, 2, 5, 10]:
            ttk.Button(quick_frame, text=f"{flow} mL/min", 
                      command=lambda f=flow: self.quick_flow(f),
                      width=10).pack(side=tk.LEFT, padx=2)
        
        # Start/Stop buttons
        btn_frame = ttk.Frame(flow_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START", 
                                     command=self.start_pump, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.start_btn.config(style="Green.TButton")
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP", 
                                    command=self.stop_pump, width=20)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status display frame
        status_frame = ttk.LabelFrame(main_frame, text="Real-time Status", padding=10)
        status_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Create a grid for status items
        status_items = [
            ("Current Flow:", "current_flow_label", "-- mL/min"),
            ("Pressure:", "pressure_label", "-- MPa"),
            ("Motor Current:", "current_label", "--"),
            ("Head Type:", "head_label", "-- mL")
        ]
        
        for i, (label, attr, default) in enumerate(status_items):
            ttk.Label(status_frame, text=label, font=("Arial", 10)).grid(
                row=i, column=0, sticky="w", padx=5, pady=3)
            lbl = ttk.Label(status_frame, text=default, 
                          font=("Arial", 12, "bold"), foreground="blue")
            lbl.grid(row=i, column=1, sticky="w", padx=20, pady=3)
            setattr(self, attr, lbl)
        
        # Quick actions frame
        action_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding=10)
        action_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        actions = [
            ("Flush (10 mL/min, 30s)", lambda: self.quick_flush(10, 30)),
            ("Flush (5 mL/min, 60s)", lambda: self.quick_flush(5, 60)),
            ("Check Errors", self.check_errors),
            ("Stop & Disconnect", self.emergency_stop)
        ]
        
        for i, (text, command) in enumerate(actions):
            ttk.Button(action_frame, text=text, command=command,
                      width=20).grid(row=i//2, column=i%2, padx=5, pady=3)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10)
        log_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Log text with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container, height=10, width=70, 
                               state='disabled', wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Configure button styles
        style = ttk.Style()
        style.configure("Green.TButton", foreground="green")
        
        # Initially disable controls
        self.set_controls_state(False)
        
        # Auto-scan ports on startup
        self.root.after(100, self.scan_ports)
        
        self.log("AZURA Pump Control System Ready")
        self.log("Click 'Scan Ports' to find your pump")
    
    def log(self, message):
        """Add message to log with timestamp"""
        self.log_text.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def set_controls_state(self, enabled):
        """Enable/disable pump controls"""
        state = 'normal' if enabled else 'disabled'
        widgets = [self.flow_var, self.start_btn, self.stop_btn]
        for widget in widgets:
            if hasattr(widget, 'config'):
                widget.config(state=state)
    
    def scan_ports(self):
        """Scan for available serial ports"""
        self.log("Scanning for serial ports...")
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.log("No serial ports found!")
            messagebox.showwarning("No Ports", "No serial ports detected.\n\n"
                                 "Check USB connection and drivers.")
            return
        
        port_list = []
        for port in ports:
            port_list.append(port.device)
            self.log(f"Found: {port.device} - {port.description}")
        
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            self.log(f"Found {len(port_list)} port(s)")
    
    def toggle_connection(self):
        """Connect or disconnect from pump"""
        if self.pump is None or not self.pump.ser or not self.pump.ser.is_open:
            # Connect
            port = self.port_var.get()
            if port == "Select port...":
                messagebox.showwarning("No Port", "Please scan and select a port first")
                return
            
            self.log(f"Connecting to {port}...")
            self.pump = AzuraPump(port=port)
            
            if self.pump.connect():
                self.log(f"✓ Connected successfully")
                self.status_label.config(text="● Connected", foreground="green")
                self.connect_btn.config(text="Disconnect")
                self.set_controls_state(True)
                self.start_monitoring()
                
                # Read initial status
                status = self.pump.get_status()
                if 'head_type_ml' in status:
                    self.log(f"Current pump head: {status['head_type_ml']}mL")
            else:
                self.log(f"✗ Failed to connect to {port}")
                messagebox.showerror("Connection Failed", 
                                   f"Could not connect to {port}\n\n"
                                   "Check:\n- USB connection\n- Port selection\n"
                                   "- Pump power")
                self.pump = None
        else:
            # Disconnect
            self.emergency_stop()
    
    def set_head_type(self):
        """Set pump head type"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        head = int(self.head_var.get())
        if self.pump.set_head_type(head):
            self.log(f"✓ Pump head set to {head}mL")
        else:
            self.log("✗ Failed to set pump head")
    
    def set_flow(self):
        """Set flow rate"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        try:
            flow_ml = float(self.flow_var.get())
            if flow_ml < 0 or flow_ml > 50:
                messagebox.showerror("Error", "Flow rate must be 0-50 mL/min")
                return
            
            flow_ul = flow_ml * 1000
            
            if self.pump.set_flow(flow_ul):
                self.log(f"✓ Flow rate set to {flow_ml} mL/min")
            else:
                self.log("✗ Failed to set flow rate")
        except ValueError:
            messagebox.showerror("Error", "Invalid flow rate - enter a number")
    
    def quick_flow(self, flow_ml):
        """Quick set flow rate"""
        self.flow_var.set(str(flow_ml))
        self.set_flow()
    
    def start_pump(self):
        """Start pump"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        if self.pump.start():
            self.log("▶ Pump STARTED")
        else:
            self.log("✗ Failed to start pump")
    
    def stop_pump(self):
        """Stop pump"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        if self.pump.stop():
            self.log("⏹ Pump STOPPED")
        else:
            self.log("✗ Failed to stop pump")
    
    def set_remote(self):
        """Enable remote mode"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        if self.pump.set_remote_mode():
            self.log("✓ Remote mode enabled (manual controls locked)")
    
    def set_local(self):
        """Enable local mode"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        if self.pump.set_local_mode():
            self.log("✓ Local mode enabled (manual controls unlocked)")
    
    def quick_flush(self, flow_ml, duration_sec):
        """Run quick flush routine"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        if messagebox.askyesno("Confirm Flush", 
                              f"Start flushing at {flow_ml} mL/min for {duration_sec} seconds?"):
            self.log(f"Starting flush: {flow_ml} mL/min for {duration_sec}s...")
            
            def flush_thread():
                flow_ul = flow_ml * 1000
                self.pump.set_flow(flow_ul)
                self.pump.start()
                
                for i in range(duration_sec):
                    time.sleep(1)
                    remaining = duration_sec - i - 1
                    if remaining > 0:
                        self.log(f"Flushing... {remaining}s remaining")
                
                self.pump.stop()
                self.log("✓ Flush complete")
            
            threading.Thread(target=flush_thread, daemon=True).start()
    
    def check_errors(self):
        """Check for errors"""
        if not self.pump:
            messagebox.showwarning("Warning", "Not connected to pump")
            return
        
        errors = self.pump.get_errors()
        if errors:
            self.log(f"Error codes: {errors}")
            messagebox.showinfo("Error Status", f"Last errors: {errors}")
        else:
            self.log("No errors reported")
            messagebox.showinfo("Status", "No errors detected")
    
    def emergency_stop(self):
        """Emergency stop and disconnect"""
        if self.pump:
            self.log("Emergency stop initiated...")
            self.stop_monitoring()
            self.pump.stop()
            self.pump.disconnect()
            self.log("✓ Pump stopped and disconnected")
            self.status_label.config(text="● Disconnected", foreground="red")
            self.connect_btn.config(text="Connect")
            self.set_controls_state(False)
            self.pump = None
    
    def start_monitoring(self):
        """Start status monitoring thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop status monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def monitor_loop(self):
        """Monitor pump status continuously"""
        while self.monitoring:
            if self.pump and self.pump.ser and self.pump.ser.is_open:
                try:
                    status = self.pump.get_status()
                    
                    if 'flow_ml_min' in status:
                        self.current_flow_label.config(
                            text=f"{status['flow_ml_min']:.3f} mL/min"
                        )
                    
                    if 'pressure_mpa' in status:
                        self.pressure_label.config(
                            text=f"{status['pressure_mpa']:.2f} MPa"
                        )
                    else:
                        self.pressure_label.config(text="N/A (P 2.1S)")
                    
                    if 'motor_current' in status:
                        self.current_label.config(
                            text=f"{status['motor_current']}"
                        )
                    
                    if 'head_type_ml' in status:
                        self.head_label.config(
                            text=f"{status['head_type_ml']} mL"
                        )
                        
                except Exception as e:
                    self.log(f"Monitor error: {e}")
            
            time.sleep(1)
    
    def on_closing(self):
        """Handle window closing"""
        if self.pump and self.pump.ser and self.pump.ser.is_open:
            if messagebox.askokcancel("Quit", "Stop pump and disconnect?"):
                self.emergency_stop()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = AzuraPumpGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()