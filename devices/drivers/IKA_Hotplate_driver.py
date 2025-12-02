"""
IKA RET Control-visc Hotplate Driver
Serial communication driver for controlling IKA hotplate via RS-232/USB
Compatible with ChemiSuite device architecture
"""

import serial
import time
from typing import Tuple


class IKAHotplateDriver:
    """Driver for IKA RET control-visc heated magnetic stirrer"""

    def __init__(self, port: str, baudrate: int = 9600):
        """
        Initialize connection to IKA hotplate

        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Communication speed (default 9600 as per manual)
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False

    def connect(self) -> Tuple[bool, str]:
        """
        Establish serial connection to the device

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            time.sleep(0.5)  # Allow connection to stabilize

            # Clear any startup garbage
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.2)

            self.connected = True

            # Try to get device name to verify connection
            device_name = self.get_device_name()
            if device_name:
                return True, f"Connected to {device_name}"
            else:
                return True, "Connected to IKA Hotplate"

        except serial.SerialException as e:
            self.connected = False
            return False, f"Failed to connect to {self.port}: {str(e)}"
        except Exception as e:
            self.connected = False
            return False, f"Connection error: {str(e)}"

    def disconnect(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.connected = False
            except:
                pass

    def _send_command(self, command: str) -> str:
        """
        Send command and receive response

        Args:
            command: NAMUR command string

        Returns:
            Response from device
        """
        if not self.connected or not self.ser:
            return ""

        try:
            # Clear input buffer
            self.ser.reset_input_buffer()
            time.sleep(0.05)

            # Send command with CR LF termination
            cmd_bytes = (command + '\r\n').encode('ascii')
            self.ser.write(cmd_bytes)
            time.sleep(0.15)  # Give device time to respond

            # Read response
            response = self.ser.readline().decode('ascii', errors='ignore').strip()

            return response

        except Exception as e:
            print(f"Communication error: {e}")
            return ""

    def get_device_name(self) -> str:
        """Get device identification"""
        return self._send_command('IN_NAME')

    def get_device_type(self) -> str:
        """Get device type"""
        return self._send_command('IN_TYPE')

    def get_software_version(self) -> str:
        """Get software version"""
        return self._send_command('IN_SOFTWARE_ID')

    # Temperature control (X=1: medium temp, X=2: hotplate temp)

    def set_temperature(self, temp: float, sensor_type: int = 2) -> bool:
        """
        Set target temperature

        Args:
            temp: Temperature in °C (0-340)
            sensor_type: 1=medium (external sensor), 2=hotplate

        Returns:
            True if command was sent successfully
        """
        if not 0 <= temp <= 340:
            return False

        self._send_command(f'OUT_SP_{sensor_type} {temp}')
        return True  # Command was sent, device doesn't always respond

    def get_temperature(self, sensor_type: int = 2) -> float:
        """
        Get current temperature

        Args:
            sensor_type: 1=medium, 2=hotplate, 3=safety, 7=carrier fluid

        Returns:
            Current temperature in °C
        """
        response = self._send_command(f'IN_PV_{sensor_type}')
        try:
            # Response format should be like "IN_PV_2 25.5" or just "25.5"
            # Remove the command echo if present
            response = response.replace(f'IN_PV_{sensor_type}', '').strip()

            # Try to extract the numeric value
            parts = response.split()
            for part in parts:
                try:
                    value = float(part)
                    return value
                except ValueError:
                    continue

            return 0.0
        except Exception:
            return 0.0

    def get_target_temperature(self, sensor_type: int = 2) -> float:
        """Get target temperature setpoint"""
        response = self._send_command(f'IN_SP_{sensor_type}')
        try:
            response = response.replace(f'IN_SP_{sensor_type}', '').strip()

            parts = response.split()
            for part in parts:
                try:
                    value = float(part)
                    return value
                except ValueError:
                    continue

            return 0.0
        except Exception:
            return 0.0

    def start_heating(self, sensor_type: int = 2) -> bool:
        """Start heating function"""
        self._send_command(f'START_{sensor_type}')
        return True  # Command was sent, device doesn't always respond

    def stop_heating(self, sensor_type: int = 2) -> bool:
        """Stop heating function"""
        self._send_command(f'STOP_{sensor_type}')
        return True  # Command was sent, device doesn't always respond

    # Stirring control (X=4)

    def set_speed(self, rpm: int) -> bool:
        """
        Set stirring speed

        Args:
            rpm: Speed in RPM (0-1700)

        Returns:
            True if command was sent successfully
        """
        if not 0 <= rpm <= 1700:
            return False

        self._send_command(f'OUT_SP_4 {rpm}')
        return True  # Command was sent, device doesn't always respond

    def get_speed(self) -> float:
        """Get current stirring speed in RPM"""
        response = self._send_command('IN_PV_4')
        try:
            response = response.replace('IN_PV_4', '').strip()

            parts = response.split()
            for part in parts:
                try:
                    value = float(part)
                    return value
                except ValueError:
                    continue

            return 0.0
        except Exception:
            return 0.0

    def get_target_speed(self) -> float:
        """Get target speed setpoint"""
        response = self._send_command('IN_SP_4')
        try:
            response = response.replace('IN_SP_4', '').strip()

            parts = response.split()
            for part in parts:
                try:
                    value = float(part)
                    return value
                except ValueError:
                    continue

            return 0.0
        except Exception:
            return 0.0

    def start_stirring(self) -> bool:
        """Start stirring motor"""
        self._send_command('START_4')
        return True  # Command was sent, device doesn't always respond

    def stop_stirring(self) -> bool:
        """Stop stirring motor"""
        self._send_command('STOP_4')
        return True  # Command was sent, device doesn't always respond

    # Safety and monitoring

    def get_status(self) -> Tuple[float, float, float]:
        """
        Get current status

        Returns:
            Tuple of (temperature, speed, viscosity_trend)
        """
        temp = self.get_temperature(2)  # Use hotplate temp
        speed = self.get_speed()
        visc_response = self._send_command('IN_PV_5')
        try:
            parts = visc_response.split()
            if len(parts) >= 2:
                viscosity = float(parts[-1])
            else:
                viscosity = 0.0
        except (ValueError, IndexError):
            viscosity = 0.0

        return temp, speed, viscosity

    def reset(self) -> bool:
        """Reset device (emergency stop)"""
        response = self._send_command('RESET')
        return response != ""

    def set_watchdog(self, mode: int, timeout: int) -> bool:
        """
        Enable watchdog function for safety

        Args:
            mode: 1=stop all on timeout, 2=switch to safety values
            timeout: Timeout in seconds (20-1500)

        Returns:
            True if command was sent successfully
        """
        if mode == 1:
            response = self._send_command(f'OUT_WD1@{timeout}')
        elif mode == 2:
            response = self._send_command(f'OUT_WD2@{timeout}')
        else:
            return False

        return response != ""

    def set_safety_temperature(self, temp: float) -> bool:
        """Set watchdog safety temperature limit"""
        response = self._send_command(f'OUT_SP_12@{temp}')
        return response != ""

    def set_safety_speed(self, rpm: int) -> bool:
        """Set watchdog safety speed limit"""
        response = self._send_command(f'OUT_SP_42@{rpm}')
        return response != ""
