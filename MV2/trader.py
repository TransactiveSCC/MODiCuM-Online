import datetime
import os
import multiprocessing
import pulsar
import sys
import time
import MV2.helpers.ledger
import MV2.helpers.PulsarREST as PulsarREST
import MV2.schema


class Trader:
    def __init__(self, cfg, schema):
        """set up allocation channel"""

        self.pulsar_client = pulsar.Client(cfg.pulsar_url)
        self.ledger_client = MV2.helpers.ledger.Client(cfg)
        self.influx_logger = MV2.helpers.influxLogger.InfluxLogger(cfg)

        # producer - offers
        self.offer_producer_1 = self.pulsar_client.create_producer(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/{cfg.topic}",
            schema=pulsar.schema.AvroSchema(schema))

        # producer - accept
        self.accept_producer_4 = self.pulsar_client.create_producer(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/accept",
            schema=pulsar.schema.AvroSchema(MV2.schema.AcceptSchema))

        # # consumer - allocations
        self.allocation_consumer_3 = self.pulsar_client.subscribe(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/allocations",
            schema=pulsar.schema.AvroSchema(MV2.schema.AllocationSchema),
            subscription_name=f"{cfg.user_uuid}-allocation-subscription",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.eval_allocation)

        self.cfg = cfg
        self.offers = {}
        self.allocations = {}
        self.processes = {}

        # consumer - accept
        self.accept_consumer_4 = self.pulsar_client.subscribe(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/accept",
            schema=pulsar.schema.AvroSchema(MV2.schema.AcceptSchema),
            subscription_name=f"{cfg.user_uuid}-accept-subscription",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.handle_accept)

        # consumer - accept
        self.market_consumer_10 = self.pulsar_client.subscribe(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/market",
            schema=pulsar.schema.AvroSchema(MV2.schema.MarketSchema),
            subscription_name=f"{cfg.user_uuid}-market-subscription",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.handle_ledger)

        print(f"trader.py - init: {self.cfg.user_uuid} initialized")
        sys.stdout.flush()

    def timeout(self):
        #  TODO. create queue for posted offers to cancel them and resubmit
        pass

    def ack_received(self, res, msg_id):
        print(f'uuid: {self.cfg.user_uuid}; ACK RECEIVED: {res}; msg_id: {msg_id}')

    def post_offer(self, offer):
        self.offers[f"{offer.offer_uuid}"] = offer
        self.offer_producer_1.send_async(offer, callback=self.ack_received)
        print(f"trader.py - post_offer")
        sys.stdout.flush()

        # ------------------------------------------------------------------
        # state tracking (1)
        # ------------------------------------------------------------------
        if self.cfg.influx_logging:            
            log_msg = {"fields": {"state": self.cfg.State.post_offer.value,
                                  "sender": self.cfg.user_uuid,
                                  "allocation": None},
                        "tags": {"uuid": offer.offer_uuid}}
            self.influx_logger.write(log_msg)
        #------------------------------------------------------------------

    def eval_allocation(self, consumer, msg):
        print(f"trader.py - eval_allocation: {self.cfg.user_uuid}")
        sys.stdout.flush()
        self.cfg.print_msg(consumer, msg)
        consumer.acknowledge(msg)

        status = False

        allocation_msg = msg.value()
        allocation_uuid = msg.value().allocation_uuid

        my_offers = [o for o in allocation_msg.allocation if o in self.offers]

        if my_offers or allocation_msg.mediator_uuid == self.cfg.user_uuid:
            # TODO evaluate allocation (check that it is valid)
            # TODO: include mediator in the allocation_msg.allocation
            status = True
        else:
            print(f"trader.py - eval_allocation: The offers in this allocation do not belong to {self.cfg.user_uuid}")
            sys.stdout.flush()


        if status:
            self.allocations[allocation_uuid] = {}
            self.allocations[allocation_uuid]["alloc_msg"] = allocation_msg
            self.allocations[allocation_uuid]["pending"] = list(allocation_msg.allocation)  # Need copy not reference
            self.allocations[allocation_uuid]["accepted"] = []
            self.allocations[allocation_uuid]["my_offers"] = my_offers
            print(f"trader.py - eval_allocation:"
                  f"{self.cfg.user_uuid} "
                  f"ALLOCATIONS: {self.allocations} "
                  f"Accepts Pending: {self.allocations[allocation_uuid]['pending']}")

            status = MV2.schema.AcceptSchema(
                allocation_uuid=allocation_uuid,
                offer_uuids=my_offers,
                status=status,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            )

            if my_offers:
                for o in my_offers:
                    self.offers.pop(o, None)

                    # ------------------------------------------------------------------
                    # state tracking (3)
                    # ------------------------------------------------------------------
                    if self.cfg.influx_logging:
                        log_msg = {"fields": {"state": self.cfg.State.allocated.value,
                                              "sender": self.cfg.user_uuid,
                                              "allocation": allocation_uuid},
                                   "tags": {"uuid": o}}
                        self.influx_logger.write(log_msg)
                    #------------------------------------------------------------------

            self.accept_producer_4.send(status)

    def handle_ledger(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)

        print(f"{self.cfg.user_uuid}- handle_ledger; msg:{msg.value()}")

        # if msg.value().user_uuid == self.cfg.user_uuid:
        allocation_uuid = msg.value().allocation_uuid
        if allocation_uuid in self.allocations:
            state = None
            if msg.value().event == "AllocationCreated" or msg.value().event == "SupplierAdded":
                self.sign(allocation_uuid)
            elif msg.value().event == "OutputPosted":
                state = self.cfg.State.OutputPosted.value
            elif msg.value().event == "MediationRequested":
                state = self.cfg.State.MediationRequested.value
            elif msg.value().event == "MediationCompleted":
                state = self.cfg.State.MediationCompleted.value
            # ------------------------------------------------------------------
            # state tracking (7,8,9)
            # ------------------------------------------------------------------
            if self.cfg.influx_logging and state:
                for offer_uuid in self.allocations[allocation_uuid]["my_offers"]:
                    log_msg = {"fields": {"state": state,
                                          "sender": self.cfg.user_uuid,
                                          "allocation": allocation_uuid},
                                "tags": {"uuid": offer_uuid}}
                    self.influx_logger.write(log_msg)
            #------------------------------------------------------------------



    def sign(self, allocation_uuid):
        pass

    def handle_accept(self, consumer, msg):
        """Fulfill job"""
        consumer.acknowledge_cumulative(msg)
        status = msg.value().status
        allocation_uuid = msg.value().allocation_uuid

        if allocation_uuid not in self.allocations:
            print(f"trader.py - handle_accept: This accept allocation is not relevant to this actor")
            print(f"allocation_uuid:{allocation_uuid}, allocations: {self.allocations}")
            sys.stdout.flush()
            return

        # Wait until all allocated agents accept
        for offer_uuid in msg.value().offer_uuids:
            if offer_uuid in self.allocations[allocation_uuid]["pending"]:
                if status:
                    self.allocations[allocation_uuid]["pending"].remove(offer_uuid)
                    self.allocations[allocation_uuid]["accepted"].append(offer_uuid)

                    if not self.allocations[allocation_uuid]["pending"]:
                        finish_fulfillment = multiprocessing.Event()
                        self.processes[allocation_uuid] = {"p": multiprocessing.Process(target=self.fulfillment,
                                                                                        args=(allocation_uuid,
                                                                                              finish_fulfillment)),
                                                           "e": finish_fulfillment}
                        print(f"\n{self.cfg.user_uuid}_{allocation_uuid} accepted: {status}\n")

                        # for aoffer_uuid in self.allocations[allocation_uuid["accepted"]]:
                        for acc_offer_uuid in self.allocations[allocation_uuid]["accepted"]:
                            if acc_offer_uuid in self.allocations[allocation_uuid]["my_offers"]:

                                # ------------------------------------------------------------------
                                # state tracking (4)
                                # ------------------------------------------------------------------
                                if self.cfg.influx_logging:                                   
                                    log_msg = {"fields": {"state": self.cfg.State.accepted.value,
                                                          "sender": self.cfg.user_uuid,
                                                          "allocation": allocation_uuid},
                                               "tags": {"uuid": acc_offer_uuid}}
                                    self.influx_logger.write(log_msg)
                                #------------------------------------------------------------------ 

                        self.processes[allocation_uuid]["p"].start()

    def fulfillment(self, allocation_uuid, finish_fulfillment):

        allocation = self.allocations[allocation_uuid]["alloc_msg"]
        self.customer_uuid = allocation.customer_uuid
        self.allocation_uuid = allocation_uuid
        self.start = allocation.start
        self.end = allocation.end
        self.rate = allocation.rate

        while True:
            sys.stdout.flush()
            tenants = PulsarREST.get_tenants(pulsar_admin_url=self.cfg.pulsar_admin_url)
            print(f"tenants: {tenants}")
            if self.customer_uuid in tenants:
                break
            else:
                print(f"{self.cfg.user_uuid}, before doing anything, sleep to make sure tenant exists")
                time.sleep(1)
                continue

        while True:
            sys.stdout.flush()
            namespaces = PulsarREST.get_namespaces(pulsar_admin_url=self.cfg.pulsar_admin_url,
                                                   tenant=self.customer_uuid)
            if not namespaces:
                time.sleep(1)
                continue

            print(f"trader.py - fulfillment:"
                  f"{self.customer_uuid}/{self.cfg.market_uuid} is in namespaces:"
                  f"{self.customer_uuid}/{self.cfg.market_uuid}" in namespaces)
            sys.stdout.flush()

            if f"{self.customer_uuid}/{self.cfg.market_uuid}" not in namespaces:
                print(f"{self.cfg.user_uuid}, before doing anything, sleep to make sure namespace exists")
                time.sleep(1)
                continue
            else:
                break

        self.finish_fulfillment = finish_fulfillment
        self.pulsar_client = pulsar.Client(self.cfg.pulsar_url)
        self.num_inputs = 0

        print(f"\nSTART {self.cfg.user_uuid} fulfillment: {allocation_uuid}; "
              f"pid:{os.getpid()}; "
              f"Topic: {self.customer_uuid}/{self.cfg.market_uuid}/app_{allocation_uuid} \n")

        self.cleanup_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/cleanup_{allocation_uuid}",
            schema=pulsar.schema.AvroSchema(MV2.schema.CleanupDataSchema),
            subscription_name=f"{self.cfg.user_uuid}-cleanup_{allocation_uuid}",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.cleanup)

    def run(self):
        pass

    def stop(self):

        for allocation_uuid in self.processes:
            self.processes[allocation_uuid]["e"].set()
            self.processes[allocation_uuid]["p"].terminate()

        self.pulsar_client.close()

    def cleanup(self, consumer, msg):
        # TODO: This doesn't do anything other than log right now... maybe delete?
        print(f"close user_uuid: {self.cfg.user_uuid}; pid: {os.getpid()}")
        sys.stdout.flush()
        consumer.acknowledge_cumulative(msg)


        # ------------------------------------------------------------------
        # state tracking (6)
        # ------------------------------------------------------------------
        allocation_uuid = msg.value().allocation_uuid
        for offer_uuid in self.allocations[allocation_uuid]["my_offers"]:
            if self.cfg.influx_logging:
                log_msg = {"fields": {"state": self.cfg.State.cleanup.value,
                                      "sender": self.cfg.user_uuid,
                                      "allocation": allocation_uuid},
                           "tags": {"uuid": offer_uuid}}
                self.influx_logger.write(log_msg)
        #------------------------------------------------------------------

    def market_producer(self, topic, schema):
        producer = self.pulsar_client.create_producer(
            topic=f"persistent://{self.customer_uuid}/{self.cfg.market_uuid}/{topic}_{self.allocation_uuid}",
            schema=pulsar.schema.AvroSchema(schema)
        )
        return producer
