import serial
import socket
import keyboard
import re
import serial
from datetime import datetime, timezone
from utils import haversine_distance
from sensor import Sensor


class GPSListener(Sensor):
    def __init__(self,serial_com,stream,callback=None):
        super().__init__()
        self.stream = stream
        self.ser = None
        self.serial_com = serial_com
        self.is_debug = False
        self.callback = callback
        self.running = False
        
        self.previous_position = None
        self.previous_speed = None
        self.previous_time = None
        #self.start()

    def connect(self):
        try:
            self.ser = serial.Serial(self.serial_com, 9600, timeout=1)
            self.running = True
            self._notify_status_change(True)
            self._notify_message(f"GPS: Connected on {self.serial_com}", "Success")
            return f"serial port {self.serial_com} connected"
        except serial.SerialException as e:
            self._notify_status_change(False)
            self._notify_message(f"GPS: Error - {e}", "Error")
            return f"{e}"
    
    def parse_nmea_sentence(self, nmea_sentence):
        """
        Parse an NMEA sentence to extract latitude, longitude, timestamp, and number of satellites.
        Supports both GNGGA and GNRMC sentences for location data.
        """
        if nmea_sentence.startswith("$GNGGA") or nmea_sentence.startswith("$GNRMC"):
            parts = nmea_sentence.split(",")
            try:
                raw_lat = parts[2]
                lat_dir = parts[3]
                raw_lon = parts[4]
                lon_dir = parts[5]
                raw_time = parts[1]
                num_satellites = int(parts[7]) if nmea_sentence.startswith("$GNGGA") else None
                altitude = float(parts[9]) if nmea_sentence.startswith("$GNGGA") else None

                if raw_lat and raw_lon and raw_time:
                    lat_deg = int(raw_lat[:2])
                    lat_min = float(raw_lat[2:])
                    latitude = lat_deg + (lat_min / 60.0)
                    if lat_dir == "S":
                        latitude = -latitude

                    lon_deg = int(raw_lon[:3])
                    lon_min = float(raw_lon[3:])
                    longitude = lon_deg + (lon_min / 60.0)
                    if lon_dir == "W":
                        longitude = -longitude

                    hours = int(raw_time[:2])
                    minutes = int(raw_time[2:4])
                    seconds = int(raw_time[4:6])
                    timestamp = datetime.now(timezone.utc).replace(hour=hours, minute=minutes, second=seconds, microsecond=0)

                    return raw_time, timestamp, num_satellites, latitude, longitude, altitude
            except (ValueError, IndexError):
                pass
        return None, None, None, None, None, None
    
    def start(self):
        """
        Read data from the GPS device, calculate speed, acceleration, and number of satellites.
        """
        if self.ser is None:
            return
        while self.running:
            line = self.ser.readline().decode("ascii", errors="ignore").strip()
            if line:
                raw_time, timestamp, num_satellites, latitude, longitude, altitude = self.parse_nmea_sentence(line)
                if latitude is not None and longitude is not None and timestamp is not None:
                    if self.previous_position and self.previous_time:
                        distance = haversine_distance(
                            self.previous_position[0], self.previous_position[1],
                            latitude, longitude
                        )
                        time_interval = (timestamp - self.previous_time).total_seconds()

                        if time_interval > 0:
                            speed = distance / time_interval
                            if self.previous_speed is not None:
                                acceleration = (speed - self.previous_speed) / time_interval
                                #print(f"Time: {raw_time}, Satellites: {num_satellites}, Latitude: {'{0:.14f}'.format(latitude)}, Longitude: {'{0:.14f}'.format(longitude)}, Altitude: {'{0:.4f}'.format(altitude)}, Speed: {speed:.2f} m/s, Acceleration: {acceleration:.2f} m/s²")
                                data = f"E;1;USB_GPS;1;;;;GPS;{raw_time};{num_satellites};{latitude};{longitude};{altitude};{speed:.2f};{acceleration:.2f}\r\n"
                                # send the data to the UDP client
                                try:
                                    if self.stream:
                                        self.stream.send(data.encode())
                                        #self._imotions_Socket.sendto(data.encode(), (self._udp_ip, self._udp_port))
                                except:
                                    print("failed to send to imotions")
                            #else:
                                #print(f"Time: {raw_time}, Satellites: {num_satellites}, Latitude: {'{0:.14f}'.format(latitude)}, Longitude: {'{0:.14f}'.format(longitude)}, Speed: {speed:.2f} m/s, Acceleration: N/A")

                            self.previous_speed = speed
                    else:
                        print(f"Time: {raw_time}, Satellites: {num_satellites}, Latitude: {'{0:.14f}'.format(latitude)}, Longitude: {'{0:.14f}'.format(longitude)}, Speed: N/A, Acceleration: N/A")

                    self.previous_position = (latitude, longitude)
                    self.previous_time = timestamp
    
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self._notify_status_change(False)
        self._notify_message("GPS: Disconnected", "Info")

    def status(self):
        return self.running