#!/usr/bin/python3
# Code adapted from Tensorflow Object Detection Framework
# https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
# Tensorflow Object Detection Detector

import numpy as np
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
#import tensorflow as tf
import cv2
import time
import glob
import os
import sys
import csv
import sys

#os.environ["CUDA_VISIBLE_DEVICES"]="-1"#Setting the script to run on GPU:3
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

#Faster RCNN detectorAPI
class DetectorAPI:
    def __init__(self, path_to_ckpt):
        self.path_to_ckpt = path_to_ckpt

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            #od_graph_def = tf.compat.v1.GraphDef()
            #with tf.compat.v2.io.gfile.GFile(self.path_to_ckpt, 'rb') as fid:
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.path_to_ckpt, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

    def processFrame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()
        im_height, im_width,_ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0,i,0] * im_height),
                        int(boxes[0,i,1]*im_width),
                        int(boxes[0,i,2] * im_height),
                        int(boxes[0,i,3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def close(self):
        self.sess.close()
        self.default_graph.close()

#function to split the image stram into regions of interest
def camera_related_cropping(camera):
    if(camera) == 'driver':
        w1 = 0
        w2 = 540
        w3 = 60
        w4 = 860
        return w1,w2,w3,w4

    elif(camera) == 'F-door':
        w1 = 540
        w2 = 1080
        w3 = 60
        w4 = 860
        return w1,w2,w3,w4

    elif(camera) == 'F-rear':
        w1 = 0
        w2 = 540
        w3 = 1020
        w4 = 1840
        return w1,w2,w3,w4

    elif(camera) == 'R-door':
        w1 = 540
        w2 = 1080
        w3 = 1020
        w4 = 1840
        return w1,w2,w3,w4

#function to read input stream images and crop it into regions of interest
def video_crop(video_path,i,cameras):
    numImages = 0
    nRows = 3
    count=0
    mCols = 3
    cropped_images = []
    for camera in cameras:
        img = cv2.imread(video_path + '%d.jpg'%count)
        w1,w2,w3,w4  = camera_related_cropping(camera)
        sizeX = img.shape[1]
        sizeY = img.shape[0]
        roi = img[w1:w2,w3:w4]
        #cv2.imwrite(video_path + "cropped_%d.jpg" %count, roi)
        cropped_images.append(roi)
        count+=1

    return cropped_images


if __name__ == "__main__":
    model_path = '/usr/src/app/faster_rcnn_inception/frozen_inference_graph.pb'
    videos = ["video1","video2","video3"]#,"video2","video3"]
    cameras = ['driver','F-door','F-rear','R-door'] #all the camera images
    model_type = ['inception']#,'nas','mobilenet']
    path = '/usr/src/app/'
    output_path = path + "output" +"/"
    os.makedirs(output_path, exist_ok=True)
    odapi = DetectorAPI(path_to_ckpt=model_path)#Fater RCNN DetectorAPI
    for video in videos:
        # TODO: This part will be handled by the customer. e.g. Customer_run.py
        video_path = path + "input" + "/" + video + '/'
        print(video_path)
        results = output_path + video + '/'
        os.makedirs(results, exist_ok=True)
        numFiles = len(glob.glob1(video_path,'*.jpg'))
        for i in range(0,numFiles): #images taken at 2FPS
            cropped_images = video_crop(video_path,i,cameras) #crop input image
            for n in range(len(cameras)):
                print("-------Image from Camera %d---------"%(n+1))
                threshold = 0.2#threshold for the person class.
                fields = ['step',
                        'detection_result',
                        'time']
                # TODO: everything below goes into app.py in run_app function. See stress-ng/app.py run_app
                img = cv2.imread(video_path + 'cropped_%d.jpg'%n)
                time1 = time.time()
                boxes, scores, classes, num = odapi.processFrame(cropped_images[n]) #passing image to the detector
                time2 = time.time() - time1
                people_count=0
                for j in range(len(boxes)):
                    # Class 1 represents human
                    if classes[j] == 1 and scores[j] > threshold:
                        people_count+=1
                        box = boxes[j]
                #time2 = time.time() - time1
                print("Frame_number:%d,Number of Persons:%d"%(i,people_count))
                print("Prediction & Counting Time:%f seconds"%time2)
                dict = [{'step':i, 'detection_result':people_count, 'time':time2}]
                file_exists = os.path.isfile(results + 'Camera%d.csv'%(n))
                with open(results + 'Camera%d.csv'%(n), 'a') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames = fields)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerows(dict)
                #TODO: return result
