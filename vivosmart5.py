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


class Vivosmart5Listener(Sensor):
    def __init__(self, stream, callback=None, address=None):
        super().__init__()
        self.stream = stream
        self.is_debug = False
        self.callback = callback
        self.running = False
        self.device = None
        self.client = None
        self.bg_thread = None
        self.event_loop = None
        self.address = address
        

    def connect(self):
        """Try to connect to Vivosmart 5 device via BLE scan or direct address."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.event_loop = loop
            device = loop.run_until_complete(self._scan_and_connect())
            self.device = device
            if device:
                self._notify_status_change(True)
                self._notify_message(f"Vivosmart5: Connected to Vivosmart 5 ({device.address})", "Success")
                logger.info(f"Vivosmart 5 device found: {device.address} - {device.name}")
            else:
                self._notify_status_change(False)
                self._notify_message("Vivosmart5: Device not found", "Error")
        except Exception as e:
            self._notify_status_change(False)
            self._notify_message(f"Vivosmart5: Error connecting - {e}", "Error")
            logger.error(f"Error connecting to Vivosmart 5: {e}")
    
    async def _scan_and_connect(self):
        """Scan for Garmin Vivosmart 5 or connect to specific address."""
        try:
            # If address provided, try direct connection first
            if self.address:
                logger.info(f"Attempting to connect to address {self.address}...")
                device = await BleakScanner.find_device_by_address(self.address, timeout=5.0)
                if device:
                    return device
            
            logger.info("Scanning for Garmin Vivosmart 5...")
            devices = await BleakScanner.discover(timeout=5.0)
            
            # Log all discovered devices for debugging
            logger.info(f"Found {len(devices)} BLE devices:")
            for d in devices:
                logger.info(f"  Address: {d.address} | Name: {d.name}")
            
            for d in devices:
                name = (d.name or "").lower()
                if "vivosmart" in name or "garmin" in name:
                    return d
            
            logger.warning("No Vivosmart 5 found in scan")
            return None
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return None
    
    def start(self):
        """Start listening to Vivosmart 5 data stream in background thread."""
        if not self.device:
            logger.error("Not connected to device. Call connect() first.")
            return
        
        self.running = True
        self.bg_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.bg_thread.start()
        logger.info("Vivosmart 5 listener started")
    
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
            
            data = f"E;1;Garmin;1;;;;Vivosmart5;{data.get('hr')};{rr_to_send}\r\n"
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
        self._notify_message("Vivosmart5: Disconnected", "Info")
        logger.info("Vivosmart 5 listener stopped")        

    def status(self):
        """Return the current status of the listener."""
        return self.running


if __name__ == "__main__":
    import sys
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Garmin Vivosmart 5 heart-rate monitor reader")
    parser.add_argument("--address", "-a", default="EC:8B:36:92:28:93", help="BLE address of the device (e.g., EC:8B:36:92:28:93)")
    args = parser.parse_args()
    
    # Mock stream for testing (prints to stdout)
    class MockStream:
        def sendall(self, data):
            print(f"[STREAM] {data.decode()}", file=sys.stdout)
    
    stream = MockStream()
    
    print("Starting Vivosmart 5 listener test...")
    print("Make sure your Garmin Vivosmart 5 is powered on and nearby.\n")
    
    vivosmart5 = Vivosmart5Listener(stream=stream, address=args.address)
    
    # Connect to device
    result = vivosmart5.connect()
    print(f"Connect result: {result}\n")
    
    if vivosmart5.device:
        # Start listening
        vivosmart5.start()
        print("Listening for HR data... Press Ctrl-C to stop.\n")
        
        try:
            while vivosmart5.status():
                import time
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            vivosmart5.stop()
            print("Vivosmart 5 listener stopped.")
    else:
        print("Failed to find Vivosmart 5 device.")
