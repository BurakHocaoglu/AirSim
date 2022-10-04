import os
import sys
import time
import setup_path
import airsim
import cv2
import traceback
import numpy as np

from datetime import datetime

def generate_sweep_path(x0, y0, length, spacing, count, resolution=100):
	i = 0
	is_south = False
	path_segments = []

	R = spacing / 2.
	x_start = x0
	x_end = x0 + length
	while i < count:
		y_i = y0 + i * spacing
		yaw = int(is_south) * np.pi
		yaw_end = (1 - int(is_south)) * np.pi

		v_x = np.linspace(x_start, x_end, resolution, False).reshape(1, -1).T
		v_y = np.repeat([[y_i]], resolution, axis=1).T
		v_theta = np.repeat([[yaw]], resolution, axis=1).T

		straight = np.hstack((v_x, v_y, v_theta))

		curve = np.linspace(yaw, yaw_end, 500).reshape(1, -1).T
		local_curve = np.linspace(yaw - np.pi / 2., yaw + np.pi / 2., 500).reshape(1, -1).T
		if is_south:
			local_curve = np.flip(local_curve)

		v_c_x = x_end + R * np.cos(local_curve)
		v_c_y = y_i + R * (1 + np.sin(local_curve))
		transition = np.hstack((v_c_x, v_c_y, curve))

		path_segments.append(straight)
		path_segments.append(transition)

		is_south = not is_south
		x_start = x_end
		x_end = x_start + (- 1) ** int(is_south) * length
		i += 1

	return path_segments

if __name__ == "__main__":
	lane_length = float(sys.argv[1])
	lane_spacing = float(sys.argv[2])
	lane_count = int(sys.argv[3])

	motion_resolution = 100 if len(sys.argv) < 5 else int(sys.argv[4])
	period = 25. if len(sys.argv) < 6 else float(sys.argv[5])
	agent_mode = "multirotor" if len(sys.argv) < 7 else sys.argv[6]

	if agent_mode != "multirotor" and agent_mode != "vision":
		print(f"Unknown mode {agent_mode}! Exiting...")
		sys.exit(1)

	delta = 1. / motion_resolution

	orient = None
	if agent_mode == "multirotor":
		orient = lambda p, r, y: airsim.to_quaternion(0, 0, y)

	else:
		orient = lambda p, r, y: airsim.to_quaternion(p, 0, y)

	client = airsim.VehicleClient()

	try:
		client.confirmConnection()
	except Exception as e:
		# raise e
		print(traceback.format_exc())
		time.sleep(1.)

	pose = client.simGetVehiclePose()
	pitch_0, roll_0, yaw_0 = airsim.to_eularian_angles(pose.orientation)
	print(f"Start Rot. (P, R, Y): {180.0 * pitch_0 / np.pi}, \
		{180.0 * roll_0 / np.pi}, \
		{180.0 * yaw_0 / np.pi}")

	# sweep_path = generate_sweep_path(pose.position.x_val, pose.position.y_val, 
	# 	lane_length, lane_spacing, lane_count, motion_resolution * period)

	# for segment in sweep_path:
	# 	for wp in segment:
	# 		print("Next: ({:.3f}, {:.3f}, {:.3f})".format(wp[0], wp[1], wp[2]))
	# 		client.simSetVehiclePose(airsim.Pose(airsim.Vector3r(wp[0], wp[1], pose.position.z_val), 
	# 											 airsim.to_quaternion(0, 0, wp[2])), False)
	# 		time.sleep(delta)

	i = 0
	is_south = False
	R = lane_spacing / 2.
	x_start = pose.position.x_val
	x_end = x_start + lane_length
	resolution = int(np.round(motion_resolution * period))

	while i < lane_count:
		y_i = pose.position.y_val + i * lane_spacing
		yaw = int(is_south) * np.pi
		yaw_end = (1 - int(is_south)) * np.pi

		v_x = np.linspace(x_start, x_end, resolution, False)
		for k_s in range(resolution):
			# client.simSetVehiclePose(airsim.Pose(
			# 							airsim.Vector3r(v_x[k_s], y_i, pose.position.z_val), 
			# 							airsim.to_quaternion(0, 0, yaw)), 
			# 						 False)
			client.simSetVehiclePose(airsim.Pose(
										airsim.Vector3r(v_x[k_s], y_i, pose.position.z_val), 
										orient(pitch_0, roll_0, yaw)), 
									 False)

			time.sleep(delta)

		curve = np.linspace(yaw, yaw_end, 250)
		local_curve = np.linspace(yaw - np.pi / 2., yaw + np.pi / 2., 250)
		if is_south:
			local_curve = np.flip(local_curve)

		v_c_x = x_end + R * np.cos(local_curve)
		v_c_y = y_i + R * (1 + np.sin(local_curve))
		for k_c in range(250):
			# client.simSetVehiclePose(airsim.Pose(
			# 							airsim.Vector3r(v_c_x[k_c], v_c_y[k_c], pose.position.z_val), 
			# 							airsim.to_quaternion(0, 0, curve[k_c])), 
			# 						 False)
			client.simSetVehiclePose(airsim.Pose(
										airsim.Vector3r(v_c_x[k_c], v_c_y[k_c], pose.position.z_val), 
										orient(pitch_0, roll_0, curve[k_c])), 
									 False)

			time.sleep(delta)

		is_south = not is_south
		x_start = x_end
		x_end = x_start + (- 1) ** int(is_south) * lane_length

		i += 1
		print(f"Lane {i} done.")

	client.reset()