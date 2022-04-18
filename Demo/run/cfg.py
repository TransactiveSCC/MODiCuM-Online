from enum import Enum, auto
import influx_cfg

class Cfg:
    def __init__(self, standalone=False):
        if standalone:
            self.ip = "172.21.20.70"
            self.port = "8080"
            self.clusters = ["standalone"]
            self.registry = "eiselesr"
            # self.registry = "mpwilbur"
        else:
            self.ip = "34.139.254.218"
            self.port = "80"
            self.clusters = ["pulsar"]
            self.registry = "us-central1-docker.pkg.dev/nomadic-line-311316/modicum-repo"
            # self.registry = "us-central1-docker.pkg.dev/ascendant-choir-331619/modicum-repo"

        self.pulsar_url = f"pulsar://{self.ip}:6650"
        self.pulsar_admin_url = f"http://{self.ip}:{self.port}/admin/v2"
        self.function_api = f"http://{self.ip}:{self.port}/admin/v3/functions"
        self.presto_host = f"{self.ip}"
        self.presto_port = 8081

    tenant = "public"
    namespace = "default"
    logger_topic = "logger"
    deposit = 1000

    # MARKET CONFIG
    VERSION = 10
    market_uuid = f"market_{VERSION}"
    # TODO: pass this in with the docker-compose. I shouldn't have to rebuild to update this. 
    # Also, the config should be passed from the main docker containers to the siblings. Those
    # containers should not import the config files. 

    # USER CONFIG
    user_uuid = "customer_1"
    mediators = ["mediator1"]

    # INFLUX CONFIG - see influx_cfg.py
    influx_logging = True
    bucket = influx_cfg.bucket
    org = influx_cfg.org
    token = influx_cfg.token
    url = influx_cfg.url

    # State
    class State(Enum):

        post_offer = 1
        pool = 2
        allocated = 3
        accepted = 4
        # starting = auto()
        running = 5
        cleanup = 6
        # checklist = auto()
        # receivechecklist = auto()
        # postOutput = auto()
        OutputPosted = 7
        MediationRequested = 8
        MediationRunning = 9
        MediationCompleted = 10
        # clearMarket = auto()
        Closed = 11


    def print_msg(self, consumer, msg):
        print(f"subscription_name:{consumer.subscription_name()}")
        # print(f"topic:{consumer.topic()}")
        # print(f"data:{msg.data()}")
        # print(f"event_timestamp:{msg.event_timestamp()}")
        print(f"message_id:{msg.message_id()}")
        # print(f"partition_key:{msg.partition_key()}")
        # print(f"properties:{msg.properties()}")
        # print(f"redelivery_count:{msg.redelivery_count()}")
        print(f"topic_name:{msg.topic_name()}")
        print(f"value:{msg.value()}\n")

    def print_msgvalue(self, msg):
        print("NEW MESSAGE")
        # print(f"subscription_name:{consumer.subscription_name()}")
        # print(f"topic:{consumer.topic()}")
        # print(f"data:{msg.data()}")
        # print(f"event_timestamp:{msg.event_timestamp()}")
        # print(f"message_id:{msg.message_id()}")
        # print(f"partition_key:{msg.partition_key()}")
        # print(f"properties:{msg.properties()}")
        # print(f"redelivery_count:{msg.redelivery_count()}")
        # print(f"topic_name:{msg.topic_name()}")
        print(f"value:{msg}\n")


if __name__ == '__main__':
    cfg0 = Cfg()
    # print(cfg0.demo_config.customer_behavior)
    print(influx)

