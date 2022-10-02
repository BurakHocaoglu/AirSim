import setup_path
import airsim
import time
import os
import numpy as np

# This example shows how to use the External Physics Engine
# It allows you to control the drone through setVehiclePose and obtain collision information.
# It is especially useful for injecting your own flight dynamics model to the AirSim drone.

# Use Blocks environment to see the drone colliding and seeing the collision information 
# in the command prompt.

# Add this line to your settings.json before running AirSim:
# "PhysicsEngineName":"ExternalPhysicsEngine"

client = airsim.VehicleClient()
client.confirmConnection()
# pose = client.simGetVehiclePose()

tmp_dir = "/home/burak/airsim-cv-recording"

# pose.orientation = airsim.to_quaternion(0.1, 0.1, 0.1)
# client.simSetVehiclePose(pose, False)

# r, p, y = 0, 0, 0

for i in range(200):
	# # responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, compress=False)])
	# responses = client.simGetImages([airsim.ImageRequest("Cam0", airsim.ImageType.Scene)])
	# if len(responses) < 0:
	# 	print("No response!")
	# 	continue

	# response = responses[0]
	# W, H = response.width, response.height
	# C = len(response.image_data_uint8) / (W * H)

	# img_path = os.path.normpath(os.path.join(tmp_dir, "Image_" + str(i) + '.png'))
	# print("%s" % (img_path, ))
	# airsim.write_file(img_path, response.image_data_uint8)
	# # airsim.write_png(img_path, np.frombuffer(response.image_data_uint8, dtype=np.uint8))

	pose = client.simGetVehiclePose()
	pose.position = pose.position + airsim.Vector3r(0.05, 0, 0)
	# pose.orientation = pose.orientation + airsim.to_quaternion(1, 1, 1)

	# p, r, y = airsim.to_eularian_angles(pose.orientation)
	# p += 0.1
	# r += 0.1
	# y += 0.1

	# pose.orientation = airsim.to_quaternion(p, r, y)
	pose.orientation = airsim.to_quaternion(0, 0, 0)

	client.simSetVehiclePose(pose, False)
	time.sleep(0.1)

	# collision = client.simGetCollisionInfo()
	# if collision.has_collided:
	# 	print(collision)

client.reset()