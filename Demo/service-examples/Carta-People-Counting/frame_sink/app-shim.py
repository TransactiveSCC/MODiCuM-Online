import argparse
import datetime
import hashlib
import multiprocessing
import pulsar
import random
import sys
import time

import app as app
import app_cfg
import app_schema as schema

class MV2AppShim:
    def __init__(self, pulsar_url, tenant, namespace, user_uuid, allocation_uuid, strategy):

        random.seed(0)
        self.output_checklist = []
        self.input_MessageId_list = []
        self.user_uuid = user_uuid
        self.app = app.APP(app_cfg)

        self.finish_event = multiprocessing.Event()

        self.pulsar_client = pulsar.Client(pulsar_url)

        # TODO: This is basically a patch to create new topics for the mediator.
        #  It could be designed better. 
        if "mediator" in self.user_uuid:
            phase = "mediation_"
        else:
            phase = ""


        self.cleanup_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{tenant}/{namespace}/{phase}cleanup_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.CleanupDataSchema),
            subscription_name=f"{user_uuid}-app-cleanup_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.cleanup)

        output_topic = f"persistent://{tenant}/{namespace}/{phase}output_{allocation_uuid}"
        print(f"\033[91m producer output_topic {output_topic} \033[00m")

        self.output_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{tenant}/{namespace}/{phase}output_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.OutputDataSchema)
        )

        self.input_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{tenant}/{namespace}/{phase}input_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.InputDataSchema),
            subscription_name=f"{user_uuid}-input_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.process)

        self.strategy = strategy

    def process(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)

        print(f"app-shim.py - process: received input")
        sys.stdout.flush()

        customer_timestamp = msg.value().timestamp
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        # TODO-NOTE: NOTE FOR DEMO PURPOSES ONLY
        P_s = float(self.strategy["P(s)"])
        r = random.uniform(0, 1)
        if r <= P_s:
            output = self.app.run_app(msg.value())  # Honest
        else:
            output = 0  # "wrongNth"
            print(f"\033[91m WrongNth \033[00m")
            if self.strategy["behavior"] == "noNth":
                return
        # TODO: When not running the demo use output = app.run_app(msg.value())



        output_msg = schema.OutputDataSchema(
            allocation_uuid=msg.value().allocation_uuid,
            value=output,
            customertimestamp=customer_timestamp,
            suppliertimestamp=now.timestamp(),
            msgnum=msg.value().msgnum,
            input_uuid=msg.value().input_uuid,
            input_msgID = msg.message_id().serialize(),
            timestamp=now.timestamp()
        )

        print(f"\n app-shim.py - process: {self.user_uuid}\n")
        sys.stdout.flush()
        self.output_producer.send(output_msg)

    def cleanup(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        print(f"\033[91m app-shim.py - cleanup \033[00m")
        sys.stdout.flush()
        self.finish_event.set()


if __name__ == '__main__':
    print("Hello World")

    # P_s = 0.5
    # r_test = random.uniform(0, 1)
    # if r_test <= P_s:
    #     print("process input")
    # else:
    #     print("skip input")

    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_url")
    parser.add_argument("tenant")
    parser.add_argument("namespace")
    parser.add_argument("user_uuid")
    parser.add_argument("allocation_uuid")
    parser.add_argument("behavior")
    parser.add_argument("Ps", type=float)
    args = parser.parse_args()

    print(args)
    sys.stdout.flush()

    strat = {"behavior": args.behavior,
             "P(s)": args.Ps}

    shim = MV2AppShim(args.pulsar_url, args.tenant, args.namespace,
                      args.user_uuid, args.allocation_uuid, strat)

    print("app is Waiting")
    sys.stdout.flush()
    shim.finish_event.wait()
    print("app is done Waiting")
    sys.stdout.flush()
    time.sleep(5)
