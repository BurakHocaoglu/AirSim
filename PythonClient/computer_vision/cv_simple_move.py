# In settings.json first activate computer vision mode: 
# https://github.com/Microsoft/AirSim/blob/master/docs/image_apis.md#computer-vision-mode

import setup_path 
import airsim

# import pprint
import tempfile
import os
import time

# pp = pprint.PrettyPrinter(indent=4)

client = airsim.VehicleClient()
client.confirmConnection()

# airsim.to_quaternion(pitch, roll, yaw)
client.simSetCameraPose("0", airsim.Pose(airsim.Vector3r(0, 0, -1), 
                                         airsim.to_quaternion(0, 0, 0)))

for x in range(25):
    client.simSetVehiclePose(airsim.Pose(airsim.Vector3r(x, 0, -1), 
                                         airsim.to_quaternion(0, 0, 0)), True)
    # time.sleep(0.1)

    # pp.pprint(client.simGetVehiclePose())
    # print(client.simGetVehiclePose())
    time.sleep(3)

client.simSetVehiclePose(airsim.Pose(airsim.Vector3r(0, 0, 0), airsim.to_quaternion(0, 0, 0)), True)