from abc import ABC, abstractmethod

class Sensor(ABC):
    """Abstract base class for all sensors."""

    def __init__(self):
        self.connected = False
        self._status_callbacks = []
        self._message_callbacks = []

    @abstractmethod
    def connect(self):
        """Connect to the sensor hardware or network."""
        pass

    @abstractmethod
    def start(self):
        """Start the sensor readings or data stream."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the sensor readings or data stream."""
        pass

    @abstractmethod
    def status(self):
        """Return the current status of the sensor."""
        pass
    
    def is_connected(self):
        """Return whether the sensor is currently connected."""
        return self.connected
    
    def register_status_callback(self, callback):
        """Register a callback to be called when connection status changes.
        
        callback should accept one argument: the new connected state (bool)
        """
        self._status_callbacks.append(callback)
    
    def register_message_callback(self, callback):
        """Register a callback to be called when a message is generated.
        
        callback should accept two arguments: message (str) and message_type (str)
        """
        self._message_callbacks.append(callback)
    
    def _notify_status_change(self, connected):
        """Notify all registered callbacks of a status change."""
        self.connected = connected
        for callback in self._status_callbacks:
            try:
                callback(connected)
            except Exception as e:
                print(f"Error in status callback: {e}")
    
    def _notify_message(self, message, message_type="Normal"):
        """Notify all registered callbacks of a message."""
        for callback in self._message_callbacks:
            try:
                callback(message, message_type)
            except Exception as e:
                print(f"Error in message callback: {e}")