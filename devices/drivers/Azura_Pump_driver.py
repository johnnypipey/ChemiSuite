"""
AZURA Pump P 2.1S/P 4.1S Driver
Based on AZURA Pump Instructions V6870
RS-232 specs: 9600 baud, 8 bit, 1 stop bit, no parity
"""

import serial
import time
from typing import Optional


class AzuraPumpDriver:
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

    def is_connected(self) -> bool:
        """Check if pump is connected"""
        return self.ser is not None and self.ser.is_open

    def _send_command(self, command: str) -> Optional[str]:
        """Send command and return response"""
        if not self.ser or not self.ser.is_open:
            return None

        try:
            self.ser.reset_input_buffer()
            cmd = command.strip() + '\r'  # Use \r only, not \r\n
            self.ser.write(cmd.encode('ascii'))
            time.sleep(0.1)
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
