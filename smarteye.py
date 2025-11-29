import logging
import time
from sensor import Sensor

from sep.sepd import Packet
from sep.socket import EndOfStreamError, TCPClient, UDPClient

class SEListener(Sensor):
    def __init__(self, port, stream=None):
        super().__init__()
        self.stream = stream
        self.port = port
        self.running = False
        self.client = None
    
    def print_packet(self, packet: Packet) -> None:
        print("** PACKET **")
        if packet.frame_number is not None:
            print(f"frame_number: {packet.frame_number}")

        if packet.estimated_delay is not None:
            print(f"estimated_delay: {packet.estimated_delay}")

        if packet.time_stamp is not None:
            print(f"time_stamp: {packet.time_stamp}")

        if packet.user_time_stamp is not None:
            print(f"user_time_stamp: {packet.user_time_stamp}")

        if packet.real_time_clock is not None:
            print(f"real_time_clock: {packet.real_time_clock}")

        if packet.frame_rate is not None:
            print(f"frame_rate: {packet.frame_rate}")

        if packet.camera_positions is not None:
            print(f"camera_positions: {packet.camera_positions}")

        if packet.camera_rotations is not None:
            print(f"camera_rotations: {packet.camera_rotations}")

        if packet.user_defined_data is not None:
            print(f"user_defined_data: {packet.user_defined_data}")

        if packet.real_time_clock is not None:
            print(f"real_time_clock: {packet.real_time_clock}")

        if packet.head_position is not None:
            print(f"head_position: {packet.head_position}")

        if packet.head_position_quality is not None:
            print(f"head_position_quality: {packet.head_position_quality}")

        if packet.head_rotation_rodrigues is not None:
            print(f"head_rotation_rodrigues: {packet.head_rotation_rodrigues}")

        if packet.head_rotation_quaternion is not None:
            print(f"head_rotation_quaternion: {packet.head_rotation_quaternion}")

        if packet.head_left_ear_direction is not None:
            print(f"head_left_ear_direction: {packet.head_left_ear_direction}")

        if packet.head_up_direction is not None:
            print(f"head_up_direction: {packet.head_up_direction}")

        if packet.head_nose_direction is not None:
            print(f"head_nose_direction: {packet.head_nose_direction}")

        if packet.head_heading is not None:
            print(f"head_heading: {packet.head_heading}")

        if packet.head_pitch is not None:
            print(f"head_pitch: {packet.head_pitch}")

        if packet.head_roll is not None:
            print(f"head_roll: {packet.head_roll}")

        if packet.head_rotation_quality is not None:
            print(f"head_rotation_quality: {packet.head_rotation_quality}")

        if packet.gaze_origin is not None:
            print(f"gaze_origin: {packet.gaze_origin}")

        if packet.left_gaze_origin is not None:
            print(f"left_gaze_origin: {packet.left_gaze_origin}")

        if packet.right_gaze_origin is not None:
            print(f"right_gaze_origin: {packet.right_gaze_origin}")

        if packet.eye_position is not None:
            print(f"eye_position: {packet.eye_position}")

        if packet.gaze_direction is not None:
            print(f"gaze_direction: {packet.gaze_direction}")

        if packet.gaze_direction_quality is not None:
            print(f"gaze_direction_quality: {packet.gaze_direction_quality}")

        if packet.left_eye_position is not None:
            print(f"left_eye_position: {packet.left_eye_position}")

        if packet.left_gaze_direction is not None:
            print(f"left_gaze_direction: {packet.left_gaze_direction}")

        if packet.left_gaze_direction_quality is not None:
            print(f"left_gaze_direction_quality: {packet.left_gaze_direction_quality}")

        if packet.right_eye_position is not None:
            print(f"right_eye_position: {packet.right_eye_position}")

        if packet.right_gaze_direction is not None:
            print(f"right_gaze_direction: {packet.right_gaze_direction}")

        if packet.right_gaze_direction_quality is not None:
            print(f"right_gaze_direction_quality: {packet.right_gaze_direction_quality}")

        if packet.gaze_heading is not None:
            print(f"gaze_heading: {packet.gaze_heading}")

        if packet.gaze_pitch is not None:
            print(f"gaze_pitch: {packet.gaze_pitch}")

        if packet.left_gaze_heading is not None:
            print(f"left_gaze_heading: {packet.left_gaze_heading}")

        if packet.left_gaze_pitch is not None:
            print(f"left_gaze_pitch: {packet.left_gaze_pitch}")

        if packet.right_gaze_heading is not None:
            print(f"right_gaze_heading: {packet.right_gaze_heading}")

        if packet.right_gaze_pitch is not None:
            print(f"right_gaze_pitch: {packet.right_gaze_pitch}")

        if packet.filtered_gaze_direction is not None:
            print(f"filtered_gaze_direction: {packet.filtered_gaze_direction}")

        if packet.filtered_left_gaze_direction is not None:
            print(f"filtered_left_gaze_direction: {packet.filtered_left_gaze_direction}")

        if packet.filtered_right_gaze_direction is not None:
            print(f"filtered_right_gaze_direction: {packet.filtered_right_gaze_direction}")

        if packet.filtered_gaze_heading is not None:
            print(f"filtered_gaze_heading: {packet.filtered_gaze_heading}")

        if packet.filtered_gaze_pitch is not None:
            print(f"filtered_gaze_pitch: {packet.filtered_gaze_pitch}")

        if packet.filtered_left_gaze_heading is not None:
            print(f"filtered_left_gaze_heading: {packet.filtered_left_gaze_heading}")

        if packet.filtered_left_gaze_pitch is not None:
            print(f"filtered_left_gaze_pitch: {packet.filtered_left_gaze_pitch}")

        if packet.filtered_right_gaze_heading is not None:
            print(f"filtered_right_gaze_heading: {packet.filtered_right_gaze_heading}")

        if packet.filtered_right_gaze_pitch is not None:
            print(f"filtered_right_gaze_pitch: {packet.filtered_right_gaze_pitch}")

        if packet.filtered_gaze_origin is not None:
            print(f"filtered_gaze_origin: {packet.filtered_gaze_origin}")

        if packet.filtered_left_gaze_origin is not None:
            print(f"filtered_left_gaze_origin: {packet.filtered_left_gaze_origin}")

        if packet.filtered_right_gaze_origin is not None:
            print(f"filtered_right_gaze_origin: {packet.filtered_right_gaze_origin}")

        if packet.saccade is not None:
            print(f"saccade: {packet.saccade}")

        if packet.fixation is not None:
            print(f"fixation: {packet.fixation}")

        if packet.blink is not None:
            print(f"blink: {packet.blink}")

        if packet.closest_world_intersection is not None:
            print(f"closest_world_intersection: {packet.closest_world_intersection}")

        if packet.filtered_closest_world_intersection is not None:
            print(f"filtered_closest_world_intersection: {packet.filtered_closest_world_intersection}")

        if packet.all_world_intersections is not None:
            print(f"all_world_intersections: {packet.all_world_intersections}")

        if packet.filtered_all_world_intersections is not None:
            print(f"filtered_all_world_intersections: {packet.filtered_all_world_intersections}")

        if packet.estimated_closest_world_intersection is not None:
            print(f"estimated_closest_world_intersection: {packet.estimated_closest_world_intersection}")

        if packet.estimated_all_world_intersections is not None:
            print(f"estimated_all_world_intersections: {packet.estimated_all_world_intersections}")

        if packet.head_closest_world_intersection is not None:
            print(f"head_closest_world_intersection: {packet.head_closest_world_intersection}")

        if packet.head_all_world_intersections is not None:
            print(f"head_all_world_intersections: {packet.head_all_world_intersections}")

        if packet.eyelid_opening is not None:
            print(f"eyelid_opening: {packet.eyelid_opening}")

        if packet.eyelid_opening_quality is not None:
            print(f"eyelid_opening_quality: {packet.eyelid_opening_quality}")

        if packet.left_eyelid_opening is not None:
            print(f"left_eyelid_opening: {packet.left_eyelid_opening}")

        if packet.left_eyelid_opening_quality is not None:
            print(f"left_eyelid_opening_quality: {packet.left_eyelid_opening_quality}")

        if packet.right_eyelid_opening is not None:
            print(f"right_eyelid_opening: {packet.right_eyelid_opening}")

        if packet.right_eyelid_opening_quality is not None:
            print(f"right_eyelid_opening_quality: {packet.right_eyelid_opening_quality}")

        if packet.keyboard_state is not None:
            print(f"keyboard_state: {packet.keyboard_state}")

        if packet.pupil_diameter is not None:
            print(f"pupil_diameter: {packet.pupil_diameter}")

        if packet.pupil_diameter_quality is not None:
            print(f"pupil_diameter_quality: {packet.pupil_diameter_quality}")

        if packet.left_pupil_diameter is not None:
            print(f"left_pupil_diameter: {packet.left_pupil_diameter}")

        if packet.left_pupil_diameter_quality is not None:
            print(f"left_pupil_diameter_quality: {packet.left_pupil_diameter_quality}")

        if packet.right_pupil_diameter is not None:
            print(f"right_pupil_diameter: {packet.right_pupil_diameter}")

        if packet.right_pupil_diameter_quality is not None:
            print(f"right_pupil_diameter_quality: {packet.right_pupil_diameter_quality}")

        if packet.filtered_pupil_diameter is not None:
            print(f"filtered_pupil_diameter: {packet.filtered_pupil_diameter}")

        if packet.filtered_pupil_diameter_quality is not None:
            print(f"filtered_pupil_diameter_quality: {packet.filtered_pupil_diameter_quality}")

        if packet.filtered_left_pupil_diameter is not None:
            print(f"filtered_left_pupil_diameter: {packet.filtered_left_pupil_diameter}")

        if packet.filtered_left_pupil_diameter_quality is not None:
            print(f"filtered_left_pupil_diameter_quality: {packet.filtered_left_pupil_diameter_quality}")

        if packet.filtered_right_pupil_diameter is not None:
            print(f"filtered_right_pupil_diameter: {packet.filtered_right_pupil_diameter}")

        if packet.filtered_right_pupil_diameter_quality is not None:
            print(f"filtered_right_pupil_diameter_quality: {packet.filtered_right_pupil_diameter_quality}")

        if packet.gps_position is not None:
            print(f"gps_position: {packet.gps_position}")

        if packet.gps_ground_speed is not None:
            print(f"gps_ground_speed: {packet.gps_ground_speed}")

        if packet.gps_course is not None:
            print(f"gps_course: {packet.gps_course}")

        if packet.gps_time is not None:
            print(f"gps_time: {packet.gps_time}")

        if packet.estimated_gaze_origin is not None:
            print(f"estimated_gaze_origin: {packet.estimated_gaze_origin}")

        if packet.estimated_left_gaze_origin is not None:
            print(f"estimated_left_gaze_origin: {packet.estimated_left_gaze_origin}")

        if packet.estimated_right_gaze_origin is not None:
            print(f"estimated_right_gaze_origin: {packet.estimated_right_gaze_origin}")

        if packet.estimated_eye_position is not None:
            print(f"estimated_eye_position: {packet.estimated_eye_position}")

        if packet.estimated_gaze_direction is not None:
            print(f"estimated_gaze_direction: {packet.estimated_gaze_direction}")

        if packet.estimated_gaze_direction_quality is not None:
            print(f"estimated_gaze_direction_quality: {packet.estimated_gaze_direction_quality}")

        if packet.estimated_gaze_heading is not None:
            print(f"estimated_gaze_heading: {packet.estimated_gaze_heading}")

        if packet.estimated_gaze_pitch is not None:
            print(f"estimated_gaze_pitch: {packet.estimated_gaze_pitch}")

        if packet.estimated_left_eye_position is not None:
            print(f"estimated_left_eye_position: {packet.estimated_left_eye_position}")

        if packet.estimated_left_gaze_direction is not None:
            print(f"estimated_left_gaze_direction: {packet.estimated_left_gaze_direction}")

        if packet.estimated_left_gaze_direction_quality is not None:
            print(f"estimated_left_gaze_direction_quality: {packet.estimated_left_gaze_direction_quality}")

        if packet.estimated_left_gaze_heading is not None:
            print(f"estimated_left_gaze_heading: {packet.estimated_left_gaze_heading}")

        if packet.estimated_left_gaze_pitch is not None:
            print(f"estimated_left_gaze_pitch: {packet.estimated_left_gaze_pitch}")

        if packet.estimated_right_eye_position is not None:
            print(f"estimated_right_eye_position: {packet.estimated_right_eye_position}")

        if packet.estimated_right_gaze_direction is not None:
            print(f"estimated_right_gaze_direction: {packet.estimated_right_gaze_direction}")

        if packet.estimated_right_gaze_direction_quality is not None:
            print(f"estimated_right_gaze_direction_quality: {packet.estimated_right_gaze_direction_quality}")

        if packet.estimated_right_gaze_heading is not None:
            print(f"estimated_right_gaze_heading: {packet.estimated_right_gaze_heading}")

        if packet.estimated_right_gaze_pitch is not None:
            print(f"estimated_right_gaze_pitch: {packet.estimated_right_gaze_pitch}")

        if packet.filtered_estimated_gaze_direction is not None:
            print(f"filtered_estimated_gaze_direction: {packet.filtered_estimated_gaze_direction}")

        if packet.filtered_estimated_gaze_direction_quality is not None:
            print(f"filtered_estimated_gaze_direction_quality: {packet.filtered_estimated_gaze_direction_quality}")

        if packet.filtered_estimated_gaze_heading is not None:
            print(f"filtered_estimated_gaze_heading: {packet.filtered_estimated_gaze_heading}")

        if packet.filtered_estimated_gaze_pitch is not None:
            print(f"filtered_estimated_gaze_pitch: {packet.filtered_estimated_gaze_pitch}")

        if packet.filtered_estimated_left_gaze_direction is not None:
            print(f"filtered_estimated_left_gaze_direction: {packet.filtered_estimated_left_gaze_direction}")

        if packet.filtered_estimated_left_gaze_direction_quality is not None:
            print(f"filtered_estimated_left_gaze_direction_quality: {packet.filtered_estimated_left_gaze_direction_quality}")

        if packet.filtered_estimated_left_gaze_heading is not None:
            print(f"filtered_estimated_left_gaze_heading: {packet.filtered_estimated_left_gaze_heading}")

        if packet.filtered_estimated_left_gaze_pitch is not None:
            print(f"filtered_estimated_left_gaze_pitch: {packet.filtered_estimated_left_gaze_pitch}")

        if packet.filtered_estimated_right_gaze_direction is not None:
            print(f"filtered_estimated_right_gaze_direction: {packet.filtered_estimated_right_gaze_direction}")

        if packet.filtered_estimated_right_gaze_direction_quality is not None:
            print(f"filtered_estimated_right_gaze_direction_quality: {packet.filtered_estimated_right_gaze_direction_quality}")

        if packet.filtered_estimated_right_gaze_heading is not None:
            print(f"filtered_estimated_right_gaze_heading: {packet.filtered_estimated_right_gaze_heading}")

        if packet.filtered_estimated_right_gaze_pitch is not None:
            print(f"filtered_estimated_right_gaze_pitch: {packet.filtered_estimated_right_gaze_pitch}")

        if packet.ascii_keyboard_state is not None:
            print(f"ascii_keyboard_state: {packet.ascii_keyboard_state}")

        if packet.calibration_gaze_intersection is not None:
            print(f"calibration_gaze_intersection: {packet.calibration_gaze_intersection}")

        if packet.tagged_gaze_intersection is not None:
            print(f"tagged_gaze_intersection: {packet.tagged_gaze_intersection}")

        if packet.left_closest_world_intersection is not None:
            print(f"left_closest_world_intersection: {packet.left_closest_world_intersection}")

        if packet.left_all_world_intersections is not None:
            print(f"left_all_world_intersections: {packet.left_all_world_intersections}")

        if packet.right_closest_world_intersection is not None:
            print(f"right_closest_world_intersection: {packet.right_closest_world_intersection}")

        if packet.right_all_world_intersections is not None:
            print(f"right_all_world_intersections: {packet.right_all_world_intersections}")

        if packet.filtered_left_closest_world_intersection is not None:
            print(f"filtered_left_closest_world_intersection: {packet.filtered_left_closest_world_intersection}")

        if packet.filtered_left_all_world_intersections is not None:
            print(f"filtered_left_all_world_intersections: {packet.filtered_left_all_world_intersections}")

        if packet.filtered_right_closest_world_intersection is not None:
            print(f"filtered_right_closest_world_intersection: {packet.filtered_right_closest_world_intersection}")

        if packet.filtered_right_all_world_intersections is not None:
            print(f"filtered_right_all_world_intersections: {packet.filtered_right_all_world_intersections}")

        if packet.estimated_left_closest_world_intersection is not None:
            print(f"estimated_left_closest_world_intersection: {packet.estimated_left_closest_world_intersection}")

        if packet.estimated_left_all_world_intersections is not None:
            print(f"estimated_left_all_world_intersections: {packet.estimated_left_all_world_intersections}")

        if packet.estimated_right_closest_world_intersection is not None:
            print(f"estimated_right_closest_world_intersection: {packet.estimated_right_closest_world_intersection}")

        if packet.estimated_right_all_world_intersections is not None:
            print(f"estimated_right_all_world_intersections: {packet.estimated_right_all_world_intersections}")

        if packet.filtered_estimated_closest_world_intersection is not None:
            print(f"filtered_estimated_closest_world_intersection: {packet.filtered_estimated_closest_world_intersection}")

        if packet.filtered_estimated_all_world_intersections is not None:
            print(f"filtered_estimated_all_world_intersections: {packet.filtered_estimated_all_world_intersections}")

        if packet.filtered_estimated_left_closest_world_intersection is not None:
            print(f"filtered_estimated_left_closest_world_intersection: {packet.filtered_estimated_left_closest_world_intersection}")

        if packet.filtered_estimated_left_all_world_intersections is not None:
            print(f"filtered_estimated_left_all_world_intersections: {packet.filtered_estimated_left_all_world_intersections}")

        if packet.filtered_estimated_right_closest_world_intersection is not None:
            print(f"filtered_estimated_right_closest_world_intersection: {packet.filtered_estimated_right_closest_world_intersection}")

        if packet.filtered_estimated_right_all_world_intersections is not None:
            print(f"filtered_estimated_right_all_world_intersections: {packet.filtered_estimated_right_all_world_intersections}")

        if packet.all_world_cone_intersections is not None:
            print(f"all_world_cone_intersections: {packet.all_world_cone_intersections}")

        if packet.left_all_world_cone_intersections is not None:
            print(f"left_all_world_cone_intersections: {packet.left_all_world_cone_intersections}")

        if packet.right_all_world_cone_intersections is not None:
            print(f"right_all_world_cone_intersections: {packet.right_all_world_cone_intersections}")

        if packet.filtered_all_world_cone_intersections is not None:
            print(f"filtered_all_world_cone_intersections: {packet.filtered_all_world_cone_intersections}")

        if packet.filtered_left_all_world_cone_intersections is not None:
            print(f"filtered_left_all_world_cone_intersections: {packet.filtered_left_all_world_cone_intersections}")

        if packet.filtered_right_all_world_cone_intersections is not None:
            print(f"filtered_right_all_world_cone_intersections: {packet.filtered_right_all_world_cone_intersections}")

        if packet.left_blink_closing_mid_time is not None:
            print(f"left_blink_closing_mid_time: {packet.left_blink_closing_mid_time}")

        if packet.left_blink_opening_mid_time is not None:
            print(f"left_blink_opening_mid_time: {packet.left_blink_opening_mid_time}")

        if packet.left_blink_closing_amplitude is not None:
            print(f"left_blink_closing_amplitude: {packet.left_blink_closing_amplitude}")

        if packet.left_blink_opening_amplitude is not None:
            print(f"left_blink_opening_amplitude: {packet.left_blink_opening_amplitude}")

        if packet.left_blink_closing_speed is not None:
            print(f"left_blink_closing_speed: {packet.left_blink_closing_speed}")

        if packet.left_blink_opening_speed is not None:
            print(f"left_blink_opening_speed: {packet.left_blink_opening_speed}")

        if packet.right_blink_closing_mid_time is not None:
            print(f"right_blink_closing_mid_time: {packet.right_blink_closing_mid_time}")

        if packet.right_blink_opening_mid_time is not None:
            print(f"right_blink_opening_mid_time: {packet.right_blink_opening_mid_time}")

        if packet.right_blink_closing_amplitude is not None:
            print(f"right_blink_closing_amplitude: {packet.right_blink_closing_amplitude}")

        if packet.right_blink_opening_amplitude is not None:
            print(f"right_blink_opening_amplitude: {packet.right_blink_opening_amplitude}")

        if packet.right_blink_closing_speed is not None:
            print(f"right_blink_closing_speed: {packet.right_blink_closing_speed}")

        if packet.right_blink_opening_speed is not None:
            print(f"right_blink_opening_speed: {packet.right_blink_opening_speed}")

        if packet.left_eye_outer_corner3d is not None:
            print(f"left_eye_outer_corner3d: {packet.left_eye_outer_corner3d}")

        if packet.left_eye_inner_corner3d is not None:
            print(f"left_eye_inner_corner3d: {packet.left_eye_inner_corner3d}")

        if packet.right_eye_inner_corner3d is not None:
            print(f"right_eye_inner_corner3d: {packet.right_eye_inner_corner3d}")

        if packet.right_eye_outer_corner3d is not None:
            print(f"right_eye_outer_corner3d: {packet.right_eye_outer_corner3d}")

        if packet.left_nostril3d is not None:
            print(f"left_nostril3d: {packet.left_nostril3d}")

        if packet.right_nostril3d is not None:
            print(f"right_nostril3d: {packet.right_nostril3d}")

        if packet.left_mouth_corner3d is not None:
            print(f"left_mouth_corner3d: {packet.left_mouth_corner3d}")

        if packet.right_mouth_corner3d is not None:
            print(f"right_mouth_corner3d: {packet.right_mouth_corner3d}")

        if packet.left_ear3d is not None:
            print(f"left_ear3d: {packet.left_ear3d}")

        if packet.right_ear3d is not None:
            print(f"right_ear3d: {packet.right_ear3d}")

        if packet.left_eye_outer_corner2d is not None:
            print(f"left_eye_outer_corner2d: {packet.left_eye_outer_corner2d}")

        if packet.left_eye_inner_corner2d is not None:
            print(f"left_eye_inner_corner2d: {packet.left_eye_inner_corner2d}")

        if packet.right_eye_inner_corner2d is not None:
            print(f"right_eye_inner_corner2d: {packet.right_eye_inner_corner2d}")

        if packet.right_eye_outer_corner2d is not None:
            print(f"right_eye_outer_corner2d: {packet.right_eye_outer_corner2d}")

        if packet.left_nostril2d is not None:
            print(f"left_nostril2d: {packet.left_nostril2d}")

        if packet.right_nostril2d is not None:
            print(f"right_nostril2d: {packet.right_nostril2d}")

        if packet.left_mouth_corner2d is not None:
            print(f"left_mouth_corner2d: {packet.left_mouth_corner2d}")

        if packet.right_mouth_corner2d is not None:
            print(f"right_mouth_corner2d: {packet.right_mouth_corner2d}")

        if packet.left_ear2d is not None:
            print(f"left_ear2d: {packet.left_ear2d}")

        if packet.right_ear2d is not None:
            print(f"right_ear2d: {packet.right_ear2d}")

        if packet.nose_tip2d is not None:
            print(f"nose_tip2d: {packet.nose_tip2d}")

        if packet.mouth_shape_points2d is not None:
            print(f"mouth_shape_points2d: {packet.mouth_shape_points2d}")

        if packet.left_ear_shape_points2d is not None:
            print(f"left_ear_shape_points2d: {packet.left_ear_shape_points2d}")

        if packet.right_ear_shape_points2d is not None:
            print(f"right_ear_shape_points2d: {packet.right_ear_shape_points2d}")

        if packet.nose_shape_points2d is not None:
            print(f"nose_shape_points2d: {packet.nose_shape_points2d}")

        if packet.left_eye_shape_points2d is not None:
            print(f"left_eye_shape_points2d: {packet.left_eye_shape_points2d}")

        if packet.right_eye_shape_points2d is not None:
            print(f"right_eye_shape_points2d: {packet.right_eye_shape_points2d}")

        if packet.left_eyelid_state is not None:
            print(f"left_eyelid_state: {packet.left_eyelid_state}")

        if packet.left_eyelid_state_quality is not None:
            print(f"left_eyelid_state_quality: {packet.left_eyelid_state_quality}")

        if packet.right_eyelid_state is not None:
            print(f"right_eyelid_state: {packet.right_eyelid_state}")

        if packet.right_eyelid_state_quality is not None:
            print(f"right_eyelid_state_quality: {packet.right_eyelid_state_quality}")

        if packet.user_marker is not None:
            print(f"user_marker: {packet.user_marker}")

        if packet.camera_clocks is not None:
            print(f"camera_clocks: {packet.camera_clocks}")

        if packet.speaking is not None:
            print(f"speaking: {packet.speaking}")

        if packet.speaking_quality is not None:
            print(f"speaking_quality: {packet.speaking_quality}")

        if packet.profile_id is not None:
            print(f"profile_id: {packet.profile_id}")

        if packet.profile_id_quality is not None:
            print(f"profile_id_quality: {packet.profile_id_quality}")

        if packet.profile_id_state is not None:
            print(f"profile_id_state: {packet.profile_id_state}")

        if packet.drowsiness9_level is not None:
            print(f"drowsiness9_level: {packet.drowsiness9_level}")

        if packet.drowsiness9_level_quality is not None:
            print(f"drowsiness9_level_quality: {packet.drowsiness9_level_quality}")

        if packet.drowsiness9_level_status is not None:
            print(f"drowsiness9_level_status: {packet.drowsiness9_level_status}")

        if packet.glasses is not None:
            print(f"glasses: {packet.glasses}")

        if packet.glasses_quality is not None:
            print(f"glasses_quality: {packet.glasses_quality}")

        if packet.face_mask is not None:
            print(f"face_mask: {packet.face_mask}")

        if packet.face_mask_quality is not None:
            print(f"face_mask_quality: {packet.face_mask_quality}")

        if packet.left_eye_occluded is not None:
            print(f"left_eye_occluded: {packet.left_eye_occluded}")

        if packet.left_eye_occluded_quality is not None:
            print(f"left_eye_occluded_quality: {packet.left_eye_occluded_quality}")

        if packet.right_eye_occluded is not None:
            print(f"right_eye_occluded: {packet.right_eye_occluded}")

        if packet.right_eye_occluded_quality is not None:
            print(f"right_eye_occluded_quality: {packet.right_eye_occluded_quality}")

        if packet.anger is not None:
            print(f"anger: {packet.anger}")

        if packet.anger_quality is not None:
            print(f"anger_quality: {packet.anger_quality}")

        if packet.disgust is not None:
            print(f"disgust: {packet.disgust}")

        if packet.disgust_quality is not None:
            print(f"disgust_quality: {packet.disgust_quality}")

        if packet.happiness is not None:
            print(f"happiness: {packet.happiness}")

        if packet.happiness_quality is not None:
            print(f"happiness_quality: {packet.happiness_quality}")

        if packet.neutral is not None:
            print(f"neutral: {packet.neutral}")

        if packet.neutral_quality is not None:
            print(f"neutral_quality: {packet.neutral_quality}")

        if packet.sadness is not None:
            print(f"sadness: {packet.sadness}")

        if packet.sadness_quality is not None:
            print(f"sadness_quality: {packet.sadness_quality}")

        if packet.surprise is not None:
            print(f"surprise: {packet.surprise}")

        if packet.surprise_quality is not None:
            print(f"surprise_quality: {packet.surprise_quality}")

        if packet.valence is not None:
            print(f"valence: {packet.valence}")

        if packet.valence_quality is not None:
            print(f"valence_quality: {packet.valence_quality}")

        if packet.mood is not None:
            print(f"mood: {packet.mood}")

        if packet.mood_quality is not None:
            print(f"mood_quality: {packet.mood_quality}")

        if packet.dominant_emotion is not None:
            print(f"dominant_emotion: {packet.dominant_emotion}")

        if packet.dominant_emotion_quality is not None:
            print(f"dominant_emotion_quality: {packet.dominant_emotion_quality}")

    def prepare_data(self, packet: Packet):
        # Placeholder for sending data to connected clients
        #data = f'{packet.frame_number if packet.frame_number is not None else 0 };{packet.estimated_delay if packet.estimated_delay is not None else 0 };{packet.time_stamp if packet.time_stamp is not None else 0 };{packet.user_time_stamp if packet.user_time_stamp is not None else 0 };{packet.real_time_clock if packet.real_time_clock is not None else 0 };{packet.frame_rate if packet.frame_rate is not None else 0 };{packet.left_gaze_direction.x if packet.left_gaze_direction and packet.left_gaze_direction.x is not None else 0 };{packet.left_gaze_direction.y if packet.left_gaze_direction and packet.left_gaze_direction.y is not None else 0 };{packet.left_gaze_direction.z if packet.left_gaze_direction and packet.left_gaze_direction.z is not None else 0 };{packet.right_gaze_direction.x if packet.right_gaze_direction and packet.right_gaze_direction.x is not None else 0 };{packet.right_gaze_direction.y if packet.right_gaze_direction and packet.right_gaze_direction.y is not None else 0 };{packet.right_gaze_direction.z if packet.right_gaze_direction and packet.right_gaze_direction.z is not None else 0 };{packet.left_eye_position.x if packet.left_eye_position and packet.left_eye_position.x is not None else 0 };{packet.left_eye_position.y if packet.left_eye_position and packet.left_eye_position.y is not None else 0 };{packet.left_eye_position.z if packet.left_eye_position and packet.left_eye_position.z is not None else 0 };{packet.right_eye_position.x if packet.right_eye_position and packet.right_eye_position.x is not None else 0 };{packet.right_eye_position.y if packet.right_eye_position and packet.right_eye_position.y is not None else 0 };{packet.right_eye_position.z if packet.right_eye_position and packet.right_eye_position.z is not None else 0 };{packet.head_rotation_quality if packet.head_rotation_quality is not None else 0 };{packet.head_roll if packet.head_roll is not None else 0 };{packet.head_pitch if packet.head_pitch is not None else 0 };{packet.head_heading if packet.head_heading is not None else 0 };{packet.head_position.x if packet.head_position and packet.head_position.x is not None else 0 };{packet.head_position.y if packet.head_position and packet.head_position.y is not None else 0 };{packet.head_position.z if packet.head_position and packet.head_position.z is not None else 0 };{packet.head_position_quality if packet.head_position_quality is not None else 0 };{packet.head_rotation_rodrigues.x if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.x is not None else 0 };{packet.head_rotation_rodrigues.y if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.y is not None else 0 };{packet.head_rotation_rodrigues.z if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.z is not None else 0 };{packet.head_rotation_quaternion.x if packet.head_rotation_quaternion and packet.head_rotation_quaternion.x is not None else 0 };{packet.head_rotation_quaternion.y if packet.head_rotation_quaternion and packet.head_rotation_quaternion.y is not None else 0 };{packet.head_rotation_quaternion.z if packet.head_rotation_quaternion and packet.head_rotation_quaternion.z is not None else 0 };{packet.head_rotation_quaternion.w if packet.head_rotation_quaternion and packet.head_rotation_quaternion.w is not None else 0 };{packet.fixation if packet.fixation is not None else 0 };{packet.blink if packet.blink is not None else 0 };{packet.saccade if packet.saccade is not None else 0 };{1 if packet.left_closest_world_intersection is not None else 0 };{packet.left_closest_world_intersection.world_point.x if packet.left_closest_world_intersection and packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.x is not None else 0 };{packet.left_closest_world_intersection.world_point.y if packet.left_closest_world_intersection and  packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.y is not None else 0 };{packet.left_closest_world_intersection.world_point.z if packet.left_closest_world_intersection and  packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.z is not None else 0 };{1 if packet.right_closest_world_intersection is not None else 0 };{packet.right_closest_world_intersection.world_point.x if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.x is not None else 0 };{packet.right_closest_world_intersection.world_point.y if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.y is not None else 0 };{packet.right_closest_world_intersection.world_point.z if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.z is not None else 0 }'
        
        # include object name if available
        data = f'{packet.frame_number if packet.frame_number is not None else 0 };\
{packet.estimated_delay if packet.estimated_delay is not None else 0 };\
{packet.time_stamp if packet.time_stamp is not None else 0 };\
{packet.user_time_stamp if packet.user_time_stamp is not None else 0 };\
{packet.real_time_clock if packet.real_time_clock is not None else 0 };\
{packet.frame_rate if packet.frame_rate is not None else 0 };\
{packet.left_gaze_direction.x if packet.left_gaze_direction and packet.left_gaze_direction.x is not None else 0 };\
{packet.left_gaze_direction.y if packet.left_gaze_direction and packet.left_gaze_direction.y is not None else 0 };\
{packet.left_gaze_direction.z if packet.left_gaze_direction and packet.left_gaze_direction.z is not None else 0 };\
{packet.right_gaze_direction.x if packet.right_gaze_direction and packet.right_gaze_direction.x is not None else 0 };\
{packet.right_gaze_direction.y if packet.right_gaze_direction and packet.right_gaze_direction.y is not None else 0 };\
{packet.right_gaze_direction.z if packet.right_gaze_direction and packet.right_gaze_direction.z is not None else 0 };\
{packet.left_eye_position.x if packet.left_eye_position and packet.left_eye_position.x is not None else 0 };\
{packet.left_eye_position.y if packet.left_eye_position and packet.left_eye_position.y is not None else 0 };\
{packet.left_eye_position.z if packet.left_eye_position and packet.left_eye_position.z is not None else 0 };\
{packet.right_eye_position.x if packet.right_eye_position and packet.right_eye_position.x is not None else 0 };\
{packet.right_eye_position.y if packet.right_eye_position and packet.right_eye_position.y is not None else 0 };\
{packet.right_eye_position.z if packet.right_eye_position and packet.right_eye_position.z is not None else 0 };\
{packet.head_rotation_quality if packet.head_rotation_quality is not None else 0 };\
{packet.head_roll if packet.head_roll is not None else 0 };\
{packet.head_pitch if packet.head_pitch is not None else 0 };\
{packet.head_heading if packet.head_heading is not None else 0 };\
{packet.head_position.x if packet.head_position and packet.head_position.x is not None else 0 };\
{packet.head_position.y if packet.head_position and packet.head_position.y is not None else 0 };\
{packet.head_position.z if packet.head_position and packet.head_position.z is not None else 0 };\
{packet.head_position_quality if packet.head_position_quality is not None else 0 };\
{packet.head_rotation_rodrigues.x if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.x is not None else 0 };\
{packet.head_rotation_rodrigues.y if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.y is not None else 0 };\
{packet.head_rotation_rodrigues.z if packet.head_rotation_rodrigues and packet.head_rotation_rodrigues.z is not None else 0 };\
{packet.head_rotation_quaternion.x if packet.head_rotation_quaternion and packet.head_rotation_quaternion.x is not None else 0 };\
{packet.head_rotation_quaternion.y if packet.head_rotation_quaternion and packet.head_rotation_quaternion.y is not None else 0 };\
{packet.head_rotation_quaternion.z if packet.head_rotation_quaternion and packet.head_rotation_quaternion.z is not None else 0 };\
{packet.head_rotation_quaternion.w if packet.head_rotation_quaternion and packet.head_rotation_quaternion.w is not None else 0 };\
{packet.fixation if packet.fixation is not None else 0 };\
{packet.blink if packet.blink is not None else 0 };\
{packet.saccade if packet.saccade is not None else 0 };\
{1 if packet.left_closest_world_intersection is not None else 0 };\
{packet.left_closest_world_intersection.world_point.x if packet.left_closest_world_intersection and packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.x is not None else 0 };\
{packet.left_closest_world_intersection.world_point.y if packet.left_closest_world_intersection and  packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.y is not None else 0 };\
{packet.left_closest_world_intersection.world_point.z if packet.left_closest_world_intersection and  packet.left_closest_world_intersection.world_point and packet.left_closest_world_intersection.world_point.z is not None else 0 };\
{1 if packet.right_closest_world_intersection is not None else 0 };\
{packet.right_closest_world_intersection.world_point.x if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.x is not None else 0 };\
{packet.right_closest_world_intersection.world_point.y if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.y is not None else 0 };\
{packet.right_closest_world_intersection.world_point.z if packet.right_closest_world_intersection and  packet.right_closest_world_intersection.world_point and packet.right_closest_world_intersection.world_point.z is not None else 0 };\
{packet.left_closest_world_intersection.object_name if packet.left_closest_world_intersection and packet.left_closest_world_intersection.object_name is not None else "" };\
{packet.right_closest_world_intersection.object_name if packet.right_closest_world_intersection and packet.right_closest_world_intersection.object_name is not None else "" }'
        return data
    
    def connect(self):
        try:
            self.client = UDPClient("0.0.0.0", self.port, timeout=50.0)        
            # Connect client to start receiving packets.
            self.client.connect()
            self.running = True
            self._notify_status_change(True)
            self._notify_message(f"SmartEye: Listening on port {self.port}", "Success")
            return f"Listening for SEP on port {self.port}"
        except Exception as e:
            self._notify_status_change(False)
            self._notify_message(f"SmartEye: Error connecting to port {self.port} - {e}", "Error")
            return f"Error connecting to port {self.port}: {e}"
        
    def start(self):
        # Handle packets by continuously calling receive.
        try:
            while self.running == True:
                packet = self.client.receive()
                se_data = self.prepare_data(packet)
                data = f"E;1;SEP;1;;;;SEP_DX;{se_data}\r\n"
                #print(data)
                if self.stream:
                    self.stream.send(data.encode())
                    #time.sleep(0.1)  # Slight delay to prevent CPU overload
        except EndOfStreamError:
            logging.info("Remote end closed the stream, shutting down.")
        except TimeoutError:
            logging.info("Connection timed out, shutting down.")
        except KeyboardInterrupt:
            logging.info("Caught keyboard interrupt, shutting down.")
        except OSError as e:
            pass
        finally:
            if self.client is not None:
                self.client.disconnect()
    
    def test(self):
        try:
            while self.running == True:
                packet = self.client.receive()
                self.print_packet(packet)
        except EndOfStreamError:
            logging.info("Remote end closed the stream, shutting down.")
    
    def stop(self):
        self.running = False
        # Close the client connection
        if self.client is not None:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None
        self._notify_status_change(False)
        self._notify_message("SmartEye: Disconnected", "Info")        
        #print("Server stopped")

    def status(self):
        return self.running

if __name__ == "__main__":
    smarteye = SEListener(port=8089)
    smarteye.connect()
    smarteye.test()