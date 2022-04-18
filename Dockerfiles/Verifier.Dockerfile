FROM python:3.8.5
RUN apt-get update && apt-get install -y stress-ng
RUN python3 -m pip install --upgrade pip
COPY setup.* /MV2/
RUN python3 -m pip install -e /MV2
COPY MV2 /MV2/MV2
# How do you get this install to work without the -e? I just get a "ModuleNotFoundError: No module named 'MV2'"
COPY Demo/run/verifier_run.py /demo/
COPY Demo/run/cfg.py /demo/
COPY Demo/run/influx_cfg.py /demo/
CMD ["python", "/demo/verifier_run.py"]
#CMD ["/bin/sh"]