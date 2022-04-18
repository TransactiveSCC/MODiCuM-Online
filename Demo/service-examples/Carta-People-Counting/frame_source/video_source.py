import cv2
import numpy as np
import os
import pulsar
import time

class InputDataSchema(pulsar.schema.Record):
    allocation_uuid = pulsar.schema.String()
    value = pulsar.schema.Bytes()
    timestamp = pulsar.schema.Float()
    msgnum = pulsar.schema.Integer()
    input_uuid = pulsar.schema.String()

frame_loc = "/home/riaps/projects/TransactiveSCC/4_MV2/Demo/service-examples/Carta-People-Counting/frames/video1_0000.jpg"


client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer(
    topic='fubar',
    schema=pulsar.schema.AvroSchema(InputDataSchema))

img = cv2.imread(frame_loc)
# '.jpg'means that the img of the current picture is encoded in jpg format, and the result of encoding in different formats is different.
img_encode = cv2.imencode('.jpg', img)[1]
# print(type(img_encode))

# img_encode2 = np.array(img_encode1)
# print(type(img_encode2))
# print(img_encode1 == img_encode2)
img_bytes = img_encode.tobytes()

msg = InputDataSchema(
    allocation_uuid="alloc1",
    value=img_bytes,
    timestamp=time.time(),
    msgnum=1,
    input_uuid="1"
)

producer.send(msg)

# image = np.asarray(bytearray(img_bytes), dtype="uint8")
# image = cv2.imdecode(image, cv2.IMREAD_COLOR)
# cv2.imshow('URL2Image', image)
# cv2.waitKey()

# str_encode = data_encode.tostring()
#
# # Cached data is saved locally
# with open('img_encode.txt', 'w') as f:
#     f.write(str_encode)
#     f.flush

# for frame_num, file in enumerate(os.listdir(frame_loc)):
#
#     # file_name = str.encode(file)
#     with open(frame_loc+file, 'rb') as imageFile:
#         frame = bytes(bytearray(imageFile.read()))
#         # print(frame)
#         # print(type(frame))
#         properties = {"content-type": "application/jpg", "frame_num": str(frame_num)}
#         timestamp = int(round(time.time() * 1000))
#         print(f"time is: {timestamp} and of type {type(timestamp)}")
#         producer.send(frame, properties, event_timestamp=int(time.time()))
#         # print(frame_num)
#         if frame_num == 3:
#             break
