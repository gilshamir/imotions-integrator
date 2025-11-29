from datetime import datetime, timezone
from sensor import Sensor
import asyncio
import struct
import threading
import json
import logging

from bleak import BleakClient, BleakScanner

logger = logging.getLogger(__name__)

# Standard BLE Heart Rate Measurement characteristic UUID
HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


class H10Listener(Sensor):
    def __init__(self, stream, callback=None):
        super().__init__()
        self.stream = stream
        self.is_debug = False
        self.callback = callback
        self.running = False
        self.device = None
        self.client = None
        self.bg_thread = None
        self.event_loop = None
        

    def connect(self):
        """Try to connect to H10 device via BLE scan."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.event_loop = loop
            device = loop.run_until_complete(self._scan_and_connect())
            self.device = device
            if device:
                self._notify_status_change(True)
                self._notify_message(f"H10: Connected to H10 ({device.address})", "Success")
                logger.info(f"H10 device found: {device.address} - {device.name}")
            else:
                self._notify_status_change(False)
                self._notify_message("H10: Device not found", "Error")
        except Exception as e:
            self._notify_status_change(False)
            self._notify_message(f"H10: Error connecting - {e}", "Error")
            logger.error(f"Error connecting to H10: {e}")
    
    async def _scan_and_connect(self):
        """Scan for Polar H10 and return device."""
        try:
            logger.info("Scanning for Polar H10...")
            devices = await BleakScanner.discover(timeout=5.0)
            for d in devices:
                name = (d.name or "").lower()
                if "polar" in name or "h10" in name:
                    return d
            logger.warning("No Polar H10 found in scan")
            return None
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return None
    
    def start(self):
        """Start listening to H10 data stream in background thread."""
        if not self.device:
            logger.error("Not connected to device. Call connect() first.")
            return
        
        self.running = True
        self.bg_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.bg_thread.start()
        logger.info("H10 listener started")
    
    def _run_listener(self):
        """Run the async event loop in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._listen())
        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            self.running = False
    
    async def _listen(self):
        """Connect to device and subscribe to HR notifications."""
        try:
            async with BleakClient(self.device) as client:
                self.client = client
                logger.info(f"Connected to {self.device.address}")
                
                def hr_handler(sender, data):
                    """Handle incoming HR data."""
                    try:
                        parsed = self._parse_heart_rate(data)
                        if parsed and 'hr' in parsed:
                            self._send_to_stream(parsed)
                    except Exception as e:
                        logger.error(f"Error handling HR data: {e}")
                
                await client.start_notify(HR_CHAR_UUID, hr_handler)
                logger.info("Subscribed to HR notifications")
                
                # Keep listening while running
                while self.running:
                    await asyncio.sleep(0.1)
                
                await client.stop_notify(HR_CHAR_UUID)
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    def _parse_heart_rate(self, data: bytearray):
        """Parse BLE Heart Rate Measurement characteristic."""
        if not data or len(data) < 2:
            return {}
        
        flags = data[0]
        hr_format_uint16 = bool(flags & 0x01)
        energy_expended_present = bool(flags & 0x08)
        rr_present = bool(flags & 0x10)
        
        offset = 1
        if hr_format_uint16:
            hr, = struct.unpack_from('<H', data, offset)
            offset += 2
        else:
            hr, = struct.unpack_from('<B', data, offset)
            offset += 1
        
        # Skip Energy Expended if present
        if energy_expended_present:
            offset += 2
        
        rr_intervals = []
        if rr_present:
            # RR-intervals are uint16 in 1/1024 sec units
            while offset + 1 < len(data):
                rr_raw, = struct.unpack_from('<H', data, offset)
                rr_seconds = rr_raw / 1024.0
                rr_intervals.append(rr_seconds)
                offset += 2
        
        return {"hr": hr, "rr": rr_intervals}
    
    def _send_to_stream(self, data):
        """Format and send HR data to the stream."""
        try:
            # Only keep the last RR interval if multiple are present
            rr_intervals = data.get("rr", [])
            rr_to_send = rr_intervals[-1] if rr_intervals else 0
            
            data = f"E;1;Polar;1;;;;H10;{data.get('hr')};{rr_to_send}\r\n"
            # send the data to the UDP client
            try:
                if self.stream:
                    self.stream.send(data.encode())
            except:
                print("failed to send to imotions")
            
            if self.is_debug:
                logger.debug(f"{data}")
            
            if self.callback:
                self.callback(data)
        except Exception as e:
            logger.error(f"Error sending to stream: {e}")
    
    def stop(self):
        """Stop the listener and close connection."""
        self.running = False
        if self.bg_thread:
            self.bg_thread.join(timeout=2.0)
        self._notify_status_change(False)
        self._notify_message("H10: Disconnected", "Info")
        logger.info("H10 listener stopped")        

    def status(self):
        """Return the current status of the listener."""
        return self.running


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    
    # Mock stream for testing (prints to stdout)
    class MockStream:
        def sendall(self, data):
            print(f"[STREAM] {data.decode()}", file=sys.stdout)
    
    stream = MockStream()
    
    print("Starting H10 listener test...")
    print("Make sure your Polar H10 is powered on and nearby.\n")
    
    h10 = H10Listener(stream=stream)
    
    # Connect to device
    result = h10.connect()
    print(f"Connect result: {result}\n")
    
    if h10.device:
        # Start listening
        h10.start()
        print("Listening for HR data... Press Ctrl-C to stop.\n")
        
        try:
            while h10.status():
                import time
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            h10.stop()
            print("H10 listener stopped.")
    else:
        print("Failed to find H10 device.")