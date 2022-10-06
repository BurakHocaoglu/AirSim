import os
import sys
import time
# import setup_path
import airsim
import json

import traceback
import numpy as np

from datetime import datetime

if __name__ == "__main__":
	content = None
	opts_path = os.environ["HOME"] + "/Documents/AirSim/rtsp_opts.json"
	with open(opts_path, 'r') as OPTS:
		content = json.load(OPTS)

	if content is None:
		raise ValueError("content is None!")

	client_addr = content["client_addr"]
	client_port = content["client_port"]

	lane_length = content["lane_length"]
	lane_spacing = content["motion_spacing"]
	lane_count = content["lane_count"]

	motion_resolution = content["motion_resolution"]
	motion_speed = content["motion_speed"]
	# period = content["motion_period"]
	period = float(lane_length) / float(motion_speed)

	agent_mode = content["sim_mode"].lower()
	if agent_mode != "multirotor" and agent_mode != "vision":
		print(f"Unknown mode {agent_mode}! Exiting...")
		sys.exit(1)

	delta = 1. / motion_resolution

	orient = None
	if agent_mode == "multirotor":
		orient = lambda p, r, y: airsim.to_quaternion(0, 0, y)

	else:
		orient = lambda p, r, y: airsim.to_quaternion(p, 0, y)

	client = airsim.VehicleClient(ip=client_addr, port=client_port)

	try:
		client.confirmConnection()
		time.sleep(1.)
	except Exception as e:
		# raise e
		print(traceback.format_exc())
		time.sleep(1.)

	pose = client.simGetVehiclePose()
	pitch_0, roll_0, yaw_0 = airsim.to_eularian_angles(pose.orientation)
	print(f"Start Rot. (P, R, Y): {180.0 * pitch_0 / np.pi}, \
		{180.0 * roll_0 / np.pi}, \
		{180.0 * yaw_0 / np.pi}")

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