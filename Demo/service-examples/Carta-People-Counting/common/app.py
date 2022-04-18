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


# function to split the image stram into regions of interest
def camera_related_cropping(camera):
    if (camera) == 'driver':
        w1 = 0
        w2 = 540
        w3 = 60
        w4 = 860
        return w1, w2, w3, w4

    elif (camera) == 'F-door':
        w1 = 540
        w2 = 1080
        w3 = 60
        w4 = 860
        return w1, w2, w3, w4

    elif (camera) == 'F-rear':
        w1 = 0
        w2 = 540
        w3 = 1020
        w4 = 1840
        return w1, w2, w3, w4

    elif (camera) == 'R-door':
        w1 = 540
        w2 = 1080
        w3 = 1020
        w4 = 1840
        return w1, w2, w3, w4

# function to read input stream images and crop it into regions of interest
def video_crop(img, cameras):
    count = 0
    cropped_images = []
    for camera in cameras:
        w1, w2, w3, w4 = camera_related_cropping(camera)
        # sizeX = img.shape[1]
        # sizeY = img.shape[0]
        roi = img[w1:w2, w3:w4]
        cropped_images.append(roi)
        count += 1

    return cropped_images


def get_count(odapi, cropped_images, cameras):
    threshold = 0.2  # threshold for the person class.

    people_count = 0

    for i, camera in enumerate(cameras):
        time1 = time.time()
        boxes, scores, classes, num = odapi.process_frame(cropped_images[i])  # passing image to the detector

        count = 0
        for j in range(len(boxes)):
            # Class 1 represents human
            if classes[j] == 1 and scores[j] > threshold:
                count += 1
                box = boxes[j]
        time2 = time.time() - time1
        print(f"camera: {i} Number of Persons: {count}")
        # print("Prediction & Counting Time:%f seconds" % time2)
        people_count = people_count + count
    return people_count


class APP:
    def __init__(self, cfg):
        model_path = cfg.model
        # videos = ["video1", "video2", "video3"]  # ,"video2","video3"]
        self.cameras = ['driver', 'F-door', 'F-rear', 'R-door']  # all the camera images
        model_type = ['inception']  # ,'nas','mobilenet']
        output_path = cfg.outputs
        os.makedirs(output_path, exist_ok=True)
        self.odapi = DetectorAPI(path_to_ckpt=model_path) #Faster RCNN DetectorAPI

    def run_app(self, input_msg):
        print(f"app.py - run_app")
        sys.stdout.flush()

        image = np.asarray(bytearray(input_msg.value), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        cropped_images = video_crop(image, cameras=self.cameras)
        print(f"frame: {input_msg.msgnum} uuid: {input_msg.input_uuid}")
        people_count = get_count(self.odapi, cropped_images, self.cameras)
        print(f"People Count: {people_count}")

        return people_count


class APP_INPUT():
    def __init__(self, cfg):
        self.frame_loc = cfg.inputs
        self.frame_num = 0
        #self.files = sorted(os.listdir(self.frame_loc))
        self.files = []
        for file in sorted(os.listdir(self.frame_loc)):
            if file.endswith(".jpg"):
                self.files.append(file)
        self.num_files = len(self.files)

    def get_input(self):
        # /demo/app/frames/.DS_Store
        print(f"app.py - get_input: {self.frame_loc}/{self.files[self.frame_num]}")
        image_file = f"{self.frame_loc}/{self.files[self.frame_num]}"
        try:
            img = cv2.imread(image_file)
            img_encode = cv2.imencode('.jpg', img)[1]
            img_bytes = img_encode.tobytes()
            self.frame_num += 1
            if self.frame_num == self.num_files:
                return img_bytes, True
            else:
                return img_bytes, False  # , properties, int(now)
        except IndexError as err:
            print(f"IndexError: {err}. Probably no more images")
