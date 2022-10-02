import os
import sys
import time
import setup_path
import airsim
import cv2

import numpy as np

from datetime import datetime

def get_images(client, idx, savedirs):
	responses = client.simGetImages([
		airsim.ImageRequest("Cam0", airsim.ImageType.Scene, False, False), 
		airsim.ImageRequest("Cam0", airsim.ImageType.Segmentation, False, False)
	])

	if len(responses) < 2:
		print(f"<{idx}> No response is obtained!")
		return

	for response in responses:
		if len(response.image_data_uint8) != response.height * response.width * 3:
			print(f"<{idx}> Response [{response.image_type}] is empty!")
			continue

		img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
		img_rgb = img1d.reshape(response.height, response.width, 3)

		filename = "{}/img_".format(savedirs["root"])
		if response.image_type == airsim.ImageType.Scene:
			filename = "{}/img_scene_".format(savedirs["scene"])

		elif response.image_type == airsim.ImageType.Segmentation:
			filename = "{}/img_seg_".format(savedirs["segmentation"])

		else:
			print(f"Not implemented for image type {response.image_type}")

		cv2.imwrite(os.path.normpath(filename + str(idx) + '.png'), img_rgb)

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
	client.confirmConnection()


	found = client.simSetSegmentationObjectID("Landscape[\w]*", 0, True)
	print("Landscape found: %r" % (found))

	found = client.simSetSegmentationObjectID("SkyDomeMesh[\w]*", 255, True)
	print("SkyDomeMesh found: %r" % (found))

	found = client.simSetSegmentationObjectID("WhiteOrnamentalKale[\w]*", 42, True)
	print("White Kale found: %r" % (found))

	found = client.simSetSegmentationObjectID("Sage[\w]*", 43, True)
	print("Sage found: %r" % (found))

	found = client.simSetSegmentationObjectID("Basil[\w]*", 44, True)
	print("Basil found: %r" % (found))


	pose = client.simGetVehiclePose()
	pitch_0, roll_0, yaw_0 = airsim.to_eularian_angles(pose.orientation)
	print(f"Start Rot. (P, R, Y): {180.0 * pitch_0 / np.pi}, \
		{180.0 * roll_0 / np.pi}, \
		{180.0 * yaw_0 / np.pi}")

	i = 0
	k = 0
	is_south = False
	R = lane_spacing / 2.
	x_start = pose.position.x_val
	x_end = x_start + lane_length
	resolution = int(np.round(motion_resolution * period))

	save_dir = "/home/burak/airsim-cv-recording/imgs/{}".format(datetime.now())
	scene_imgs_dir = "{}/scene".format(save_dir)
	segmentation_imgs_dir = "{}/segmentation".format(save_dir)
	os.makedirs(save_dir)
	os.makedirs(scene_imgs_dir)
	os.makedirs(segmentation_imgs_dir)

	dirs = {
		"root": save_dir,
		"scene": scene_imgs_dir,
		"segmentation": segmentation_imgs_dir,
	}

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

			get_images(client, k, dirs)
			k += 1

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