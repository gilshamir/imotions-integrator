# Copyright (C) Smart Eye AB
# THE CODE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
# ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
# OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE CODE OR THE USE OR OTHER DEALINGS IN THE CODE.
"""Command line interface to communicate with RPC server

external_interfaces.py takes input from command_line.py
and sends the command to the RPC server.
The response is printed and returned.

"""

import sys
import json
import socket
import select
import os
import time
import threading
import logging


# pylint: disable=C0111,R0904,C0103,R0902
# Disabling C0111: Missing docstring since they are explained in command_line.py
# Disabling R0904: Too many public methods since they need to be reached from command_line.py
# Disabling C0103: Invalid method name to keep the same names as in command_line.py
# Disabling R0902: Too many instance attributes
class ExternalInterfaceError(Exception):
    """Custom exception for ExternalInterface errors."""

    pass


class ExternalInterface(object):
    DEFAULT_UDP_PORT = 5001

    def __init__(self):
        self.ip = None
        self.port = None
        self.open_data_streams_udp = {}
        self.con = None
        self.is_connected = False
        self.listening_for_notifications = False
        self.subscriptions = {}  # Store the notifications we have subscribed for
        self.lock = threading.Lock()
        self.tracker_states = self.get_states("tracker_states.json")
        self.recording_states = self.get_states("record_states.json")
        self.log_data_list = self.get_log_data_spec()

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context related to this object.
        """
        try:
            if self.is_connected:
                while self.open_data_streams_udp:
                    ip, port = next(iter(self.open_data_streams_udp.items()))
                    ExternalInterface.handle_error(
                        "close_data_stream_udp", self.close_data_stream_udp([ip, port])
                    )
                ExternalInterface.handle_error("disconnect", self.disconnect())
        except ExternalInterfaceError as e:
            logging.error(f"Failed to exit the runtime context: {e}")
        if exc_type is not None:
            logging.error(f"Exception occurred: {exc_value}")
        return False  # Do not suppress exceptions

    @staticmethod
    def handle_error(method_name, result):
        if result is not None:
            error_message = f"Error during {method_name}: {result}"
            logging.error(error_message)
            raise ExternalInterfaceError(error_message)

    @staticmethod
    def alert(msg):
        logging.error(msg)
        raise ExternalInterfaceError(msg)

    def connect(self, ip, port):
        self.ip = ip
        self.port = port
        self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.con.settimeout(0.1)  # Set timeout to not have recv() blocking
        try:
            self.con.connect((ip, int(port)))
        except socket.timeout:
            msg = f"Connection to {ip}:{port} timed out."
            ExternalInterface.alert(msg)
        except socket.error as e:
            msg = f"Failed to connect to {ip}:{port}. Exception: {e}"
            ExternalInterface.alert(msg)
        else:
            self.is_connected = True
            logging.info(f"Successfully connected to {ip}:{port}")

    def disconnect(self):
        if self.is_connected:
            self.con.close()
            self.is_connected = False
        else:
            ExternalInterface.alert("Error: Not connected to server")

    def send_and_receive(self, obj):
        if self.is_connected:
            json_string = json.dumps(obj)
            net_string = "{0}:{1},".format(len(json_string), json_string)
            self.lock.acquire()
            self.__flush()
            message_received = False
            n_of_attempts = 0
            try:
                self.con.send(net_string.encode("utf-8"))
                while not message_received:
                    try:
                        netstring, netstring_size = self.peek_netstring()
                        read_size = int(netstring) + netstring_size + 1
                        rec_in_net_string_format = self._recv_exact(read_size)
                    except socket.timeout as e:  # After 50 attempts,
                        # print error and return to
                        # avoid getting stuck in loop
                        if n_of_attempts == 50:
                            msg = (
                                "Something's wrong with %s. Exception type is %s."
                                " Retry the command"
                            )
                            ExternalInterface.alert(msg % (self.ip, e))
                            self.lock.release()
                            return e
                        n_of_attempts += 1
                        continue  # Should get a response when sending command,
                        # so just continue until message_received
                    except ValueError:
                        self.subscriptions = {}
                        self.lock.release()
                        return None
                    else:
                        message_received = True
                        self.lock.release()
                        try:
                            return_value = json.loads(
                                rec_in_net_string_format[netstring_size:-1]
                            )
                        except ValueError:
                            print(
                                f"Could not decode response when sending {net_string}"
                            )  # If SEP crashes for instance
                            return
                        return return_value
            except socket.error as e:  # Connection down, print error and return
                msg = (
                    "Something's wrong with %s. Exception type is %s. Make sure "
                    "that the SmartEyePro application is started and try to reconnect."
                )
                ExternalInterface.alert(msg % (self.ip, e))
                self.subscriptions = {}  # Clear subscriptions list so notification thread starts
                # when application is back up and we subscribe again
                self.lock.release()
                return None
        else:
            ExternalInterface.alert("Error: Not connected to server")

    def send(self, method, params=None):
        if params is not None:
            req_obj = self.__create_request_with_param(method, params)
        else:
            req_obj = self.__create_request(method)
        return self.send_and_receive(req_obj)

    def send_ping(self):
        response = self.send("ping")
        if response is not None:
            print(response["result"])
        return response

    def get_real_time_clock(self):
        response = self.send("getRealTimeClock")
        return self.__get_result_from_response(response)

    def get_rpc_version(self):
        response = self.send("getRPCVersion")
        if response is not None:
            result = (
                "version:"
                + str(response["result"]["major"])
                + "."
                + str(response["result"]["minor"])
            )
            print(result)
            return result

    def get_product_name(self):
        response = self.send("getProductName")
        if response is not None:
            print(response["result"])
        return response

    def get_product_version(self):
        response = self.send("getProductVersion")
        if response is not None:
            print(response["result"])
        return response

    def get_camera_type(self):
        response = self.send("getCameraType")
        if response is not None:
            print(response["result"])
        return response

    def get_firmware_versions(self):
        response = self.send("getFirmwareVersions")
        if response is not None:
            print(response["result"])
        return response

    # IlluminationMode
    def get_illumination_mode(self):
        response = self.send("getIlluminationMode")
        return self.__get_result_from_response(response)

    def set_illumination_mode(self, mode):
        response = self.send("setIlluminationMode", mode)
        return self.__get_result_from_response(response)

    def get_state(self):
        response = self.send("getState")
        if response is not None:
            print(self.__get_tracker_state_name(response["result"]["state"]))
            return self.__get_tracker_state_name(response["result"]["state"])

    def get_recording_state(self):
        response = self.send("getRecordingState")
        if response is not None:
            print(self.__get_recording_state_name(response["result"]["recordingState"]))
            return self.__get_recording_state_name(response["result"]["recordingState"])

    # Subject Category
    def get_subject_category(self):
        response = self.send("getSubjectCategory")
        if response is not None:
            print(response["result"])
        return response

    def set_subject_category(self, subject_category):
        response = self.send("setSubjectCategory", subject_category)
        return self.__get_result_from_response(response)

    # Tracking
    def start_tracking(self):
        response = self.send("startTracking")
        return self.__get_result_from_response(response)

    def stop_tracking(self):
        response = self.send("stopTracking")
        return self.__get_result_from_response(response)

    # Logging
    def set_log_specification(self, params):
        if params == "":
            response = self.send("setLogSpecification", self.log_data_list)
        else:
            response = self.send("setLogSpecification", params)
        return self.__get_result_from_response(response)

    def set_log_file(self, file_name):
        response = self.send("setLogFile", file_name)
        return self.__get_result_from_response(response)

    def start_log(self):
        response = self.send("startLog")
        return self.__get_result_from_response(response)

    def stop_log(self):
        response = self.send("stopLog")
        return self.__get_result_from_response(response)

    # Recording
    def set_recording_file(self, file_name):
        response = self.send("setRecordingFile", file_name)
        return self.__get_result_from_response(response)

    def start_recording(self, compression=0):
        try:
            compression = int(compression)
        except ValueError:
            compression = 0
        response = self.send("startRecording", int(compression))
        return self.__get_result_from_response(response)

    def stop_recording(self):
        response = self.send("stopRecording")
        return self.__get_result_from_response(response)

    # Image source
    def set_image_source_cameras(self):
        response = self.send("setImageSourceCameras")
        return self.__get_result_from_response(response)

    def set_image_source_recording(self, file_name_sma, file_name_smb=""):
        if not file_name_smb:
            file_name_smb = file_name_sma.replace(".sma", ".smb")

        response = self.send("setImageSourceRecording", [file_name_sma, file_name_smb])
        return self.__get_result_from_response(response)

    # Profile
    def clear_profile(self):
        response = self.send("clearProfile")
        return self.__get_result_from_response(response)

    def save_profile(self, file_name):
        response = self.send("saveProfile", file_name)
        return self.__get_result_from_response(response)

    def load_profile(self, file_name):
        response = self.send("loadProfile", file_name)
        return self.__get_result_from_response(response)

    def get_profile(self):
        response = self.send("getProfile")
        return self.__get_result_from_response(response)

    def set_profile(self, profile_data):
        response = self.send("setProfile", profile_data)
        return self.__get_result_from_response(response)

    def get_active_eyes(self):
        response = self.send("getActiveEyes")
        return self.__get_result_from_response(response)

    def set_active_eyes(self, left, right):
        response = self.send("setActiveEyes", [left, right])
        return self.__get_result_from_response(response)

    def get_profile_load_mode(self):
        response = self.send("getProfileLoadMode")
        return self.__get_result_from_response(response)

    def set_profile_load_mode(self, load_mode):
        response = self.send("setProfileLoadMode", load_mode)
        return self.__get_result_from_response(response)

    # World model
    def clear_world_model(self):
        response = self.send("clearWorldModel")
        return self.__get_result_from_response(response)

    def load_world_model(self, file_name):
        response = self.send("loadWorldModel", file_name)
        return self.__get_result_from_response(response)

    def load_default_world_model(self):
        response = self.send("loadWorldModel")
        return self.__get_result_from_response(response)

    def get_world_model(self):
        response = self.send("getWorldModel")
        return self.__get_result_from_response(response)

    def set_world_model(self, params):
        response = self.send("setWorldModel", params)
        return self.__get_result_from_response(response)

    # Communication UDP/TCP
    def open_data_stream_udp(self, params):
        ip = params[0] if params[0] else self.ip
        port = params[1] if len(params) > 1 else ExternalInterface.DEFAULT_UDP_PORT
        log_data_list = params[2] if len(params) > 2 else self.log_data_list

        response = self.send("openDataStreamUDP", [ip, port, log_data_list])
        self.open_data_streams_udp[ip] = port
        return self.__get_result_from_response(response)

    def close_data_stream_udp(self, params):
        ip = params[0] if params[0] else self.ip
        port = params[1] if len(params) > 1 else ExternalInterface.DEFAULT_UDP_PORT

        response = self.send("closeDataStreamUDP", [ip, port])
        self.open_data_streams_udp.pop(ip, None)
        return self.__get_result_from_response(response)

    def open_data_stream_tcp(self, params):
        if len(params) < 2:
            params.append(self.log_data_list)
        response = self.send("openDataStreamTCP", params)
        return self.__get_result_from_response(response)

    def close_data_stream_tcp(self, params):
        response = self.send("closeDataStreamTCP", params)
        return self.__get_result_from_response(response)

    # Gaze calibration
    def start_collect_samples_wcs(self, params):
        response = self.send("startCollectSamplesWCS", params)
        return self.__get_result_from_response(response)

    def start_collect_samples_by_target_name(self, params):
        response = self.send("startCollectSamplesByTargetName", params)
        return self.__get_result_from_response(response)

    def retrieve_target_samples_statistics(self, params):
        response = self.send("retrieveTargetSamplesStatistics", params)
        return self.__get_result_from_response(response)

    def start_collect_samples_object(self, params):
        response = self.send("startCollectSamplesObject", params)
        return self.__get_result_from_response(response)

    def stop_collect_samples(self):
        response = self.send("stopCollectSamples")
        return self.__get_result_from_response(response)

    def clear_all_target_samples(self):
        response = self.send("clearAllTargetSamples")
        return self.__get_result_from_response(response)

    def clear_target_samples(self, params):
        response = self.send("clearTargetSamples", params)
        return self.__get_result_from_response(response)

    def retrieve_target_statistics(self, params):
        response = self.send("retrieveTargetStatistics", params)
        return self.__get_result_from_response(response)

    def retrieve_target_statistics_with_gaze_origin(self, params):
        response = self.send("retrieveTargetStatisticsWithGazeOrigin", params)
        return self.__get_result_from_response(response)

    def calibrate_gaze(self):
        response = self.send("calibrateGaze")
        return self.__get_result_from_response(response)

    def apply_gaze_calibration(self):
        response = self.send("applyGazeCalibration")
        return self.__get_result_from_response(response)

    def clear_gaze_calibration(self):
        response = self.send("clearGazeCalibration")
        return self.__get_result_from_response(response)

    def is_gaze_calibrated(self):
        response = self.send("isGazeCalibrated")
        return self.__get_result_from_response(response)

    # Application control
    def key_down(self, key):
        response = self.send("keyDown", key)
        return self.__get_result_from_response(response)

    def key_up(self, key):
        response = self.send("keyUp", key)
        return self.__get_result_from_response(response)

    def shut_down(self):
        response = self.send("shutdown")
        self.is_connected = False
        return self.__get_result_from_response(response)

    # Notification
    def subscribe_to_notification(self, notification):
        self.subscribe_to_notificationCB(notification, "")

    def subscribe_to_notificationCB(self, notification, callback):
        response = self.send("subscribeToNotification", notification)
        result = self.__get_result_from_response(response)
        if result is None:
            if callable(callback):
                print(
                    f"Registered callback {callback.__name__} for notification {notification}."
                )
            self.subscriptions[notification] = callback
            if len(self.subscriptions) == 1 and self.is_connected:
                self.__start_listen_for_notifications()  # Start listening to notifications
                # when first subscription is done.
        return result

    def unsubscribe_to_notification(self, params):
        response = self.send("unsubscribeToNotification", params)
        result = self.__get_result_from_response(response)
        if result is None and self.subscriptions:
            del self.subscriptions[params]  # When last item is removed
            # the thread listening for notifications will stop.
        return result

    def send_notification(self, params):
        response = self.send("sendNotification", params)
        return self.__get_result_from_response(response)

    def receive_notification(self, max_wait_time=7200):
        """
        Wait to receive a json_rpc response.

        max_wait_time specifies a timeout for receive_notification in
        seconds (default 2 hours).
        """
        # Waiting for socket to be ready
        max_wait_time -= self._await_socket_ready(max_wait_time)

        # Read length of the next netstring message.
        remaining_msg_len = self.get_netstring_size()
        # +1 to include ending netstring ",".
        remaining_msg_len += 1

        # Read the next netstring message (in chunks) until exactly msg_len
        # bytes has been read.
        msg = b""
        buf = bytearray(4096)
        retry_count = 0
        max_retries = 3

        while remaining_msg_len > 0:
            if max_wait_time <= 0:
                raise OSError("Connection to Smart Eye Pro timed out.")

            try:
                max_wait_time -= self._await_socket_ready(max_wait_time)
                n = self.con.recv_into(buf, min(remaining_msg_len, 4096))
                msg += buf[:n]
                remaining_msg_len -= n
                retry_count = 0
            except socket.timeout:
                retry_count += 1
                if retry_count > max_retries:
                    raise OSError(
                        f"Failed to receive data after {max_retries} retry attempts."
                    )
                logging.warning(
                    f"Socket timeout during recv_into, retrying... ({retry_count}/{max_retries})"
                )
                continue

        if remaining_msg_len != 0 or not msg.endswith(b","):
            raise OSError(f"Bad netstring message: {repr(msg)}.")
        # Drop ending netstring ",".
        msg = msg[:-1]
        # Interpret as UTF-8 encoded JSON message.
        return json.loads(msg.decode("utf-8"))

    def _await_socket_ready(self, timeout):
        """
        Wait at most timeout seconds for self.socket to be ready. Raises an
        OSError if the timeout is exceeded.

        Returns the number of seconds elapsed until socket was ready.
        """
        if timeout <= 0:
            raise OSError("Connection to Smart Eye Pro timed out.")

        start_time = time.time()
        socket_ready = select.select([self.con], [], [], timeout)
        if not socket_ready[0]:
            raise OSError("Connection to Smart Eye Pro timed out.")
        return round(time.time() - start_time)

    def get_netstring_size(self, max_retries=3):
        """Returns size of the incoming netstring.
        https://en.wikipedia.org/wiki/Netstring"""
        netstring_size = ""
        done = False
        # The max number of chars representing the size in a netstring payload
        size_max_len = 7

        for _ in range(size_max_len):
            # parse digits until we're "done", i.e. we get the ":" separator
            retry_count = 0
            while True:
                try:
                    digit = self.con.recv(1).decode()
                    break  # Successfully got a digit, exit retry loop
                except socket.timeout:
                    retry_count += 1
                    if retry_count > max_retries:
                        raise OSError(
                            f"Failed to receive netstring size digit after {max_retries} retry attempts."
                        )
                    logging.warning(
                        f"Socket timeout during recv in get_netstring_size, retrying... ({retry_count}/{max_retries})"
                    )
                    continue

            if digit == ":":
                done = True
                break

            netstring_size += digit

        if not done:
            # We never finished, ie we never got the ":" separator
            raise OSError(f"Invalid netstring size format: {netstring_size}")

        return int(netstring_size)

    # Calibration Results
    def retrieve_calibration_results(self):
        response = self.send("retrieveCalibrationResults")
        return self.__get_result_from_response(response)

    # Playback
    def set_playback_speed_to_max(self):
        response = self.send("setPlaybackSpeedToMax")
        return self.__get_result_from_response(response)

    def set_playback_speed_to_real_time(self):
        response = self.send("setPlaybackSpeedToRealTime")
        return self.__get_result_from_response(response)

    def set_playback_position(self, params):
        response = self.send("setPlaybackPosition", params)
        return self.__get_result_from_response(response)

    def set_playback_start_stop_positions(self, params):
        response = self.send("setPlaybackStartStopPositions", params)
        return self.__get_result_from_response(response)

    def resume_playback(self):
        response = self.send("resumePlayback")
        return self.__get_result_from_response(response)

    def pause_playback(self):
        response = self.send("pausePlayback")
        return self.__get_result_from_response(response)

    def set_playback_repeat_on(self):
        response = self.send("setPlaybackRepeatOn")
        return self.__get_result_from_response(response)

    def set_playback_repeat_off(self):
        response = self.send("setPlaybackRepeatOff")
        return self.__get_result_from_response(response)

    # Collect Point Samples
    def start_collect_point_samples_automatic(self):
        response = self.send("startCollectPointSamplesAutomatic")
        return self.__get_result_from_response(response)

    def stop_collect_point_samples_automatic(self):
        response = self.send("stopCollectPointSamplesAutomatic")
        return self.__get_result_from_response(response)

    # Camera Image
    def get_camera_image(self, params):
        response = self.send("getCameraImage", params)
        return self.__get_result_from_response(response)

    # Chessboard Tracking
    def start_chessboard_tracking(self):
        response = self.send("startChessboardTracking")
        return self.__get_result_from_response(response)

    def stop_chessboard_tracking(self):
        response = self.send("stopChessboardTracking")
        return self.__get_result_from_response(response)

    # Camera GPIO
    def set_camera_gpio(self, params):
        response = self.send("setCameraGPIO", params)
        return self.__get_result_from_response(response)

    # Usb speed
    def is_camera_connected_to_usb3(self, params):
        response = self.send("isCameraConnectedToUSB3", params)
        return self.__get_result_from_response(response)

    # Reflex Reduction
    def set_reflex_reduction_mode(self, params):
        response = self.send("setReflexReductionMode", params)
        return self.__get_result_from_response(response)

    # ProfileId
    def clear_single_profile_id(self, params):
        response = self.send("clearSingleProfileId", params)
        return self.__get_result_from_response(response)

    def clear_all_profile_ids(self):
        response = self.send("clearAllProfileIds")
        return self.__get_result_from_response(response)

    # Modules
    def get_all_modules(self):
        response = self.send("getAllModules")
        return self.__get_result_from_response(response)

    def get_enabled_modules(self):
        response = self.send("getEnabledModules")
        return self.__get_result_from_response(response)

    def enable_module(self, params):
        response = self.send("enableModule", params)
        return self.__get_result_from_response(response)

    def disable_module(self, params):
        response = self.send("disableModule", params)
        return self.__get_result_from_response(response)

    # Hardware Information
    def get_hardware_info(self):
        response = self.send("getHardwareInfo")
        return self.__get_result_from_response(response)

    # Following are help functions used in this script
    def __get_tracker_state_name(self, enum_value):
        for state in self.tracker_states:
            if state["EnumValue"] == format(enum_value, "#06x"):
                return state["Description"]
        return "Wrong value"

    def __get_recording_state_name(self, enum_value):
        if not self.recording_states:
            return "Unable to get recording state. No recording states file loaded."
        for state in self.recording_states:
            if state["EnumValue"] == format(enum_value, "#06x"):
                return state["Description"]
        return "Wrong value"

    @staticmethod
    def __create_request(method):
        net_string = {"jsonrpc": "2.0", "method": method, "id": 0}
        return net_string

    @staticmethod
    def __create_request_with_param(method, parameters):
        if isinstance(parameters, list):
            net_string = {
                "jsonrpc": "2.0",
                "method": method,
                "params": parameters,
                "id": 0,
            }
        else:
            net_string = {
                "jsonrpc": "2.0",
                "method": method,
                "params": [parameters],
                "id": 0,
            }
        return net_string

    @staticmethod
    def __get_result_from_response(response):
        if response is not None:
            if "error" in response:
                print(
                    "Something went wrong ErrorMsg: "
                    + response["error"]["message"]
                    + " ErrorCode: "
                    + str(response["error"]["code"])
                )
                return response["error"]["message"]
            elif "result" in response:
                if response["result"] is not None:
                    print(f"Action was successful with result: {response['result']}")
                return response["result"]
            return response

    def __flush(self):
        # Flush unhandled notifications
        while True:
            try:
                netstring, netstring_size = self.peek_netstring()
                read_size = int(netstring) + netstring_size + 1
                rec_in_net_string_format = self._recv_exact(read_size)
            except socket.timeout:  # Nothing to flush, just return
                return
            except socket.error:  # Nothing to flush, just return
                return
            else:
                if rec_in_net_string_format:
                    prefix_length = len(rec_in_net_string_format.split(":")[0]) + 1
                    result = json.loads(rec_in_net_string_format[prefix_length:-1])
                    print("Notification received: %s" % result["method"])
                    callback = self.subscriptions[result["method"]]
                    if callable(callback):
                        callback()

    def __start_listen_for_notifications(self):
        if not self.listening_for_notifications:
            self.listening_for_notifications = True
            try:
                threading.Thread(
                    target=self.__listen_for_notifications, daemon=True
                ).start()
            except threading.ThreadError as e:
                msg = (
                    "Could not start listening for notifications. "
                    "Try to unsubscribe and subscribe again"
                )
                ExternalInterface.alert(msg % (e))

    def __listen_for_notifications(self):
        print("Listening for notifications...")
        while self.subscriptions:
            self.lock.acquire()
            try:
                try:
                    netstring, netstring_size = self.peek_netstring()
                    read_size = int(netstring) + netstring_size + 1
                    rec_in_net_string_format = self._recv_exact(read_size)
                except socket.timeout:
                    # No notification available.
                    pass
                except (socket.error, ValueError) as e:
                    print(f"Error while listening for notifications: {e}")
                    self.listening_for_notifications = False
                    return
                else:
                    # Process the notification
                    if rec_in_net_string_format:
                        try:
                            result = json.loads(
                                rec_in_net_string_format[netstring_size:-1]
                            )
                            method = result.get("method")

                            if method:
                                print(f"Notification received: {method}")

                                if "params" in result:
                                    print(f"Params: {result['params']}")

                                callback = self.subscriptions.get(method)
                                if callable(callback):
                                    try:
                                        callback()
                                    except Exception as e:
                                        print(f"Error in callback for {method}: {e}")
                        except json.JSONDecodeError as e:
                            print(f"Error decoding notification JSON: {e}")
            finally:
                self.lock.release()

            time.sleep(0.5)

        print("Stopped listening for notifications.")
        self.listening_for_notifications = False

    def peek_netstring(self):
        peek_msg = self.con.recv(2048, socket.MSG_PEEK).decode("utf-8")
        netstring = peek_msg.split(":")[0]
        netstring_size = len(netstring) + 1
        return netstring, netstring_size

    def _recv_exact(self, n_bytes):
        msg = b""
        buf = bytearray(4096)
        while n_bytes > 0:
            n = self.con.recv_into(buf, min(n_bytes, 4096))
            msg += buf[:n]
            n_bytes -= n
        return msg.decode("utf-8")

    def get_states(self, filename):
        states_file_path = self.find_states_file(filename)
        if not states_file_path:
            print("Unable to get states. File not found.")
            return None

        try:
            with open(states_file_path, "r") as states_file:
                states = json.loads(states_file.read())
                return states

        except Exception as e:
            print(f"Error opening or reading states file: {e}")
            return None

    def find_states_file(self, filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        if hasattr(sys, "_MEIPASS"):
            path = os.path.join(sys._MEIPASS, filename)
            return path

        paths_to_check = [
            os.path.join(script_dir, "..", "..", "..", "include", filename),
            os.path.join(
                script_dir, "..", "..", "..", "..", "..", "Definitions", filename
            ),
        ]

        for path in paths_to_check:
            if os.path.exists(path):
                return path
        return None

    def get_log_data_spec(self):
        try:
            # Determine the correct path to log_data_list.txt
            if hasattr(sys, "_MEIPASS"):
                # If running in a PyInstaller bundle
                log_data_list_path = os.path.join(sys._MEIPASS, "log_data_list.txt")
            else:
                # If running in a normal Python environment
                script_dir = os.path.dirname(os.path.abspath(__file__))
                log_data_list_path = os.path.join(script_dir, "log_data_list.txt")

            # Open and read the log_data_list.txt file
            with open(log_data_list_path, "r") as log_data_list_file:
                self.log_data_list = log_data_list_file.read()
        except IOError as e:
            print("Unable to get log_data_spec. Error: {0}".format(e))
