#!/usr/bin/env python3

from pathlib import Path
import cv2
import depthai as dai
import numpy as np
import time
import argparse
import torch
#import torch.nn as nn
#import torch.nn.functional as F
#import torch.optim as optim
import matplotlib.pyplot as plt
import SD2_Model as SD

nnPathDefault = str((Path(__file__).parent / Path('../yolo_v4_tiny_openvino_2021.3_6shave.blob')).resolve().absolute())

# Set the path of the second NN
nnCoordinatePathDefault = './best_2nd_NN.pt'
      
gpu_device = torch.device("cuda")
model = SD.Net().to(gpu_device)

# Load the entire model
model = torch.load(nnCoordinatePathDefault)
model.eval()

#live plot setup
plt.ion()
fig, ax = plt.subplots()
x, y = [],[]
sc = ax.scatter(x,y)
plt.xlim(-1,1)
plt.ylim(-1,1)
plt.xlabel("X axis label")
plt.ylabel("Y axis label")
plt.title('drone position')
plt.grid()
plt.draw()

def drawDronepos(x,y):
    sc.set_offsets(np.c_[x,y])
    fig.canvas.draw_idle()
    #plt.pause(0.001)

#
parser = argparse.ArgumentParser()
parser.add_argument('nnPath', nargs='?', help="Path to mobilenet detection network blob", default=nnPathDefault)
parser.add_argument('-s', '--sync', action="store_true", help="Sync RGB output with NN output", default=False)
args = parser.parse_args()
if not Path(nnPathDefault).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# yolo label texts
labelMap = ["drone"]
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

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Output queues will be used to get the rgb frames and nn data from the outputs defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    qDet = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

    frame = None
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
        for detection in detections:
            bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
            #cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            #cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            #print(bbox[0], bbox[1],bbox[2] ,bbox[3])
            x = int(((bbox[2]-bbox[0])/2)+bbox[0])
            y = int(((bbox[3]-bbox[1])/2)+bbox[1])

            # Inputting data into model
            model_input = torch.tensor([x - 256,y -160]).to(gpu_device).float()
            #print(model_input)

            # transform column tensor to row tensor
            output = model(model_input)

            # convert tensor to numpy array
            output_converted_numpy = output.cpu().detach().numpy()
            #print(output_converted_numpy)

            # extract x and y values for output and round to the 2nd nearest decimal place
            output_x = round(output_converted_numpy[0], 2)
            output_y = round(output_converted_numpy[1], 2)
            #draw to live graph
            drawDronepos(output_x,output_y)
            cv2.putText(frame, f"{x,y}", (100, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            cv2.putText(frame, f"{output_x, output_y}", (200, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            cv2.circle(frame, (x,y), radius=2, color=(255, 0, 0), thickness=-1)
            #print(detection.label)
        # Show the frame
        cv2.imshow(name, frame)

    while True:
        if syncNN:
            inRgb = qRgb.get()
            inDet = qDet.get()
        else:
            inRgb = qRgb.tryGet()
            inDet = qDet.tryGet()

        if inRgb is not None:
            frame = inRgb.getCvFrame()
            #marker dots for camera orientation
            cv2.circle(frame, (int(frame.shape[1]/2),int(frame.shape[0]/2)), radius=2, color=(0, 0, 0), thickness=-1) #center
            cv2.circle(frame, (187,84), radius=2, color=(0, 0, 0), thickness=-1) #top-left
            cv2.circle(frame, (320,65), radius=2, color=(0, 0, 0), thickness=-1) #top-right
            cv2.circle(frame, (183,238), radius=2, color=(0, 0, 0), thickness=-1) #bottom-left
            cv2.circle(frame, (325,232), radius=2, color=(0, 0, 0), thickness=-1) #bottom-right
            cv2.putText(frame, "NN fps: {:.2f}".format(counter / (time.monotonic() - startTime)),
                        (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color2) #FPS counter

        if inDet is not None:
            detections = inDet.detections
            counter += 1

        if frame is not None:
            displayFrame("rgb", frame)

        if cv2.waitKey(1) == ord('q'):
            break