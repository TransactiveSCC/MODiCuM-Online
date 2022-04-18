#!/usr/bin/python3
import cv2
import os

# Extract images from videos at 30 FPS
def extract_video_images(video_path, store_path, video):
    count = 0
    x = 0
    vidcap = cv2.VideoCapture(video_path)
    video_length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    print("Number of frames: ", video_length)
    success, image = vidcap.read()
    success = True
    while success:
        # vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*1000))
        success, image = vidcap.read()
        if count % 30 == 0:
            # cv2.imwrite(store_path + "%d.jpg" % x, image)  # save frame as JPEG file
            cv2.imwrite(f"{store_path}/{video}_{str(x).zfill(4)}.jpg", image)  # save frame as JPEG file
            x += 1
        # print('Read a new frame: ', success)
        count += 1


if __name__ == '__main__':
    #path = "/home/riaps/projects/TransactiveSCC/4_MV2/Demo/service-examples/Carta-People-Counting"
    path = "/Volumes/external_drive/Code/MV2/Demo/service-examples/Carta-preproc"
    store_path = f"{path}/frames"
    videos = ["video1", "video2", "video3"]
    os.makedirs(store_path, exist_ok=True)
    for video in videos:
        video_path = f"{path}/videos/{video}.avi"
        image_store_path = f"{store_path}"
        os.makedirs(image_store_path, exist_ok=True)
        extract_video_images(video_path, image_store_path, video)
