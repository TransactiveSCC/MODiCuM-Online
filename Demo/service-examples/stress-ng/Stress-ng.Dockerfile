FROM python:3.8.5
RUN apt-get update && apt-get install -y stress-ng

COPY service-examples/stress-ng/requirements.txt ./

RUN python3 -m pip install --no-cache-dir --upgrade pip && python3 -m pip install --no-cache-dir -r requirements.txt

COPY service-examples/stress-ng/ /demo/app/

COPY run/cfg.py /demo/app/
COPY run/influx_cfg.py /demo/app/

#CMD ["python", "/demo/app/app-shim.py"]
ENTRYPOINT ["python", "/demo/app/app-shim.py"]
#ENTRYPOINT ["python", "/demo/app/app-shim.py", "pulsar://172.21.20.70:6650", "customer_1", "market_11", "supplier_1", "allocation_1", "honest", "1"]
#CMD ["/bin/sh"]