import serial
import socket
import keyboard
import re
import serial
from datetime import datetime
from utils import haversine_distance
from sensor import Sensor


class TriggerBoxListener(Sensor):
    def __init__(self, triggers, serial_com,stream,callback=None):
        super().__init__()
        self.triggers = triggers
        self.stream = stream
        self.ser = None
        self.serial_com = serial_com
        self.is_debug = False
        self.callback = callback
        self.running = False
        #self.start()

    def connect(self):
        try:
            self.ser = serial.Serial(self.serial_com, 9600, timeout=1)
            self.running = True
            self._notify_status_change(True)
            self._notify_message(f"Trigger Box: Connected on {self.serial_com}", "Success")
        except serial.SerialException as e:
            self._notify_status_change(False)
            self._notify_message(f"Trigger Box: Error - {e}", "Error")
    
    def parse_trigger(self, trigger_index):
        """
        Get the trigger command from the trigger box (Arduino Uno)
        1 = FP_LEFT
        2 = FP_RIGHT
        3 = DRIVE
        4 = DONE
        """
        for i, trigger in enumerate(self.triggers):
            if str(i+1) == trigger_index:
                return trigger
        return None
    
    def start(self):
        """
        Read data from the GPS device, calculate speed, acceleration, and number of satellites.
        """
        if self.ser is None:
            return
        while self.running:
            line = self.ser.readline().decode("ascii", errors="ignore").strip()
            if line:
                cmd = self.parse_trigger(line)
                if cmd is not None:
                    data = f"E;1;API_TRIGGER_BOX;1;;;;Trigger;{cmd}\r\n"
                    
                    # send the data to the UDP client
                    try:
                        if self.stream:
                            self.stream.send(data.encode())
                    except:
                        self._notify_status_change(False)
                        self._notify_message(f"Trigger Box: Failed to sent to IMotions", "Error")
    
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self._notify_status_change(False)
        self._notify_message("Trigger Box: Disconnected", "Info")

    def status(self):
        return self.running

