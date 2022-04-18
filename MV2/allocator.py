import datetime
import multiprocessing
import pulsar
import sys
from termcolor import cprint
import time

import MV2.schema
import MV2.helpers.influxLogger
import MV2.helpers.ledger
import MV2.algorithms.alg1 as alg



class Allocator:
    def __init__(self, cfg):

        self.ai = 0

        self.sq = multiprocessing.Queue()
        self.cq = multiprocessing.Queue()
        self.mq = multiprocessing.Queue()

        self.supplier_offers = {}
        self.customer_offers = {}
        self.mediator_offers = {}
        self.allocations = {}

        self.cfg = cfg

        self.pulsar_client = pulsar.Client(cfg.pulsar_url)
        self.influx_logger = MV2.helpers.influxLogger.InfluxLogger(cfg)


        # consumer - customer offers
        self.coffer_consumer = self.pulsar_client.subscribe(topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/customer_offers",
                                                            schema=pulsar.schema.AvroSchema(MV2.schema.ServiceSchema),
                                                            subscription_name=f"{cfg.user_uuid}-offer-subscription",
                                                            initial_position=pulsar.InitialPosition.Earliest,
                                                            consumer_type=pulsar.ConsumerType.Exclusive,
                                                            message_listener=self.process_customer_offer)

        # consumer - supplier offers
        self.soffer_consumer = self.pulsar_client.subscribe(topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/supplier_offers",
                                                            schema=pulsar.schema.AvroSchema(MV2.schema.ResourceSchema),
                                                            subscription_name=f"{cfg.user_uuid}-offer-subscription",
                                                            initial_position=pulsar.InitialPosition.Earliest,
                                                            consumer_type=pulsar.ConsumerType.Exclusive,
                                                            message_listener=self.process_supplier_offer
                                                            )

        # consumer - mediator offers
        self.moffer_consumer = self.pulsar_client.subscribe(topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/mediator_offers",
                                                            schema=pulsar.schema.AvroSchema(MV2.schema.ResourceSchema),
                                                            subscription_name=f"{cfg.user_uuid}-offer-subscription",
                                                            initial_position=pulsar.InitialPosition.Earliest,
                                                            consumer_type=pulsar.ConsumerType.Exclusive,
                                                            message_listener=self.process_mediator_offer
                                                            )

        self.allocation_process = multiprocessing.Process(target=self.allocate, args=(self.sq, self.cq, self.mq))
        self.allocation_process.start()


    def process_customer_offer(self, consumer, msg):
        # print("\nprocess_customer_offer\n")
        consumer.acknowledge_cumulative(msg)
        # TODO: Check that offer is valid (i.e. that mediator is valid.)
        #  For now assume mediator is a reliable cloud service that is
        #  always available with fixed price so check is unnecessary
        self.cq.put(msg.value())

        print(f"\u001b[34m what did we get?: {msg.value().start}, {msg.value().end}\u001b[0m")

        # ------------------------------------------------------------------
        # state tracking
        # ------------------------------------------------------------------
        offer_uuid = msg.value().offer_uuid
        if self.cfg.influx_logging:
            log_msg = {"fields": {"state": self.cfg.State.pool.value,
                                  "sender": self.cfg.user_uuid,
                                  "allocation": None},
                        "tags": {"uuid": offer_uuid}}
            self.influx_logger.write(log_msg)
        # ------------------------------------------------------------------

    def process_supplier_offer(self, consumer, msg):
        # print("\nprocess_supplier_offer\n")
        consumer.acknowledge_cumulative(msg)
        # TODO: Check that offer is valid
        self.sq.put(msg.value())

        # ------------------------------------------------------------------
        # state tracking
        # ------------------------------------------------------------------
        offer_uuid = msg.value().offer_uuid
        if self.cfg.influx_logging:
            log_msg = {"fields": {"state": self.cfg.State.pool.value,
                                  "sender": self.cfg.user_uuid,
                                  "allocation": None},
                        "tags": {"uuid": offer_uuid}}
            self.influx_logger.write(log_msg)
        # ------------------------------------------------------------------

    def process_mediator_offer(self, consumer, msg):
        consumer.acknowledge_cumulative(msg)
        # TODO: Check that offer is valid
        self.mq.put(msg.value())


    def allocate(self,sq, cq, mq):

        print("allocate loop started")
        sys.stdout.flush()

        self.ledger_client = MV2.helpers.ledger.Client(self.cfg)
        self.pulsar_client = pulsar.Client(self.cfg.pulsar_url)

        # producer - offers
        self.allocation_producer = self.pulsar_client.create_producer(
            topic=f"persistent://{self.cfg.tenant}/{self.cfg.market_uuid}/allocations",
            schema=pulsar.schema.AvroSchema(MV2.schema.AllocationSchema))

        # consumer - accept
        self.accept_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{self.cfg.tenant}/{self.cfg.market_uuid}/accept",
            schema=pulsar.schema.AvroSchema(MV2.schema.AcceptSchema),
            subscription_name=f"{self.cfg.user_uuid}-accept-subscription",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.start_fulfillment)

        # self.ledger_producer = self.pulsar_client.create_producer(
        #     topic=f"persistent://{self.cfg.tenant}/{self.cfg.market_uuid}/ledger",
        #     schema=pulsar.schema.AvroSchema(MV2.schema.LedgerSchema))

        print("allocation_producer created")
        sys.stdout.flush()

        first = True
        new_msg = False

        while True:

            sys.stdout.flush()

            if first:
                first = False
                print("Start allocate while loop")
                sys.stdout.flush()

            while not sq.empty():
                print("add supplier messages to sq")
                sys.stdout.flush()
                msgvalue = sq.get()
                key = f"{msgvalue.offer_uuid}"
                self.supplier_offers[key] = msgvalue
                # self.cfg.print_msgvalue(msgvalue)
                print(f"len: {len(self.supplier_offers)}; supplier offers: {self.supplier_offers}")
                sys.stdout.flush()
                new_msg = True

            while not cq.empty():
                print("add customer messages to cq")
                sys.stdout.flush()
                msgvalue = cq.get()
                key = f"{msgvalue.offer_uuid}"
                self.customer_offers[key] = msgvalue
                # self.cfg.print_msgvalue(msgvalue)
                print(f"len: {len(self.customer_offers)}; customer_offers: {self.customer_offers}")
                sys.stdout.flush()
                new_msg = True

            while not mq.empty():
                print("add mediator messages to mq")
                cprint("add mediator messages to mq", "yellow")
                sys.stdout.flush()
                msgvalue = mq.get()
                key = f"{msgvalue.offer_uuid}"
                self.mediator_offers[key] = msgvalue
                # self.cfg.print_msgvalue(msgvalue)
                print(f"len: {len(self.mediator_offers)}; mediator_offers: {self.mediator_offers}")
                sys.stdout.flush()
                new_msg = True

            if new_msg and len(self.supplier_offers) > 0 and len(self.customer_offers) > 0 and len(self.mediator_offers):
                new_msg = False
                allocations = alg.allocate(self.customer_offers, self.supplier_offers, test=True)
                #TODO: change to test=False when there are more than two offers in the system
                sys.stdout.flush()
            else:
                time.sleep(10)
                cprint("no messages", "yellow")
                sys.stdout.flush()
                continue

            if not allocations:
                print("No feasible allocation")
                sys.stdout.flush()
                time.sleep(1)
            else:
                print("NEW Allocation")
                sys.stdout.flush()

                for customer_offer_uuid in allocations:
                    allocation = []
                    supplier_offer_uuid = allocations[customer_offer_uuid]["sell_offer"]
                    mediator_uuid = allocations[customer_offer_uuid]["mediator"]

                    coffer = self.customer_offers.pop(customer_offer_uuid)
                    soffer = self.supplier_offers.pop(supplier_offer_uuid)

                    for mediator_offer_uuid in self.mediator_offers:
                        #TODO: fix allocation algorithm to include a specific mediator offer instead of
                        # picking one like this
                        if mediator_uuid in mediator_offer_uuid:
                            # moffer = self.mediator_offers.pop(mediator_offer_uuid)
                            moffer = self.mediator_offers[mediator_offer_uuid]
                            allocation.append(customer_offer_uuid)
                            allocation.append(supplier_offer_uuid)
                            # allocation.append(mediator_offer_uuid)
                            #TODO: append mediator_offer_uuid when the mediator if fixed to send an accept msg.
                            break  # Once you find one, quit the loop

                    allocation_uuid = f"allocation_{self.ai}"
                    price = allocations[customer_offer_uuid]["price"]

                    timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
                    
                    allocation_msg = MV2.schema.AllocationSchema(
                        service_uuid=coffer.service_uuid,
                        customer_uuid= customer_offer_uuid, #coffer.user_uuid,  # include because this will be the tenant
                        allocation_uuid=allocation_uuid,
                        mediator_uuid=moffer.user_uuid,
                        supplier_uuids=[soffer.user_uuid],
                        allocation=allocation,
                        start=coffer.start,
                        rate=coffer.rate,
                        end=coffer.end,
                        price=price,
                        replicas=coffer.replicas,
                        timestamp=timestamp.timestamp()
                    )

                    print(f"ALLOCATION {self.ai}; allocation_msg: {allocation_msg}")
                    sys.stdout.flush()
                    self.ai = self.ai + 1

                    # List to make sure all allocated agents accept
                    self.allocations[allocation_uuid] = {}
                    self.allocations[allocation_uuid]["msg"] = allocation_msg
                    self.allocations[allocation_uuid]["pending"] = list(allocation_msg.allocation) # Need a copy not a reference
                    self.allocations[allocation_uuid]["accepted"] = []

                    print(f"allocator.py - line 235: Send allocation msg: {allocation_uuid}")
                    sys.stdout.flush()
                    self.allocation_producer.send(allocation_msg)


    def ack_received(self, res, msg_id):
        print('uuid: %s; ALLOC ACK RECEIVED: %s; msg_id: %s' % (self.cfg.user_uuid, res, msg_id))

    def stop(self):
        self.pulsar_client.close()
        self.allocation_process.terminate()


    def start_fulfillment(self, consumer, msg):
        """Fulfill job"""
        consumer.acknowledge_cumulative(msg)
        status = msg.value().status
        allocation_uuid = msg.value().allocation_uuid

        if allocation_uuid not in self.allocations:
            print(f"allocator.py - start_fulfillment: {allocation_uuid} does not belong to this allocator")
            return


        # Wait until all allocated agents accept
        for o in msg.value().offer_uuids:
            if o in self.allocations[allocation_uuid]["pending"]:
                if status == True:
                    self.allocations[allocation_uuid]["pending"].remove(o)
                    self.allocations[allocation_uuid]["accepted"].append(o)

                    # If all agents accept then create the allocation on the smart contract
                    if not self.allocations[allocation_uuid]["pending"]:
                        cprint(f"All allocated agents have accepted. Create Allocation on ledger ", "yellow")
                        alloc_msg = self.allocations[allocation_uuid]["msg"]
                        # TODO: pass arguments for message to the ledger.
                        cprint(f"{self.cfg.user_uuid} start_fulfillment: {alloc_msg}", "yellow")
                        self.ledger_client.createAllocation(
                            allocation_uuid,
                            alloc_msg)
                            # alloc_msg.customer_uuid,
                            # alloc_msg.mediator_uuid,
                            # alloc_msg.price)


                        cprint(f"{self.cfg.user_uuid} suppliers: {alloc_msg.supplier_uuids}", "yellow")
                        for supplier in alloc_msg.supplier_uuids:
                            self.ledger_client.addSupplier(allocation_uuid, supplier)


if __name__ == "__main__":

    alloc = Allocator()
