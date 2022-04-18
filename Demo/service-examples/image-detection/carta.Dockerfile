FROM python:3.8.5
#TODO: update to match docker2
RUN apt-get update && apt-get install -y
COPY service-examples/stress-ng/requirements.txt ./
RUN python3 -m pip install --no-cache-dir --upgrade pip && python3 -m pip install --no-cache-dir -r requirements.txt
COPY service-examples/stress-ng/ /demo/app/
COPY run/cfg.py /demo/app/
COPY run/influx_cfg.py /demo/app/



#CMD ["python", "/demo/app/app-shim.py"]
ENTRYPOINT ["python", "/demo/app/app-shim.py"]
# ENTRYPOINT ["python", "/demo/app/app-shim.py", "pulsar://172.21.20.53:6650", "customer_1", "market_98", "supplier_1", "allocation_1"]
#CMD ["/bin/sh"]