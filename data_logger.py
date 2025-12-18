"""
Core data logging service for ChemiSuite
Manages background polling and data collection from devices
"""

import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from database.db_manager import DatabaseManager

class DataLogger:
    """Central data logging service"""

    def __init__(self):
        """Initialize data logger"""
        self.db = DatabaseManager()
        self.active_session_id = None
        self.polling_thread = None
        self.running = False
        self.paused = False

        # Configuration for current session
        self.devices_to_log = []  # List of device dicts with their drivers
        self.parameters_to_log = {}  # Dict: device_name -> [parameters]
        self.interval_seconds = 5

        # Statistics
        self.total_data_points = 0
        self.last_poll_time = None
        self.poll_count = 0

    def start_session(self, session_name: str, devices: List[Dict],
                     parameters: Dict[str, List[str]], interval_seconds: int = 5,
                     metadata: Dict = None):
        """
        Start a new logging session

        Args:
            session_name: Name for this logging session
            devices: List of device objects to log from
            parameters: Dict mapping device_name to list of parameters to log
            interval_seconds: How often to poll devices (in seconds)
            metadata: Optional metadata to store with session
        """
        if self.running:
            raise RuntimeError("A logging session is already running. Stop it first.")

        # Create session in database
        self.active_session_id = self.db.create_session(
            name=session_name,
            interval_seconds=interval_seconds,
            metadata=metadata or {}
        )

        # Store configuration
        self.devices_to_log = devices
        self.parameters_to_log = parameters
        self.interval_seconds = interval_seconds

        # Reset statistics
        self.total_data_points = 0
        self.poll_count = 0
        self.last_poll_time = None

        # Start polling thread
        self.running = True
        self.paused = False
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()

        return self.active_session_id

    def stop_session(self):
        """Stop the current logging session"""
        if not self.running:
            return

        self.running = False

        # Wait for polling thread to finish
        if self.polling_thread:
            self.polling_thread.join(timeout=5)

        # Update session status in database
        if self.active_session_id:
            self.db.update_session_status(self.active_session_id, 'stopped')

        # Clear configuration
        self.active_session_id = None
        self.devices_to_log = []
        self.parameters_to_log = {}

    def pause_session(self):
        """Pause data collection without stopping the session"""
        if self.running and not self.paused:
            self.paused = True
            if self.active_session_id:
                self.db.update_session_status(self.active_session_id, 'paused')

    def resume_session(self):
        """Resume a paused session"""
        if self.running and self.paused:
            self.paused = False
            if self.active_session_id:
                self.db.update_session_status(self.active_session_id, 'running')

    def _polling_loop(self):
        """Background polling loop that collects data from devices"""
        while self.running:
            if not self.paused:
                self._poll_devices()
                self.poll_count += 1
                self.last_poll_time = datetime.now()

            # Sleep for the specified interval
            time.sleep(self.interval_seconds)

    def _poll_devices(self):
        """Poll all configured devices and record data points"""
        for device in self.devices_to_log:
            device_name = device['name']
            device_type = device['type']
            driver = device.get('driver')

            # Skip if device has no driver or isn't connected
            if not driver:
                continue

            # Get parameters to log for this device
            params = self.parameters_to_log.get(device_name, [])

            # Get loggable parameters configuration from device
            loggable_params = device.get('loggable_parameters', {})

            for param_name in params:
                if param_name not in loggable_params:
                    continue

                param_config = loggable_params[param_name]

                try:
                    # Call the device method to get the value
                    method_name = param_config['method']
                    method = getattr(driver, method_name, None)

                    if method:
                        # Call method with configured arguments
                        args = param_config.get('args', {})
                        value = method(**args)

                        # Record the data point
                        if value is not None:
                            self.db.record_data_point(
                                session_id=self.active_session_id,
                                device_name=device_name,
                                device_type=device_type,
                                parameter=param_name,
                                value=float(value),
                                unit=param_config['unit']
                            )
                            self.total_data_points += 1

                except Exception as e:
                    # Silently ignore errors during polling (device might be disconnected)
                    print(f"Error polling {device_name}.{param_name}: {e}")
                    pass

    def get_session_status(self) -> Dict:
        """Get current session status and statistics"""
        if not self.active_session_id:
            return {
                'active': False,
                'session_id': None,
                'status': 'No active session'
            }

        session_info = self.db.get_session_info(self.active_session_id)

        # Calculate elapsed time
        start_time = datetime.fromisoformat(session_info['start_time'])
        elapsed = datetime.now() - start_time

        # Calculate data points stored in database
        db_data_points = self.db.get_data_point_count(self.active_session_id)

        return {
            'active': True,
            'session_id': self.active_session_id,
            'session_name': session_info['name'],
            'status': 'Paused' if self.paused else 'Running',
            'start_time': session_info['start_time'],
            'elapsed_seconds': int(elapsed.total_seconds()),
            'elapsed_formatted': str(elapsed).split('.')[0],  # Remove microseconds
            'poll_count': self.poll_count,
            'data_points': db_data_points,
            'interval_seconds': self.interval_seconds,
            'last_poll': self.last_poll_time.isoformat() if self.last_poll_time else None
        }

    def get_all_sessions(self) -> List[Dict]:
        """Get all logging sessions from database"""
        return self.db.get_all_sessions()

    def get_session_data(self, session_id: int, parameter: Optional[str] = None):
        """Get data for a specific session"""
        return self.db.get_session_data(session_id, parameter)

    def get_recent_data(self, session_id: int, minutes: int = 10):
        """Get recent data points for live plotting"""
        return self.db.get_recent_data(session_id, minutes)

    def export_session_to_csv(self, session_id: int, filepath: str):
        """Export a session to CSV file"""
        self.db.export_to_csv(session_id, filepath)

    def delete_session(self, session_id: int):
        """Delete a session and all its data"""
        # Don't allow deleting active session
        if session_id == self.active_session_id:
            raise RuntimeError("Cannot delete active session. Stop it first.")

        self.db.delete_session(session_id)

    def import_session_from_csv(self, filepath: str) -> int:
        """Import a session from CSV file"""
        return self.db.import_from_csv(filepath)


# Global data logger instance
data_logger = DataLogger()
