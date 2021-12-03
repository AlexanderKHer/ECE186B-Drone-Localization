#!/usr/bin/env python3

from pathlib import Path
import cv2
import depthai as dai
import numpy as np
import time
import argparse

## crazyflie imports
import logging
import sys
import time
import keyboard

import cflib.crtp # crazie_radio lib
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
import LogHelper as LH
##
##global
drone_frame_X = 0
drone_frame_Y = 0

## crazyflie setup
# my vector object
class controller_class:
    def __init__(self): # class constructor
        self.vector_x = 0
        self.vector_y = 0
        self.vector_z = 0
        self.yaw = 0
        self.keep_flying = False
    
    # debug print
    def print_vectors(self):
        print(f'{ self.vector_x},{ self.vector_y},{ self.vector_z}')

# create my vector object
cntr_object = controller_class()


# my keyboard callback function
# gets called anytime there is a keyboard event
# responds to WASD and q and, arrow keys
# requires cntr_object to exist
def key_events_callback(e):
    #for code in keyboard._pressed_events:
    #    print(code)
    k = list(keyboard._pressed_events.keys())
    # press q to unhook keyboard events
    if 16 in k:
        # stop the crazyflie flying
        cntr_object.keep_flying = False
        keyboard.unhook_all()
        
    # up key and not down key    
    if 72 in k and 80 not in k: # forward
        cntr_object.vector_x = 0.5
    elif  80 in k and 72 not in k: # back
        cntr_object.vector_x = -0.5
    else:
        cntr_object.vector_x = 0
    
    # left key and not right key
    if 75 in k and 77 not in k: # left
        cntr_object.vector_y = 0.5
    elif  77 in k and 75 not in k: # right
        cntr_object.vector_y = -0.5
    else:
        cntr_object.vector_y = 0
       
    # 'w' key and not 's' key
    if 17 in k and 31 not in k: #z up
        cntr_object.vector_z = 0.2
    elif  31 in k and 17 not in k: #z down
        cntr_object.vector_z = -0.2
    else:
        cntr_object.vector_z = 0

URI = 'radio://0/80/2M'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

## depth camera setup

nnPathDefault = str((Path(__file__).parent / Path('../yolo_v4_tiny_openvino_2021.3_6shave.blob')).resolve().absolute())
#
parser = argparse.ArgumentParser()
parser.add_argument('nnPath', nargs='?', help="Path to mobilenet detection network blob", default=nnPathDefault)
parser.add_argument('-s', '--sync', action="store_true", help="Sync RGB output with NN output", default=False)
args = parser.parse_args()

if not Path(nnPathDefault).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# MobilenetSSD label texts
labelMap = '../label_map.pbtxt'


syncNN = True

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
camRgb = pipeline.create(dai.node.ColorCamera)
detectionNetwork = pipeline.create(dai.node.YoloDetectionNetwork)
xoutRgb = pipeline.create(dai.node.XLinkOut)
nnOut = pipeline.create(dai.node.XLinkOut)

xoutRgb.setStreamName("rgb")
nnOut.setStreamName("nn")

# Properties
camRgb.setPreviewSize(512, 320)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
camRgb.setFps(60)

# Network specific settings
detectionNetwork.setConfidenceThreshold(0.5)
detectionNetwork.setNumClasses(1)
detectionNetwork.setCoordinateSize(4)
detectionNetwork.setAnchors(np.array([10, 14, 23, 27, 37, 58, 81, 82, 135, 169, 344, 319]))
#detectionNetwork.setAnchorMasks({"side26": np.array([1, 2, 3]), "side13": np.array([3, 4, 5])})
detectionNetwork.setAnchorMasks({"side32": np.array([1, 2, 3]), "side16": np.array([3, 4, 5])})
#detectionNetwork.setIouThreshold(0.8)
detectionNetwork.setBlobPath(nnPathDefault)
detectionNetwork.setNumInferenceThreads(2)
detectionNetwork.input.setBlocking(False)

# Linking
camRgb.preview.link(detectionNetwork.input)
if syncNN:
    detectionNetwork.passthrough.link(xoutRgb.input)
else:
    camRgb.preview.link(xoutRgb.input)

detectionNetwork.out.link(nnOut.input)


if __name__ == '__main__':
    # Connect to device and start pipeline
    with dai.Device(pipeline) as device:

        # Initialize the low-level drivers (don't list the debug drivers)
        cflib.crtp.init_drivers(enable_debug_driver=False)

        cf = Crazyflie(rw_cache='./cache')
        with SyncCrazyflie(URI, cf=cf) as scf:
            with MotionCommander(scf) as motion_commander:
                # set true for flight
                cntr_object.keep_flying = True
                keyboard.hook(key_events_callback)

                # Output queues will be used to get the rgb frames and nn data from the outputs defined above
                qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
                qDet = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

                frame = None
                #drone_frame_X = 0
                #drone_frame_Y = 0
                detections = []
                startTime = time.monotonic()
                counter = 0
                color2 = (255, 255, 255)

                # nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
                def frameNorm(frame, bbox):
                    normVals = np.full(len(bbox), frame.shape[0])
                    normVals[::2] = frame.shape[1]
                    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

                def displayFrame(name, frame):
                    color = (255, 0, 0)
                    global drone_frame_X
                    global drone_frame_Y
                    for detection in detections:
                        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                        #cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        #cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                        drone_frame_X = int(((bbox[2]-bbox[0])/2)+bbox[0])
                        drone_frame_Y = int(((bbox[3]-bbox[1])/2)+bbox[1])

                        #print(x,y)
                        cv2.putText(frame, f"{drone_frame_X,drone_frame_Y}", (100, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                        cv2.circle(frame, (drone_frame_X,drone_frame_Y), radius=2, color=(255, 0, 0), thickness=-1)
                    # Show the frame
                    cv2.imshow(name, frame)

                while cntr_object.keep_flying:

                    motion_commander.start_linear_motion( cntr_object.vector_x, cntr_object.vector_y, cntr_object.vector_z)
                    drone_data = LH.getLHPos(scf)
                    # send packets at a specific interval
                    time.sleep(0.01)
                    if syncNN:
                        inRgb = qRgb.get()
                        inDet = qDet.get()
                    else:
                        inRgb = qRgb.tryGet()
                        inDet = qDet.tryGet()

                    if inRgb is not None:
                        frame = inRgb.getCvFrame()
                        cv2.circle(frame, (int(frame.shape[1]/2),int(frame.shape[0]/2)), radius=2, color=(0, 0, 0), thickness=-1)
                        #dots for camera orientation
                        cv2.circle(frame, (187,84), radius=2, color=(0, 0, 0), thickness=-1)
                        cv2.circle(frame, (320,65), radius=2, color=(0, 0, 0), thickness=-1)
                        cv2.circle(frame, (183,238), radius=2, color=(0, 0, 0), thickness=-1)
                        cv2.circle(frame, (325,232), radius=2, color=(0, 0, 0), thickness=-1)
                        cv2.putText(frame, "NN fps: {:.2f}".format(counter / (time.monotonic() - startTime)),
                                    (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color2)

                    if inDet is not None:
                        detections = inDet.detections
                        counter += 1

                    if frame is not None:
                        displayFrame("rgb", frame)
                        # write to csv
                        print(drone_frame_X,drone_frame_Y,drone_data)

                    if cv2.waitKey(1) == ord('q'):
                        break

