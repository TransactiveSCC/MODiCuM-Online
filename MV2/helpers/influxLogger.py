import datetime
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
import urllib3
import time


class InfluxLogger:
    def __init__(self, cfg):
        # log_msg = {"measurement": "State",
        #            "time": datetime.datetime.utcfromtimestamp(time.time()).isoformat() + 'Z',
        #            "fields": {"state": self.cfg.State.allocate},
        #            "tags": {"allocation_uuid": allocation_uuid, "user_uuid": alloc_msg.customer_uuid}}

        self.cfg = cfg

        self.influx_client = influxdb_client.InfluxDBClient(
            url=cfg.url,
            token=cfg.token,
            org=cfg.org,
            retries=3,
            debug=False
            )

        self.write_client = self.influx_client.write_api(write_options=SYNCHRONOUS)
        self.query_client = self.influx_client.query_api()

    def write(self, influx_dict):
        influx_dict["measurement"] = "Events"
        influx_dict["time"] = datetime.datetime.utcfromtimestamp(time.time()).isoformat() + 'Z'
        try:
            self.write_client.write(self.cfg.bucket, self.cfg.org, [influx_dict])
        except influxdb_client.rest.ApiException as e:
            print(f" \033[91m Failed to write: {e} \033[00m")
        except urllib3.exceptions.ReadTimeoutError as e:
            print(f"Read timeout error I guess: {e}")




