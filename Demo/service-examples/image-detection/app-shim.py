import argparse
import datetime
import hashlib
import multiprocessing
import pulsar
import sys
import time

import app_schema as schema
import app as app


class MV2AppShim:
    def __init__(self, pulsar_url, tenant, namespace, user_uuid, allocation_uuid):

        self.finish_event = multiprocessing.Event()

        self.pulsar_client = pulsar.Client(pulsar_url)

        self.cleanup_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{tenant}/{namespace}/cleanup_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.CleanupDataSchema),
            subscription_name=f"{user_uuid}-app-cleanup_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.cleanup)

        self.output_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{tenant}/{namespace}/output_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.OutputDataSchema)
        )

        self.input_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{tenant}/{namespace}/input_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema.InputDataSchema),
            subscription_name=f"{user_uuid}-input_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.process)

        self.user_uuid = user_uuid

    def process(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)

        print(f"app-shim.py - process: received input\n")
        sys.stdout.flush()

        customer_timestamp = msg.value().timestamp
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        output = app.run_app(msg.value())

        output_msg = schema.OutputDataSchema(
            allocation_uuid=msg.value().allocation_uuid,
            value=output,
            customertimestamp=customer_timestamp,
            suppliertimestamp=now.timestamp(),
            input_uuid=msg.value().input_uuid,
            timestamp=now.timestamp()
        )

        print(f"\n app-shim.py - process: {self.user_uuid}; {msg.value()}\n")
        sys.stdout.flush()
        self.output_producer.send(output_msg)

    def cleanup(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        self.finish_event.set()


if __name__ == '__main__':
    print("Hello World")

    parser = argparse.ArgumentParser()
    parser.add_argument("pulsar_url")
    parser.add_argument("tenant")
    parser.add_argument("namespace")
    parser.add_argument("user_uuid")
    parser.add_argument("allocation_uuid")
    args = parser.parse_args()

    print(args)
    sys.stdout.flush()

    shim = MV2AppShim(args.pulsar_url, args.tenant, args.namespace,
                      args.user_uuid, args.allocation_uuid)

    print("app is Waiting")
    sys.stdout.flush()
    shim.finish_event.wait()
    print("app is done Waiting")
    sys.stdout.flush()
    time.sleep(5)
