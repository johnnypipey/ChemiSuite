"""
Database manager for ChemiSuite data logging
Handles SQLite database operations for logging sessions and data points
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

class DatabaseManager:
    """Manages SQLite database for data logging"""

    def __init__(self, db_path: str = "database/chemisuite.db"):
        """Initialize database manager and create tables if needed"""
        self.db_path = db_path

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database schema
        self._init_database()

    def _init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create logging_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logging_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                interval_seconds INTEGER NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Create data_points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                parameter TEXT NOT NULL,
                value REAL,
                unit TEXT,
                FOREIGN KEY(session_id) REFERENCES logging_sessions(id)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_time
            ON data_points(session_id, timestamp)
        """)

        conn.commit()
        conn.close()

    def create_session(self, name: str, interval_seconds: int, metadata: Dict = None) -> int:
        """Create a new logging session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO logging_sessions (name, start_time, interval_seconds, status, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (name, datetime.now(), interval_seconds, 'running', json.dumps(metadata or {})))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id

    def update_session_status(self, session_id: int, status: str):
        """Update session status (running, paused, stopped)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE logging_sessions
            SET status = ?
            WHERE id = ?
        """, (status, session_id))

        # If stopping, set end_time
        if status == 'stopped':
            cursor.execute("""
                UPDATE logging_sessions
                SET end_time = ?
                WHERE id = ?
            """, (datetime.now(), session_id))

        conn.commit()
        conn.close()

    def record_data_point(self, session_id: int, device_name: str, device_type: str,
                         parameter: str, value: float, unit: str):
        """Record a single data point"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data_points (session_id, timestamp, device_name, device_type, parameter, value, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), device_name, device_type, parameter, value, unit))

        conn.commit()
        conn.close()

    def get_session_data(self, session_id: int, parameter: Optional[str] = None) -> List[Tuple]:
        """Get all data points for a session, optionally filtered by parameter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if parameter:
            cursor.execute("""
                SELECT timestamp, device_name, parameter, value, unit
                FROM data_points
                WHERE session_id = ? AND parameter = ?
                ORDER BY timestamp
            """, (session_id, parameter))
        else:
            cursor.execute("""
                SELECT timestamp, device_name, parameter, value, unit
                FROM data_points
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))

        data = cursor.fetchall()
        conn.close()

        return data

    def get_recent_data(self, session_id: int, minutes: int = 10) -> List[Tuple]:
        """Get data points from the last N minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, device_name, parameter, value, unit
            FROM data_points
            WHERE session_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' minutes')
            ORDER BY timestamp
        """, (session_id, minutes))

        data = cursor.fetchall()
        conn.close()

        return data

    def get_all_sessions(self) -> List[Dict]:
        """Get all logging sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, start_time, end_time, interval_seconds, status, metadata
            FROM logging_sessions
            ORDER BY start_time DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'name': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'interval_seconds': row[4],
                'status': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            })

        conn.close()
        return sessions

    def get_session_info(self, session_id: int) -> Optional[Dict]:
        """Get information about a specific session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, start_time, end_time, interval_seconds, status, metadata
            FROM logging_sessions
            WHERE id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'interval_seconds': row[4],
                'status': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            }
        return None

    def get_data_point_count(self, session_id: int) -> int:
        """Get the number of data points in a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM data_points WHERE session_id = ?
        """, (session_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def delete_session(self, session_id: int):
        """Delete a session and all its data points"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete data points first (foreign key constraint)
        cursor.execute("DELETE FROM data_points WHERE session_id = ?", (session_id,))

        # Delete session
        cursor.execute("DELETE FROM logging_sessions WHERE id = ?", (session_id,))

        conn.commit()
        conn.close()

    def export_to_csv(self, session_id: int, filepath: str):
        """Export session data to CSV file"""
        import csv

        session_info = self.get_session_info(session_id)
        data = self.get_session_data(session_id)

        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header with session info
            writer.writerow(['Session:', session_info['name']])
            writer.writerow(['Start Time:', session_info['start_time']])
            writer.writerow(['End Time:', session_info['end_time'] or 'In Progress'])
            writer.writerow(['Interval (seconds):', session_info['interval_seconds']])
            writer.writerow([])

            # Write data header
            writer.writerow(['Timestamp', 'Device Name', 'Parameter', 'Value', 'Unit'])

            # Write data points
            for row in data:
                writer.writerow(row)

    def import_from_csv(self, filepath: str) -> int:
        """Import session data from CSV file and return new session ID"""
        import csv
        from datetime import datetime

        with open(filepath, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)

            # Read session metadata
            session_name = next(reader)[1]  # Session:, Name
            start_time_str = next(reader)[1]  # Start Time:, value
            end_time_str = next(reader)[1]  # End Time:, value
            interval_seconds = int(next(reader)[1])  # Interval (seconds):, value
            next(reader)  # Skip blank line
            next(reader)  # Skip data header

            # Create new session
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO logging_sessions (name, start_time, end_time, interval_seconds, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_name, start_time_str, end_time_str if end_time_str != 'In Progress' else None,
                  interval_seconds, 'stopped', json.dumps({})))

            session_id = cursor.lastrowid

            # Read and insert data points
            for row in reader:
                timestamp, device_name, parameter, value, unit = row

                cursor.execute("""
                    INSERT INTO data_points (session_id, timestamp, device_name, device_type, parameter, value, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, timestamp, device_name, 'imported', parameter, float(value), unit))

            conn.commit()
            conn.close()

            return session_id
