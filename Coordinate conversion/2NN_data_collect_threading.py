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
#from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander
import LogHelper as LH
import threading

## data colletion
import csv
save = True
dataset_save_path = "2NN_dataset.csv"
##global

## crazyflie setup
URI = 'radio://0/80/2M'
# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)
# flight variables
keep_flying = False

def sequence(scf,pc):
    global keep_flying
    pc.go_to(-0.5, 0.5, 0.3)
    for x in np.arange(-0.5,0.6,0.1):
        for y in np.arange(0.5,-0.6,-0.1):
            if(not keep_flying):
                pc.go_to(0.0, 0.0, 0.0)
                return
            #print(round(x,1),round(y,1))
            pc.go_to(round(x,1), round(y,1), 0.3)
            #LH.getLHPos(scf)
            time.sleep(0.2)
    pc.go_to(0.0, 0.0, 0.0)
    keep_flying = False
    print("drone done. trying to land")
    pc.land()

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
            #with MotionCommander(scf) as motion_commander:
            with PositionHlCommander(scf, x=0.0, y=0.0, z=0.0, default_velocity=0.1, default_height=0.3) as pc:
                with open(dataset_save_path,'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # set true for flight
                    keep_flying = True
                    print("starting move_thread")
                    move_thread = threading.Thread(target=sequence, args=(scf,pc,))
                    move_thread.start()

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
            
                    while keep_flying:
                        
                        #motion_commander.start_linear_motion( cntr_object.vector_x, cntr_object.vector_y, cntr_object.vector_z)
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
                            #displayFrame("rgb", frame)
                            color = (255, 0, 0)
                            for detection in detections:
                                bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                                drone_frame_X = int(((bbox[2]-bbox[0])/2)+bbox[0])
                                drone_frame_Y = int(((bbox[3]-bbox[1])/2)+bbox[1])

                                cv2.putText(frame, f"{drone_frame_X,drone_frame_Y}", (100, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                                cv2.circle(frame, (drone_frame_X,drone_frame_Y), radius=2, color=(255, 0, 0), thickness=-1)
                                if(save):
                                    writer.writerow([drone_frame_X,drone_frame_Y,drone_data[0],drone_data[1],drone_data[2]])

                                print([drone_frame_X,drone_frame_Y,drone_data[0],drone_data[1],drone_data[2]])    
                            cv2.imshow("rgb", frame)

                        if cv2.waitKey(1) == ord('q'):
                            keep_flying = False
                            move_thread.join()
                            break
    keep_flying = False
    move_thread.join()