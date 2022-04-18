# Standalone Demo

## Docker
1. add to .bashrc 
```
export DOCKER_BUILDKIT=1 export COMPOSE_DOCKER_CLI_BUILD=1
```
### Dockerhub
1. Create [dockerhub](https://docs.docker.com/docker-hub/) account and set `self.registry` in `MV2/Demo/run/cfg.py` to the username.
2. Log into account from docker cli: `docker login -u <dockerhub username> --password-stdin`

### Create a docker network. Only have to do once. See command:
```bash
docker network create mv2-default
```

## Setup Application

Here we setup the people counting application, which is the demo app we use to test the system. Only need to setup once. 

1. Create a `videos` directory in `Demo/service-examples/Carta-preproc`
2. Use this [link](https://vanderbilt365-my.sharepoint.com/:f:/g/personal/scott_r_eisele_vanderbilt_edu/EprbHD6wS61Oon0eDujPAGMBHSttbQF58nxN_Vm105xBvA?e=TfA4u4) to get videos and put `video1.avi`, `video2.avi` and `video3.avi` in `Demo/service-examples/Carta-preproc/videos`.
3. go to `Demo/service-examples/Carta-preproc/docker-data` folder and run `python3 image_extraction.py`
4. download this [tar file](https://vanderbilt365-my.sharepoint.com/:u:/g/personal/scott_r_eisele_vanderbilt_edu/EZZ2FAsJHYhNrPmDhnQCEwwBFikBGiWpwJBHqZx5as1MCg?e=PBf2IB)
5. untar it and put it in `Demo/service-examples/Carta-People-Counting/frame_sink`, should look like this: `Demo/service-examples/Carta-People-Counting/frame_sink/faster_rcnn_inception_v2_coco_2018_01_28`

## Influx

1. Install influx locally. 
2. Start influx with `influxd`
3. Go to dashboard `http:localhost:8086`, make sure you have a username and password. Also create a bucket `modicumdb`. 
4. org?
5. Use the dashboard to create a token.

## Update configs and build
1. Update `REGISTRY` in `.env` with your dockerhub account ID
2. Update influx config `MV2/Demo/run/influx_cfg.py` under `influx=='local'` with the parameters from the Influx step.
3. In the general config file `MV2/Demo/run/cfg.py`, ensure that `standalone=True`, `self.ip` matches your local machine, and increment `VERSION`. 
4. Build frame sink: `cd Demo/service-examples/Carta-People-Counting/frame_sink`, `docker-compose build`.
5. Build frame source: `cd Demo/service-examples/Carta-People-Counting/frame_source`, `docker-compose build`.
6. Build platform: `cd MV2/Demo`, `MV2/Demo$ docker-compose.yml build`

## Run

### Pulsar
You can start pulsar locally with our docker-compose file in MV2/demo/pulsar. Pulsar needs to be running for demo to work. To run from our docker image: 
1. `cd MV2/Demo/pulsar`
2. `MV2/Demo/pulsar$ docker-compose up`

### Demo
Run the demo:
1. `cd MV2/Demo/Demo`
2. `MV2/Demo/pulsar$ docker-compose up`

## Other Notes

### Cleanup
Delete influx data
```
influx delete --org "modicum" --bucket "modicumdb" --start 1970-01-01T00:00:00Z --stop 2022-01-01T00:00:00Z --predicate '_measurement="State"'
```