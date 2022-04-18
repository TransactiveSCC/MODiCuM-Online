FROM python:3.8.5

ENV DOCKERVERSION=20.10.7
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
  && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKERVERSION}.tgz

RUN apt-get update
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install docker tqdm
COPY setup.* /MV2/
RUN python3 -m pip install -e /MV2
COPY MV2 /MV2/MV2
#RUN cat /MV2/MV2/secrets/nomadic-line-311316-38555d81df7b.json | docker login -u _json_key --password-stdin https://us-central1-docker.pkg.dev
# How do you get this install to work without the -e? I just get a "ModuleNotFoundError: No module named 'MV2'"
COPY Demo/run/mediator_run.py /demo/
COPY Demo/run/cfg.py /demo/
COPY Demo/run/influx_cfg.py /demo/

RUN cat /MV2/MV2/secrets/ascendant-choir-331619-079cb90db7d5.json | docker login -u _json_key --password-stdin https://us-central1-docker.pkg.dev

CMD ["python", "/demo/mediator_run.py"]
#CMD ["/bin/sh"]