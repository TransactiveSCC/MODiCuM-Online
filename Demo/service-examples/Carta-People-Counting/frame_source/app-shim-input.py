import argparse
import datetime
import hashlib
import multiprocessing
import pulsar
import sys
import time
import uuid

import demo_cfg as cfg
import app_cfg
import app_schema as schema
import app as app

import MV2.helpers.PulsarREST as PulsarRest


class MV2AppShim:
    def __init__(self, pulsar_url, tenant, namespace, user_uuid, allocation_uuid, start, end, rate):
        self.start = start
        self.end = end
        self.rate = rate
        self.num_inputs = int((end-start)*rate)
        print(f"MV2APPShim - Need to send {self.end}-{self.start}*{rate}={self.num_inputs} inputs")
        self.inputs_sent = 0
        self.finish_event = multiprocessing.Event()
        self.cfg = cfg.Cfg()
        self.pulsar_client = pulsar.Client(pulsar_url)

        PulsarRest.get_namespaces(self.cfg.pulsar_admin_url, tenant)

        self.cleanup_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{tenant}/{namespace}/cleanup_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.CleanupDataSchema),
            subscription_name=f"{user_uuid}-app-cleanup_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.cleanup)

        self.input_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{tenant}/{namespace}/input_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.InputDataSchema)
        )

        self.user_uuid = user_uuid

    def process(self, allocation_uuid):

        print(f"app-shim.py - process: send inputs")
        sys.stdout.flush()
        app_i = app.APP_INPUT(app_cfg)

        # while not self.finish_event.wait(timeout=1):
        while True: # TODO: HACK
            # timeout controls delay between sends
            now = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

            app_input, last = app_i.get_input()
            
            sent_min = self.inputs_sent >= len(self.cfg.check_list)
            #  TODO: sent_enough is a hack to make sure all test inputs were sent.
            # In reality we need to properly handle the case when the supplier didn't
            # get all the inputs.
            sent_enough = self.inputs_sent >= self.num_inputs

            # if last or (now > self.end and sent_enough):
            if last or sent_enough:
                input_uuid = self.cfg.last_input
                # TODO: Fix this. Currently it makes all outputs after num_inputs have this hash
            else:
                input_uuid = hashlib.sha256(app_input).hexdigest()

            input_msg = schema.InputDataSchema(
                allocation_uuid=allocation_uuid,
                value=app_input,
                timestamp=now,
                msgnum=self.inputs_sent,
                input_uuid=input_uuid
            )
            print(f"app-shim-input.py - process: {self.user_uuid}; {allocation_uuid, input_uuid}")
            print(f"app-shim-input.py: allocation:{allocation_uuid} inputs_sent:{self.inputs_sent}")
            sys.stdout.flush()
            self.input_producer.send(input_msg)
            if last or sent_enough:
                print(f"app-shim-input.py: reached break on allocation:{allocation_uuid}")
                break
                # TODO: bit of a hack. Should stop because of cleanup message.
            self.inputs_sent += 1
            time.sleep(1) # TODO: HACK
        print(f"app-shim.py - process: done sending inputs")

    def cleanup(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        print(f"app-shim-input.py - cleanup: {msg.value()}")
        self.finish_event.set()


if __name__ == '__main__':
    print("Starting app-shim-input: Hello World")
    print(f"app-shim-input: raw input - {str(sys.argv)}")

    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_url")
    parser.add_argument("tenant")
    parser.add_argument("namespace")
    parser.add_argument("user_uuid")
    parser.add_argument("allocation_uuid")
    parser.add_argument("start", type=float)
    parser.add_argument("end", type=float)
    parser.add_argument("rate", type=float)
    args = parser.parse_args()

    print(args)
    sys.stdout.flush()

    shim = MV2AppShim(args.pulsar_url, args.tenant, args.namespace,
                      args.user_uuid, args.allocation_uuid,
                      args.start, args.end, args.rate)

    shim.process(allocation_uuid=args.allocation_uuid)
    print("app is Waiting")
    sys.stdout.flush()
    shim.finish_event.wait()
    print("app is done Waiting")
    sys.stdout.flush()
    time.sleep(5)
