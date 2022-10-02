# In settings.json first activate computer vision mode: 
# https://github.com/Microsoft/AirSim/blob/master/docs/image_apis.md#computer-vision-mode

import os
import airsim
import cv2
import numpy as np
import setup_path
import time

client = airsim.VehicleClient()
client.confirmConnection()

airsim.wait_key('Press any key to change one ground object ID')
found = client.simSetSegmentationObjectID("Landscape", 0)
print("Landscape found: %r" % (found))

found = client.simSetSegmentationObjectID("SkyDomeMesh", 20)
print("SkyDomeMesh found: %r" % (found))

# found = client.simSetSegmentationObjectID("SkyDomeMesh", 0)
# print("SkySphere found: %r" % (found))

for i in range(10):
    responses = client.simGetImages([
        airsim.ImageRequest("Cam0", airsim.ImageType.Segmentation, False, False)
    ])

    for idx, response in enumerate(responses):
        filename = '/home/burak/airsim-cv-recording/imgs/py_seg_' + str(i) + "_" + str(idx)

        if response.pixels_as_float:
            print("Type %d, size %d" % (response.image_type, len(response.image_data_float)))
            airsim.write_pfm(os.path.normpath(filename + '.pfm'), airsim.get_pfm_array(response))

        elif response.compress:
            print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
            airsim.write_file(os.path.normpath(filename + '.png'), response.image_data_uint8)

        else:
            print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
            img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
            img_rgb = img1d.reshape(response.height, response.width, 3)
            cv2.imwrite(os.path.normpath(filename + '.png'), img_rgb)

            print(np.unique(img_rgb[:,:,0], return_counts=True))
            print(np.unique(img_rgb[:,:,1], return_counts=True))
            print(np.unique(img_rgb[:,:,2], return_counts=True))

    pose = client.simGetVehiclePose()
    pose.position.x_val += 1.

    client.simSetVehiclePose(pose, False)
    time.sleep(1.)

client.reset()