import cv2 as cv
import argparse
import sys
import numpy as np
import os.path

# Initialize the parameters
confThreshold = 0.3  #Confidence threshold
nmsThreshold = 0.4   #Non-maximum suppression threshold 0.4
inpWidth = 412       #Width of network's input image
inpHeight = 412      #Height of network's input image
showBG = False      # show / Noit show image background
bgColor = 100       # Blackground image color
Drawframe = ""      # Frame to be draw


rtspStream = 'rtsp://192.168.1.3:554/user=admin&password=&channel=1&stream=0.sdp?real_stream'
    
# Load names of classes
classesFile = "coco.names";
classes = None
with open(classesFile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

modelConfiguration = "yolov3-tiny.cfg";
modelWeights = "yolov3-tiny.weights";


net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)


# Get the names of the output layers
def getOutputsNames(net):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers, i.e. the layers with unconnected outputs
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Draw the predicted bounding box
def drawPred(classId, conf, left, top, right, bottom):
    global Drawframe
    Drawframe = frame

    if showBG==False:
        global bgColor
        # Create black color image
        height,width,depth = frame.shape
        blackFrame = np.zeros([height,width,3],dtype=np.uint8) 
        blackFrame.fill(bgColor)
        Drawframe = blackFrame

    # Draw a bounding box.
    cv.rectangle(Drawframe, (left, top), (right, bottom), (255, 178, 50), 3)
    
    label = '%.2f' % conf
        
    # Get the label for the class name and its confidence
    if classes:
        assert(classId < len(classes))
        label = '%s : %s' % (classes[classId], label)

    #Display the label at the top of the bounding box
    labelSize, baseLine = cv.getTextSize(label, cv.FONT_HERSHEY_TRIPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    #Text Blackground
    cv.rectangle(Drawframe, (left, top - round(1.8*labelSize[1])), (left + round(1.8*labelSize[0]), top + baseLine), (0, 0, 0), cv.FILLED)
    cv.putText(Drawframe, label, (left, top), cv.FONT_HERSHEY_TRIPLEX, 0.9, (0,255,0), 2)

# Remove the bounding boxes with low confidence using non-maxima suppression
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    classIds = []
    confidences = []
    boxes = []
    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(classIds[i], confidences[i], left, top, left + width, top + height)




# Process inputs
winName = 'Fall Detection'
cv.namedWindow(winName, cv.WINDOW_NORMAL)



##Camera
cap = cv.VideoCapture(rtspStream)


# Get the video writer initialized to save the output video

#vid_writer = cv.VideoWriter(outputFile, cv.VideoWriter_fourcc('M','J','P','G'), 30, (round(cap.get(cv.CAP_PROP_FRAME_WIDTH)),round(cap.get(cv.CAP_PROP_FRAME_HEIGHT))))

from matplotlib import pyplot as plt

while cv.waitKey(1) < 0:
    
    # get frame from the video
    hasFrame, frame = cap.read()
    
    # Stop the program if reached end of video
    if not hasFrame:
        print("Done processing !!!")
       # print("Output file is stored as ", outputFile)
        cv.waitKey(3000)
        break

    # Create a 4D blob from a frame.
    blob = cv.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0,0,0], 1, crop=False)

    # Sets the input to the network
    net.setInput(blob)

    # Runs the forward pass to get output of the output layers
    outs = net.forward(getOutputsNames(net))

    
    # Remove the bounding boxes with low confidence
    postprocess(frame, outs)

    # Put efficiency information. The function getPerfProfile returns the overall time for inference(t) and the timings for each of the layers(in layersTimes)
    t, _ = net.getPerfProfile()
    
    # Show Frame rate at the top lef video
    label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
    #label = cv.

    cv.putText(frame, label, (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0))

    #vid_writer.write(frame.astype(np.uint8))

    cv.imshow(winName, Drawframe)

