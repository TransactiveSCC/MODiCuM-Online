import datetime
import hashlib
import os
import pulsar
import pprint
import sys
from termcolor import cprint
import uuid

from MV2.helpers import DockerWrapper
import MV2.schema
from MV2.trader import Trader
import MV2.helpers.dummyApp as dummyApp


class Supplier(Trader):

    def fulfillment(self, allocation_uuid, finish_fulfillment):
        """Receive and process Job"""

        self.dockerClient = DockerWrapper.get_docker_client()

        self.hashed_outputs = {}
        self.msgnum = 0
        self.ready = False

        super(Supplier, self).fulfillment(allocation_uuid, finish_fulfillment)

        self.output_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/output_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.OutputDataSchema),
            subscription_name=f"{self.cfg.user_uuid}-output_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.hash_output)

        self.supplier_commit_producer = self.market_producer("supplier_commit", MV2.schema.SupplierCommitSchema)

        self.checklist_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/checklist_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.Checklist),
            subscription_name=f"{self.cfg.user_uuid}-checklist_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.checklist)


        app_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/app_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.AppSchema),
            subscription_name=f"{self.cfg.user_uuid}-app_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.setup)
        # Switched initial_position to Earliest because sometimes messages would be sent before supplier was ready.


        print(f"\napp_consumer.topic: {app_consumer.topic()}; pid:{os.getpid()}\n")

        print("Supplier is Waiting")
        sys.stdout.flush()
        self.finish_fulfillment.wait()
        print("Supplier is done Waiting")
        sys.stdout.flush()

    def hash_output(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)

        output = msg.value().value
        input_uuid = msg.value().input_uuid
        output_uuid = f"{input_uuid}_{output}"

        hash_input_uuid = hashlib.sha256(str(input_uuid).encode("utf-8")).hexdigest()

        self.hashed_outputs[hash_input_uuid] = {"output": output,
                                                "msgnum": msg.value().msgnum,
                                                "input_uuid": input_uuid,
                                                "output_uuid": output_uuid,
                                                "input_MessageId": msg.value().input_msgID,
                                                "output_MessageId": msg.message_id().serialize()}

    def setup(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        allocation_uuid = msg.value().allocation_uuid
        allocation = self.allocations[allocation_uuid]
        allocation_msg = self.allocations[allocation_uuid]["alloc_msg"]

        cprint(f"SUPPLIER.py - setup\n"
               f"alloc_msg: {allocation_msg}", "magenta")
        sys.stdout.flush()

        pulsar_url = self.cfg.pulsar_url
        tenant = allocation_msg.customer_uuid
        namespace = self.cfg.market_uuid
        user_uuid = self.cfg.user_uuid

        service_uuid = allocation_msg.service_uuid
        tag = f"{self.cfg.registry}/{service_uuid}"  # the registry location of the image
        name = f"{user_uuid}_{service_uuid}_{uuid.uuid4().hex}"  # Add uuid4 to avoid potential collisions of docker containers.
        strategy = self.cfg.strategy
        behavior = strategy["behavior"]
        Ps = strategy["P(s)"]

        command = f"{pulsar_url} {tenant} {namespace} {user_uuid} {allocation_uuid} {behavior} {Ps}"
        xdict = {
            "command": command,
            "mounts": {},
            "env": {},
            "network": ""
        }

        container = DockerWrapper.run_container(client=self.dockerClient, tag=tag, name=name, xdict=xdict)

        # ------------------------------------------------------------------
        # state tracking
        # ------------------------------------------------------------------
        if self.cfg.influx_logging:
            for offer_uuid in allocation["my_offers"]:
                log_msg = {"fields": {"state": self.cfg.State.running.value,
                                      "sender": self.cfg.user_uuid,
                                      "allocation": allocation_uuid},
                            "tags": {"uuid": offer_uuid}}
                self.influx_logger.write(log_msg)
        #------------------------------------------------------------------

        for log_bytes in container.logs(stream=True):
            log = log_bytes.decode("utf-8")
            if "error" in log:
                error_msg = log
                print(f"error_msg: {error_msg}")
            print(log)
            sys.stdout.flush()

        # DockerWrapper.monitor(docker_client=self.dockerClient, container=container)
        exit_code = container.wait()
        print(f"supplier.py - setup: app exit code: {exit_code}")
        #TODO: Send this message on a topic to someone. This is particularly relevant if the container fails to run,
        #TODO: resulting in no input/output topics and thus no way to clean up.
        sys.stdout.flush()

    def cleanup(self, consumer, msg):
        super(Supplier, self).cleanup(consumer, msg)

    def checklist(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        allocation_uuid = msg.value().allocation_uuid
        user_uuid = self.cfg.user_uuid

        cprint(f"{self.cfg.user_uuid} receive checklist", "magenta")
        sys.stdout.flush()

        output_checklist = []
        input_MessageId_list = []
        print(f"length of self.hashed_outputs: {len(self.hashed_outputs)}")
        pprint.pprint(self.hashed_outputs)
        for hashed_output in msg.value().checklist:
            if hashed_output in self.hashed_outputs:
                output_checklist.append(self.hashed_outputs[hashed_output]["output_uuid"])
                input_MessageId_list.append(self.hashed_outputs[hashed_output]["input_MessageId"])

        hashed_output_checklist = hashlib.sha256(str(output_checklist).encode("utf-8")).hexdigest()

        print(f"supplier.py - checklist - {self.cfg.user_uuid}; \n"
              f"received hashed checklist: {msg.value().checklist}\n"
              f"output_checklist:{output_checklist}; \n"
              f"hashed_output_checklist: {hashed_output_checklist};\n"
              f"input_MessageId_list: {input_MessageId_list}")

        offer_uuid = self.allocations[allocation_uuid]["my_offers"][0] # TODO:  if multiple offers are in 1 allocation this will need work
        self.ledger_client.postOutput(allocation_uuid, offer_uuid, hashed_output_checklist, input_MessageId_list)


        self.finish_fulfillment.set()
        #TODO: Add clearmarket message and listener and trigger off of that?
        #TODO: Maybe not... this is the end of the actual work...

    def sign(self, allocation_uuid):
        cprint(f"{self.cfg.user_uuid} Signing", "magenta")
        # TODO: Commit to ledger
        # TODO: Sign on ledger
        offer_uuid = self.allocations[allocation_uuid]["my_offers"][0] # TODO:  if multiple offers are in 1 allocation this will need work
        self.ledger_client.supplierSign(allocation_uuid, offer_uuid)
        sys.stdout.flush()








