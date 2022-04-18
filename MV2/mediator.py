import datetime
import docker
import hashlib
import multiprocessing
import sys

import pulsar
from termcolor import cprint
import time
import uuid

import MV2.helpers.DockerWrapper as DockerWrapper
import MV2.helpers.ledger
import MV2.schema
from MV2.trader import Trader


class Mediator(Trader):
    def __init__(self, cfg, schema):

        self.output_checklist = {}
        self.app_inputs = {}
        
        super(Mediator, self).__init__(cfg, schema)

    def MediationRequested(self, msg):
        cprint(f"{self.cfg.user_uuid}; Mediation Request Received", "cyan")

        finish_event = multiprocessing.Event()
        mediation_process = multiprocessing.Process(target=self.Mediation,
                                                    args=(msg, finish_event))
        mediation_process.start()


    def Mediation(self, msg, finish_event):

        self.dockerClient = DockerWrapper.get_docker_client()
        self.finish_event = finish_event
        self.pulsar_client = pulsar.Client(self.cfg.pulsar_url)

        allocation_uuid = msg.value().allocation_uuid
        customer_uuid = msg.value().customer_uuid
        customer_hash = msg.value().customer_hash
        self.input_MessageId_list = msg.value().args_bytes

        output_topic = f"persistent://{customer_uuid}/{self.cfg.market_uuid}/mediation_output_{allocation_uuid}"
        print(f"\033[91m consumer output_topic {output_topic} \033[00m")

        self.output_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{customer_uuid}/{self.cfg.market_uuid}/mediation_output_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.OutputDataSchema),
            subscription_name=f"{self.cfg.user_uuid}-output_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.store_output)

        checklist_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{customer_uuid}/{self.cfg.market_uuid}/checklist_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.Checklist),
            subscription_name=f"{self.cfg.user_uuid}-checklist_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive)
        
        customer_checklist = checklist_consumer.receive()
        checklist_consumer.acknowledge(customer_checklist)
        self.customer_checklist = customer_checklist.value().checklist

        

        # if len(self.input_MessageId_list) < len(self.customer_checklist):
        #     pass
        #     # TODO: add this logic later to skip processing if not enough inputs are 
            #  specified by the supplier.
            # self.ledger_client.postMediation(allocation_uuid, hashed_output_checklist)


        # msg fields: allocation_uuid, ledger_id, user_uuid, customer_uuid, customer_hash,
        #             event, args_bytes(input_MessageId_list), timestamp
        cprint(f"msg.value(): {msg.value()}")

        cleanup_channel = f"mediation_cleanup_{allocation_uuid}"
        self.cleanup_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{customer_uuid}/{self.cfg.market_uuid}/{cleanup_channel}",
            schema=pulsar.schema.AvroSchema(MV2.schema.CleanupDataSchema)
        )
               
        input_channel = f"mediation_input_{allocation_uuid}"
        input_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{customer_uuid}/{self.cfg.market_uuid}/{input_channel}",
            schema=pulsar.schema.AvroSchema(MV2.schema.InputDataSchema)
        )

        """ This puts all inputs on the topic before the listener is contructed. 
            Should work fine though, because we are using Earliest. """
        print(f" \033[91m input_MessageId_list: {self.input_MessageId_list} \033[00m")
        for serial_msg_id in self.input_MessageId_list:
            msg_id = pulsar.MessageId.deserialize(serial_msg_id)
            reader = self.pulsar_client.create_reader(
                topic=f"persistent://{customer_uuid}/{self.cfg.market_uuid}/input_{allocation_uuid}",
                start_message_id=msg_id,
                schema=pulsar.schema.AvroSchema(MV2.schema.InputDataSchema)
            )

            input_msg = reader.read_next()
            time.sleep(.2)
            if allocation_uuid not in self.app_inputs:
                self.app_inputs[allocation_uuid] = []
            self.app_inputs[allocation_uuid].append(input_msg.value().value)
            print(f"\033[91m send image: {input_msg.value().input_uuid} \033[00m")
            sys.stdout.flush()
            input_producer.send(input_msg.value())

        self.setup(msg)

    def setup(self, msg):

        print(f"\033[91m setup docker container \033[00m")
        sys.stdout.flush()
        dockerClient = DockerWrapper.get_docker_client()
        allocation_uuid = msg.value().allocation_uuid
        pulsar_url = self.cfg.pulsar_url
        tenant = msg.value().customer_uuid
        namespace = self.cfg.market_uuid
        user_uuid = self.cfg.user_uuid
        behavior = "honest"  # Assume mediator will behave honestly
        Ps = 1

        

        command = f"{pulsar_url} {tenant} {namespace} {user_uuid} {allocation_uuid} {behavior} {Ps}"
        xdict = {
            "command": command,
            "mounts": {},
            "env": {},
            "network": ""
        }

        allocation_msg = self.allocations[allocation_uuid]["alloc_msg"]

        tag = f"{self.cfg.registry}/{allocation_msg.service_uuid}"
        name = f"{user_uuid}_{allocation_msg.service_uuid}_{uuid.uuid4().hex}"  # Add uuid4 to avoid potential collisions of docker containers.

        print(f"\033[91m start container \033[00m")
        container = DockerWrapper.run_container(client=dockerClient, tag=tag, name=name, xdict=xdict)

        
        # ------------------------------------------------------------------
        # state tracking
        # ------------------------------------------------------------------
        allocation = self.allocations[allocation_uuid]["alloc_msg"].allocation
        if self.cfg.influx_logging:

            for offer_uuid in allocation:
                log_msg = {"fields": {"state": self.cfg.State.MediationRunning.value,
                                      "sender": self.cfg.user_uuid,
                                      "allocation": allocation_uuid},
                           "tags": {"uuid": offer_uuid}}
                self.influx_logger.write(log_msg)
        #------------------------------------------------------------------

        try:
            print(f"\033[91m wait for container to finish \033[00m")
            sys.stdout.flush()
            for log_bytes in container.logs(stream=True):
                log = log_bytes.decode("utf-8")
                if "error" in log:
                    error_msg = log
                    print(f"error_msg: {error_msg}")
                print(f"log: {log}")
                sys.stdout.flush()

            exit_code = container.wait()
            print(f"mediator.py - setup: app exit code: {exit_code}")
        except docker.errors.NotFound as e:
            print(f"docker container not found... I guess?: {e}")

        print(f"output_checklist: {self.output_checklist[allocation_uuid]}")
        

        hash1 = hashlib.sha256(str(self.output_checklist[allocation_uuid]).encode("utf-8")).hexdigest()
        hashed_output_checklist = hashlib.sha256(hash1.encode("utf-8")).hexdigest()

        self.ledger_client.postMediation(allocation_uuid, hashed_output_checklist)
        sys.stdout.flush()

    def store_output(self, consumer, msg):
        print(f"\033[91m store_output  \033[00m")
        sys.stdout.flush()
        consumer.acknowledge_cumulative(msg)

        allocation_uuid = msg.value().allocation_uuid
        output = msg.value().value
        input_uuid = msg.value().input_uuid
        output_uuid = f"{input_uuid}_{output}"

        if allocation_uuid not in self.output_checklist:
            self.output_checklist[allocation_uuid] = []

        self.output_checklist[allocation_uuid].append(output_uuid)

        received = len(self.output_checklist[allocation_uuid])
        expected = len(self.input_MessageId_list)
        all_received = received >= expected

        print(f"\033[91m store_output: {self.output_checklist[allocation_uuid]} < {len(self.input_MessageId_list)}"
              f"{all_received} \033[00m")
        sys.stdout.flush()

        if all_received:
            print(f"\033[91m expected: {expected} received: {received} \033[00m ")
            print("recieved all, send cleanup")
            recv_timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            cleanup = MV2.schema.CleanupDataSchema(
                allocation_uuid=msg.value().allocation_uuid,
                cleanup=True,
                timestamp=recv_timestamp
            )
            self.cleanup_producer.send(cleanup)
        else:
            print(f"\033[91m expected: {expected} received: {received} \033[00m ")


    def fulfillment(self, allocation_uuid, finish_event):
        # This function is not used in the mediator. The mediator becomes active when Mediation is requested
        pass

        # output_checklist = []
        # for data_input in inputs:
        #     output = data_input
        #     output_checklist.append(output)
        #
        #     hash1 = hashlib.sha256(str(output_checklist).encode("utf-8")).hexdigest()
        #     hashed_output_checklist = hashlib.sha256(hash1.encode("utf-8")).hexdigest()
        #
        # return hashed_output_checklist

    def sign(self, allocation_uuid):
        # TODO: Commit to ledger
        # TODO: Sign on ledger
        self.ledger_client.mediatorSign(allocation_uuid, self.cfg.user_uuid)




    def handle_ledger(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        print(f"MEDIATOR.py - handle_ledger; msg:{msg.value()}")
        event = msg.value().event
        user_uuid = msg.value().user_uuid
        if event == "MediationRequested":
            getattr(self, event)(msg)
        #TODO: Handle other requests


    # def process_verification(self, consumer, msg):
    #     # TODO: send data to app for processing
    #     consumer.acknowledge_cumulative(msg)
    #     print(f"\nProcess input: {msg.value()}\n")
    #
    #     if msg.value().result == "Match":
    #         print(f"user_uuid: {self.cfg.user_uuid}; Result: {msg.value().result}")
    #     else:
    #         customertimestamp = msg.value().timestamp
    #         now = datetime.datetime.now(tz=datetime.timezone.utc)
    #
    #         #TODO: Re-run relevant inputs and Compare results against hashes
    #         result = "Match"
    #         customer = ""
    #
    #         #TODO: fill out
    #         output = MV2.schema.MediationSchema(
    #             result=result,
    #             customer = customer,
    #             supplierspass = [],
    #             suppliersfail = [],
    #             allocation_uuid = msg.value().allocation_uuid,
    #             checktimestamp = msg.value().timestamp,
    #             mediationtimestamp = now.timestamp()
    #         )
    #
    #     # Send outcome of mediation
    #     self.mediation_producer.send(output)
    #     #TODO: write outcome to ledger
    #     self.ledger_client.PostMediation()

    # def cleanup(self, consumer, msg):
    #     consumer.acknowledge_cumulative(msg)
    #     self.pulsar_client.close()
    #     self.finish_event.set()









