from subprocess import PIPE, run
import cv2
import numpy as np
import os
import sys
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import time


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

    def process_frame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()
        im_height, im_width, _ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0, i, 0] * im_height),
                             int(boxes[0, i, 1]*im_width),
                             int(boxes[0, i, 2] * im_height),
                             int(boxes[0, i, 3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def close(self):
        self.sess.close()
        self.default_graph.close()


class APP:
    def __init__(self, cfg):
        model_path = '/usr/src/app/faster_rcnn_inception/frozen_inference_graph.pb'
        videos = ["video1", "video2", "video3"]  # ,"video2","video3"]
        cameras = ['driver', 'F-door', 'F-rear', 'R-door'] # all the camera images
        model_type = ['inception']  # ,'nas','mobilenet']
        path = '/usr/src/app/'
        output_path = path + "output" +"/"
        os.makedirs(output_path, exist_ok=True)
        odapi = DetectorAPI(path_to_ckpt=model_path)#Fater RCNN DetectorAPI

        # video = "video1"
        # frame_loc = f"{path}input/{video}"
        self.frame_loc = cfg.inputs
        self.frame_num = 0
        self.files = os.listdir(self.frame_loc)

    def get_input(self):

        with open(self.frame_loc + self.files[self.frame_num], 'rb') as imageFile:
            img = cv2.imread(imageFile)
            img_encode = cv2.imencode('.jpg', img)[1]
            # TODO: Figure out encoding
            frame = bytes(bytearray(imageFile.read()))
            # print(frame)
            # print(type(frame))
            properties = {"content-type": "application/jpg", "frame_num": str(self.frame_num)}
            now = time.time()
            timestamp = int(round(now * 1000))
            print(f"time is: {timestamp} and of type {type(timestamp)}")
            self.frame_num += 1
            return frame  # , properties, int(now)


def run_app(self, input_msg):
    print(f"app.py - run_app: input_msg: {input_msg}")
    sys.stdout.flush()

    image_file_byte_array = bytearray(input_msg.value)
    img = 0  # Decode the image

    #TODO: run processFrame on image

    people_count = 1

    return people_count
