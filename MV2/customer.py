import datetime
import docker
import hashlib
import os
import pulsar
import sys
from termcolor import cprint
import time
import uuid

from MV2.helpers import DockerWrapper
import MV2.helpers.PulsarREST as PulsarREST
import MV2.schema
from MV2.trader import Trader

class Customer(Trader):

    def fulfillment(self, allocation_uuid, finish_fulfillment):
        """Send app"""

        print(f"customer.py - fulfillment; user:{self.cfg.user_uuid}, clusters:{self.cfg.clusters}")
        sys.stdout.flush()

        allocation = self.allocations[allocation_uuid]["alloc_msg"]
        self.customer_uuid = allocation.customer_uuid # aka self.offer_uuid (see allocator.py allocation_msg)

        self.dockerClient = DockerWrapper.get_docker_client()

        self.running = False
        self.num_outputs = 0

        PulsarREST.get_clusters(pulsar_admin_url=self.cfg.pulsar_admin_url)
        tenants = PulsarREST.get_tenants(pulsar_admin_url=self.cfg.pulsar_admin_url)
        PulsarREST.create_tenant(pulsar_admin_url=self.cfg.pulsar_admin_url,
                                 clusters=self.cfg.clusters,
                                 tenant=self.customer_uuid)
        
        self.offer_uuid = self.allocations[allocation_uuid]["my_offers"][0]
        PulsarREST.create_namespace(pulsar_admin_url=self.cfg.pulsar_admin_url,
                                    # tenant=self.cfg.user_uuid,
                                    tenant = self.customer_uuid,
                                    namespace=self.cfg.market_uuid)

        super(Customer, self).fulfillment(allocation_uuid, finish_fulfillment)

        self.checklist_producer = self.market_producer("checklist", MV2.schema.Checklist)

        self.cleanup_producer = self.market_producer("cleanup", MV2.schema.CleanupDataSchema)

        self.output_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/output_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.OutputDataSchema),
            subscription_name=f"{self.cfg.user_uuid}-output_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.process)

        # self.input_producer = self.market_producer("input", MV2.schema.InputDataSchema)

        self.app_producer = self.market_producer("app", MV2.schema.AppSchema)

        app_desc = MV2.schema.AppSchema(
            allocation_uuid=allocation_uuid,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )  # TODO: This channel isn't needed since we use an image registry

        print(f"\n{self.cfg.user_uuid}; pid:{os.getpid()}; send app on {self.cfg.user_uuid}/{self.cfg.market_uuid}/app_{allocation_uuid}\n")
        sys.stdout.flush()
        self.app_producer.send(app_desc)

        # TODO: This logic belongs on the data source.
        #  In this case it is the customer but there should be a source.py or something

        pulsar_url = self.cfg.pulsar_url
        tenant = self.customer_uuid
        namespace = self.cfg.market_uuid
        user_uuid = self.cfg.user_uuid
        input_uuid = self.cfg.input_uuid
        input_tag = f"{self.cfg.registry}/{self.cfg.input_uuid}"  # the registry location of the image
        name = f"{user_uuid}_{input_uuid}_{uuid.uuid4().hex}"  # Add uuid4 to avoid potential collisions of docker containers.

                                                                          # self.start/end set in trader.py
        command = f"{pulsar_url} {tenant} {namespace} {user_uuid} {allocation_uuid} {self.start} {self.end} {self.rate}"
        xdict = {
            "command": command,
            "mounts": {},
            "env": {},
            "network": ""
        }
        print(f"customer: command - {command}")
        print(f"customer: input_tag - {input_tag}")
        print(f"customer: xdict - {xdict}")
        container = DockerWrapper.run_container(client=self.dockerClient, tag=input_tag,
                                                name=name, xdict=xdict)
        print("Customer is starting container")

        DockerWrapper.get_logs(container)
        
        try: 
            exit_code = container.wait()
        except docker.errors.NotFound as e:
            print(f"docker container not found... I guess?: {e}")

        print("Customer is Waiting for all outputs")
        sys.stdout.flush()
        self.finish_fulfillment.wait()
        print("Customer is Done Waiting")

        hash_check_list_outputs = []
        for input_uuid in self.cfg.check_list:
            hash_input_uuid = hashlib.sha256(str(input_uuid).encode("utf-8")).hexdigest()
            # single hashed outputs to send to Supplier
            hash_check_list_outputs.append(hash_input_uuid)

        checklist_msg = MV2.schema.Checklist(
            allocation_uuid=self.allocation_uuid,
            checklist=hash_check_list_outputs,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        cprint(f"{self.cfg.user_uuid} send checklist", "blue")
        sys.stdout.flush()
        self.checklist_producer.send(checklist_msg)

        cprint(f"Make customer sleep. Maybe then it will ack everything")
        # Somthing weird happens here. I sometimes get the last output message
        # but not all of them get acknowleged so when I run again it re-receives them.
        # Why aren't they being acknowledged fast enough?
        for i in range(1):
            time.sleep(1)
            cprint(f"sleeping {i}", "blue")
            sys.stdout.flush()


    def process(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)

        recv_timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

        if not self.running:
            self.running = True
            allocation_uuid = msg.value().allocation_uuid

            # ------------------------------------------------------------------
            # state tracking
            # ------------------------------------------------------------------
            if self.cfg.influx_logging:
                for offer_uuid in self.allocations[allocation_uuid]["my_offers"]:
                    log_msg = {"fields": {"state": self.cfg.State.running.value,
                                          "sender": self.cfg.user_uuid,
                                          "allocation": allocation_uuid},
                               "tags": {"uuid": offer_uuid}}
                    self.influx_logger.write(log_msg)
            # ------------------------------------------------------------------

        self.num_outputs = self.num_outputs + 1
        output = msg.value().value
        cprint(f"CUSTOMER.py - process:\n"
               f"{self.cfg.user_uuid} "
               f"receive output message:{self.num_outputs}; "
               f"output value: {output}", "blue")
        sys.stdout.flush()

        # TODO: convert to time based?
        # TODO: Move to allocator?
        last = msg.value().input_uuid == self.cfg.last_input
        cprint(f"Customer.py - process"
               f"\n Last message?: {msg.value().input_uuid}=={self.cfg.last_input}: {last}"
               f"\n num_ouputs:{self.num_outputs}", "blue")
        if last:
            print("customer.py - process:"
                  "All outputs received. Call cleanup")
            sys.stdout.flush()
            cleanup = MV2.schema.CleanupDataSchema(
                allocation_uuid=msg.value().allocation_uuid,
                cleanup=True,
                timestamp=recv_timestamp
            )
            self.cleanup_producer.send(cleanup)

        sys.stdout.flush()

    def sign(self, allocation_uuid):

        '''Hash entire commit list, then hash it again. This is so that when the supplier submits its output has the verifier can hash that result and compare against the cusomter commit hash. See the paper for further details.'''

        cprint(f" {self.cfg.user_uuid} Signing", "blue")
        hash1 = hashlib.sha256(str(self.cfg.commit_list).encode("utf-8")).hexdigest()
        hash_commitlist = hashlib.sha256(hash1.encode("utf-8")).hexdigest()
        cprint(f"{self.cfg.user_uuid}; hash1: {hash1}; commit: {hash_commitlist}", "blue")
        sys.stdout.flush()
        self.pulsar_sign(hash_commitlist, allocation_uuid)

    def pulsar_sign(self, hash_commitlist, allocation_uuid):
        # TODO: Commit to blockchain
        # TODO: Sign on blockchain
        offer_uuid = self.allocations[allocation_uuid]["my_offers"][0] # TODO:  if multiple offers are in 1 allocation this will need work

        self.ledger_client.customerSign(allocation_uuid, offer_uuid, hash_commitlist)

    def cleanup(self, consumer, msg):
        super(Customer, self).cleanup(consumer, msg)
        self.finish_fulfillment.set()


