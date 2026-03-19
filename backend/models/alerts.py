class Alert:
    def __init__(self, id, message, level, timestamp):
        self.id = id  # Unique identifier for the alert
        self.message = message  # The notification message
        self.level = level  # Severity level (e.g., INFO, WARNING, ERROR)
        self.timestamp = timestamp  # When the alert was created

    def __repr__(self):
        return f"<Alert(id={self.id}, message='{self.message}', level='{self.level}', timestamp='{self.timestamp}')>"