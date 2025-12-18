import serial
import time
import threading
from typing import Optional, Dict, Callable
from dataclasses import dataclass

@dataclass
class MotorStatus:
    """Represents the current status of a motor"""
    name: str
    angle: float
    moving: bool
    enabled: bool
    timestamp: float

class MotorController:
    """
    Python interface for controlling four stepper motors via Arduino.
    
    Example usage:
        controller = MotorController('/dev/ttyUSB0')
        controller.connect()
        
        # Move to predefined positions
        controller.move_to_gas('A')
        controller.move_to_vacuum('B')
        
        # Move to specific angle
        controller.move_to_angle('C', 45.0)
        
        # Control enable pins
        controller.enable_motor('D')
        controller.disable_motor('D')
        
        # Get status
        status = controller.get_motor_status('A')
        print(f"Motor A at {status.angle}°")
        
        # Monitor all motors
        controller.start_monitoring(callback=lambda statuses: print(statuses))
    """
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.motor_statuses: Dict[str, MotorStatus] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.response_callbacks: Dict[str, Callable] = {}
        
    def connect(self) -> bool:
        """Establish serial connection to Arduino"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino reset
            
            # Read initial READY message
            while self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                if line.startswith('READY'):
                    print(f"Connected: {line}")
                    return True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        self.stop_monitoring()
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def _send_command(self, command: str) -> bool:
        """Send command to Arduino"""
        if not self.serial or not self.serial.is_open:
            print("Error: Serial port not open")
            return False
        
        try:
            self.serial.write(f"{command}\n".encode('utf-8'))
            self.serial.flush()
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    def _parse_status(self, line: str):
        """Parse STATUS message from Arduino"""
        # Format: STATUS|A,90.00,1,1|B,0.00,0,1|C,270.00,1,1|D,45.00,0,1|END
        if not line.startswith('STATUS|') or not line.endswith('|END'):
            return
        
        parts = line[7:-4].split('|')  # Remove STATUS| and |END
        for part in parts:
            fields = part.split(',')
            if len(fields) == 4:
                name = fields[0]
                try:
                    angle = float(fields[1]) if fields[1] != 'NaN' else float('nan')
                except ValueError:
                    angle = float('nan')
                moving = fields[2] == '1'
                enabled = fields[3] == '1'
                
                self.motor_statuses[name] = MotorStatus(
                    name=name,
                    angle=angle,
                    moving=moving,
                    enabled=enabled,
                    timestamp=time.time()
                )
    
    def _parse_response(self, line: str):
        """Parse RESPONSE message from Arduino"""
        # Format: RESPONSE|A|OK|Moving to 90.00 degrees|END
        if not line.startswith('RESPONSE|') or not line.endswith('|END'):
            return
        
        parts = line[9:-4].split('|')  # Remove RESPONSE| and |END
        if len(parts) == 3:
            motor, status, message = parts
            print(f"[{motor}] {status}: {message}")
    
    def _read_loop(self):
        """Background thread to read serial data"""
        while self.monitoring and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line.startswith('STATUS'):
                        self._parse_status(line)
                    elif line.startswith('RESPONSE'):
                        self._parse_response(line)
                time.sleep(0.01)
            except Exception as e:
                print(f"Read error: {e}")
                break
    
    def start_monitoring(self):
        """Start background thread to monitor motor status"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring thread"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
    
    # --- Motor Control Commands ---
    
    def move_to_angle(self, motor: str, angle: float) -> bool:
        """Move motor to specific angle (0-360 degrees)"""
        if not 0 <= angle <= 360:
            print(f"Error: Angle must be between 0 and 360")
            return False
        return self._send_command(f"{motor.upper()} ANGLE {angle}")
    
    def move_to_gas(self, motor: str) -> bool:
        """Move motor to GAS position (90°)"""
        return self._send_command(f"{motor.upper()} GAS")
    
    def move_to_closed(self, motor: str) -> bool:
        """Move motor to CLOSED position (0°)"""
        return self._send_command(f"{motor.upper()} CLOSED")
    
    def move_to_vacuum(self, motor: str) -> bool:
        """Move motor to VACUUM position (270°)"""
        return self._send_command(f"{motor.upper()} VACUUM")
    
    def enable_motor(self, motor: str) -> bool:
        """Enable motor driver"""
        return self._send_command(f"{motor.upper()} ENABLE")
    
    def disable_motor(self, motor: str) -> bool:
        """Disable motor driver"""
        return self._send_command(f"{motor.upper()} DISABLE")
    
    def stop_motor(self, motor: str) -> bool:
        """Stop motor movement immediately"""
        return self._send_command(f"{motor.upper()} STOP")
    
    def get_status(self) -> bool:
        """Request status update from all motors"""
        return self._send_command("STATUS")
    
    def get_motor_status(self, motor: str) -> Optional[MotorStatus]:
        """Get latest status for specific motor"""
        return self.motor_statuses.get(motor.upper())
    
    def get_all_statuses(self) -> Dict[str, MotorStatus]:
        """Get latest status for all motors"""
        return self.motor_statuses.copy()
    
    def wait_for_motor(self, motor: str, timeout: float = 30.0) -> bool:
        """Wait until motor stops moving"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_motor_status(motor)
            if status and not status.moving:
                return True
            time.sleep(0.1)
        return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize controller
    controller = MotorController('/dev/ttyUSB0')  # Change to your port
    
    if not controller.connect():
        print("Failed to connect to Arduino")
        exit(1)
    
    # Start monitoring for continuous status updates
    controller.start_monitoring()
    time.sleep(0.5)
    
    print("\n=== Motor Control Demo ===\n")
    
    # Example 1: Move motors to predefined positions
    print("Moving Motor A to GAS position...")
    controller.move_to_gas('A')
    controller.wait_for_motor('A')
    
    print("\nMoving Motor B to VACUUM position...")
    controller.move_to_vacuum('B')
    controller.wait_for_motor('B')
    
    # Example 2: Move to specific angle
    print("\nMoving Motor C to 45 degrees...")
    controller.move_to_angle('C', 45.0)
    controller.wait_for_motor('C')
    
    # Example 3: Get motor status
    print("\n=== Current Motor Positions ===")
    for motor_name in ['A', 'B', 'C', 'D']:
        status = controller.get_motor_status(motor_name)
        if status:
            print(f"Motor {status.name}: {status.angle:.2f}° "
                  f"[{'MOVING' if status.moving else 'STOPPED'}] "
                  f"[{'ENABLED' if status.enabled else 'DISABLED'}]")
    
    # Example 4: Disable a motor
    print("\nDisabling Motor D...")
    controller.disable_motor('D')
    time.sleep(0.5)
    
    # Example 5: Re-enable and move
    print("\nRe-enabling Motor D and moving to CLOSED...")
    controller.enable_motor('D')
    time.sleep(0.2)
    controller.move_to_closed('D')
    controller.wait_for_motor('D')
    
    print("\n=== Demo Complete ===")
    
    # Cleanup
    controller.disconnect()