#!/usr/bin/env python3

from pathlib import Path
import sys
import cv2
import depthai as dai
import numpy as np
from time import monotonic

# Get argument first
parentDir = Path(__file__).parent
nnPath = str((parentDir / Path('yolo_v4_tiny_openvino_2021.3_6shave.blob')).resolve().absolute())
videoPath = str((parentDir / Path('IMG_0103.mp4')).resolve().absolute())
if len(sys.argv) > 2:
    nnPath = sys.argv[1]
    videoPath = sys.argv[2]

if not Path(nnPath).exists() or not Path(videoPath).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

# our label map for the YOLOv4-Tiny Network
labelMap = ["drone"]

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
nn = pipeline.create(dai.node.YoloDetectionNetwork)

xinFrame = pipeline.create(dai.node.XLinkIn)
nnOut = pipeline.create(dai.node.XLinkOut)

xinFrame.setStreamName("inFrame")
nnOut.setStreamName("nn")

# Properties
# our yolo model is using a resolution of 512 x 320
nn.setNumClasses(1)
nn.setCoordinateSize(4)
nn.setAnchors(np.array([10, 14, 23, 27, 37, 58, 81, 82, 135, 169, 344, 319]))
nn.setAnchorMasks({"side32": np.array([1, 2, 3]), "side16": np.array([3, 4, 5])})
nn.setConfidenceThreshold(0.5)
nn.setBlobPath(nnPath)
nn.setNumInferenceThreads(2)
nn.input.setBlocking(False)

# Linking
xinFrame.out.link(nn.input)
nn.out.link(nnOut.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    # Input queue will be used to send video frames to the device.
    qIn = device.getInputQueue(name="inFrame")
    # Output queue will be used to get nn data from the video frames.
    qDet = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

    frame = None
    detections = []

    # nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
    def frameNorm(frame, bbox):
        normVals = np.full(len(bbox), frame.shape[0])
        normVals[::2] = frame.shape[1]
        return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

    def to_planar(arr: np.ndarray, shape: tuple) -> np.ndarray:
        return cv2.resize(arr, shape).transpose(2, 0, 1).flatten()

    def displayFrame(name, frame):
        for detection in detections:
            bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
            cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
        # Show the frame
        cv2.imshow(name, frame)

    cap = cv2.VideoCapture(videoPath)
    while cap.isOpened():
        read_correctly, frame = cap.read()
        if not read_correctly:
            break

        img = dai.ImgFrame()
        img.setData(to_planar(frame, (512, 320)))
        img.setTimestamp(monotonic())
        img.setWidth(512)
        img.setHeight(320)
        qIn.send(img)

        inDet = qDet.tryGet()

        if inDet is not None:
            detections = inDet.detections

        if frame is not None:
            displayFrame("rgb", frame)

        if cv2.waitKey(1) == ord('q'):
            break