FROM python:3.8.5
RUN apt-get update
RUN python3 -m pip install --no-cache-dir --upgrade pip

COPY Demo/service-examples/Carta-People-Counting/frame_sink/faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb /demo/app/faster_rcnn_inception/

COPY Demo/service-examples/Carta-People-Counting/common/requirements.txt /demo/app/
RUN python3 -m pip install --no-cache-dir -r /demo/app/requirements.txt

#COPY setup.* /MV2/
#RUN python3 -m pip install -e /MV2
#COPY MV2 /MV2/MV2

WORKDIR /demo/app
#COPY Carta-People-Counting/frames /demo/app/frames


COPY Demo/run/cfg.py /demo/app/
COPY Demo/run/influx_cfg.py /demo/app/
COPY Demo/service-examples/Carta-People-Counting/common/ /demo/app/
COPY Demo/service-examples/Carta-People-Counting/frame_sink/app-shim.py /demo/app/

ENTRYPOINT ["python", "/demo/app/app-shim.py"]
#CMD ["python", "/demo/app/app-shim.py", "pulsar://172.21.20.70:6650", "public", "default", "supplier_1", "allocation_1"]
#CMD ["/bin/sh"]