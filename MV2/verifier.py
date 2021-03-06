import datetime
import hashlib
import multiprocessing
import os
import pulsar
import sys
from termcolor import cprint

import MV2.helpers.helpers as helper
import MV2.helpers.influxLogger
import MV2.schema


# def verification_consumer():
#     return pulsar_verifier()
#     # return blockchain_verifier()
#
#
def pulsar_verifier():
    #TODO
    pass
#     pulsar_consumer = self.pulsar_client.subscribe(
#         topic=f"persistent://{cfg.tenant}/{self.cfg.market_uuid}/verify",
#         schema=pulsar.schema.AvroSchema(MV2.schema.VerifySchema),
#         subscription_name=f"{self.cfg.user_uuid}-verify",
#         initial_position=pulsar.InitialPosition.Latest,
#         consumer_type=pulsar.ConsumerType.Exclusive,
#         message_listener=self.process_verification)
#     return pulsar_consumer

def blockchain_verifier():
    #TODO: blockchain verifier equivalent.
    pass


class Verifier:

    def __init__(self, cfg):

        self.cfg = cfg
        cprint(f"START {self.cfg.user_uuid}; pid:{os.getpid()}", "green")
        sys.stdout.flush()
        self.finish_event = multiprocessing.Event()
        self.allocations = {}
        self.outputsPosted = {}

        self.pulsar_client = pulsar.Client(cfg.pulsar_url)
        self.influx_logger = MV2.helpers.influxLogger.InfluxLogger(cfg)

        if not helper.waiting4namespace(self.cfg):
            self.market_producer = self.pulsar_client.create_producer(
                topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/market",
                schema=pulsar.schema.AvroSchema(MV2.schema.MarketSchema))

        # Simulates ledger receiving 'createAllocation' transaction
        self.ledger_consumer = self.pulsar_client.subscribe(
            topic=f"persistent://{cfg.tenant}/{cfg.market_uuid}/ledger",
            schema=pulsar.schema.AvroSchema(MV2.schema.LedgerSchema),
            subscription_name=f"{cfg.user_uuid}-ledger-subscription",
            initial_position=pulsar.InitialPosition.Earliest,
            consumer_type=pulsar.ConsumerType.Exclusive,
            message_listener=self.eval_transaction)

    def createAllocation(self, msg):

        cprint(f"{self.cfg.user_uuid} CreateAllocation", "green")
        sys.stdout.flush()
        allocation_uuid = msg.value().allocation_uuid
        customer_uuid = msg.value().user_uuid
        mediator_uuid = msg.value().mediator_uuid
        # allocation = msg.value().allocation
        allocation = msg.value().args
        value = msg.value().price

        self.allocations[allocation_uuid] = {"customer": {"uuid": customer_uuid,
                                                          "signed": False},
                                             "suppliers": {},
                                             "allocation": allocation}
        # TODO: MEDIATOR WILL EVENTUALLY NEED TO ACTUALLY SIGN... probably
        self.allocations[allocation_uuid]["mediator"] = {"uuid": mediator_uuid,
                                                         "signed": True}
        self.allocations[allocation_uuid]["value"] = value
        self.outputsPosted[allocation_uuid] = 0

        cprint(f"{self.cfg.user_uuid} createAllocation: {self.allocations}", "green")
        sys.stdout.flush()

        market_msg = MV2.schema.MarketSchema(
            allocation_uuid=allocation_uuid,
            ledger_id=1,  # supposed to be the identifier for a supplier on a give allocation
            user_uuid=customer_uuid,
            event="AllocationCreated",
            args_bytes=[],
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        self.market_producer.send(market_msg)

    def addSupplier(self, msg):

        allocation_uuid = msg.value().allocation_uuid
        args = msg.value().args

        supplier_uuid = msg.value().user_uuid
        self.allocations[allocation_uuid]["suppliers"][supplier_uuid] = {"signed": False}


        cprint(f"{self.cfg.user_uuid} addSupplier", "green")
        sys.stdout.flush()


        market_msg = MV2.schema.MarketSchema(
            allocation_uuid=allocation_uuid,
            ledger_id=1,  # supposed to be the identifier for a supplier on a give allocation
            user_uuid=supplier_uuid,
            event="SupplierAdded",
            args_bytes=[],
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        self.market_producer.send(market_msg)

    def customerSign(self, msg):

        allocation_uuid = msg.value().allocation_uuid
        user_uuid = msg.value().user_uuid

        hashed_commitlist = msg.value().args[0]
        self.allocations[allocation_uuid]["customer"] = {"uuid": user_uuid,
                                                         "commit_hash": hashed_commitlist,
                                                         "signed": True}

        cprint(f"{self.cfg.user_uuid}: customer signed {self.allocations[allocation_uuid]}", "green")
        sys.stdout.flush()

    def supplierSign(self, msg):
        allocation_uuid = msg.value().allocation_uuid
        user_uuid = msg.value().user_uuid
        # self.allocations[allocation_uuid][user_uuid]["signed"] = True
        self.allocations[allocation_uuid]["suppliers"] = {user_uuid:
                                                          {"signed": True}
                                                          }

        cprint(f"{self.cfg.user_uuid} Supplier signed: {self.allocations[allocation_uuid]}", "green")
        sys.stdout.flush()

    def mediatorSign(self, msg):

        allocation_uuid = msg.value().allocation_uuid
        user_uuid = msg.value().user_uuid
        self.allocations[allocation_uuid]["mediator"] = {"uuid": user_uuid,
                                                         "signed": True}

        cprint(f"{self.cfg.user_uuid} Mediator signed: {self.allocations[allocation_uuid]}", "green")
        sys.stdout.flush()

    # Supplier post output
    def postOutput(self, msg):

        allocation_uuid = msg.value().allocation_uuid
        supplier_uuid = msg.value().user_uuid

        input_MessageId_list  = msg.value().args_bytes

        cprint(f"{self.cfg.user_uuid} postOutput: {self.allocations}", "green")
        sys.stdout.flush()

        hashed_customer_commit = self.allocations[allocation_uuid]["customer"]["commit_hash"]
        supplier_commit = msg.value().args[0]
        hashed_supplier_commit = hashlib.sha256(supplier_commit.encode("utf-8")).hexdigest()
        self.allocations[allocation_uuid]["suppliers"][supplier_uuid]["commit_hash"] = hashed_supplier_commit
        self.allocations[allocation_uuid]["suppliers"][supplier_uuid]["outputPosted"] = True
        self.outputsPosted[allocation_uuid] += 1

        cprint(f"{self.cfg.user_uuid} record supplier commit: "
               f" supplier_commit: {supplier_commit}; "
               f" hashed_supplier_commit: {hashed_supplier_commit} "
               f" hashed_customer_commit: {hashed_customer_commit}", "green")
        sys.stdout.flush()

        market_msg = MV2.schema.MarketSchema(
            allocation_uuid=allocation_uuid,
            ledger_id=1,  # supposed to be the identifier for a supplier on a given allocation
            user_uuid=supplier_uuid,
            event="OutputPosted",
            args_bytes=[],
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )
        self.market_producer.send(market_msg)

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if hashed_customer_commit == hashed_supplier_commit:

            verifcation_msg = MV2.schema.VerifySchema(
                allocation_uuid=allocation_uuid,
                result="Match",
                timestamp=now.timestamp()
            )

            cprint(f"{self.cfg.user_uuid} MATCH", "green")
            sys.stdout.flush()
            self.clearMarket(allocation_uuid)

        else:
            verifcation_msg = MV2.schema.VerifySchema(
                allocation_uuid=allocation_uuid,
                result="Mismatch",
                timestamp=now.timestamp())

            cprint(f"{self.cfg.user_uuid} NOT A MATCH, REQUEST MEDIATION", "green")
            sys.stdout.flush()
            self.allocations[allocation_uuid]["mediator"]["status"] = "REQUESTED"

            market_msg = MV2.schema.MarketSchema(
                allocation_uuid=allocation_uuid,
                ledger_id=1,  # supposed to be the identifier for a supplier on a given allocation
                user_uuid=supplier_uuid,
                customer_uuid=self.allocations[allocation_uuid]["customer"]["uuid"],
                customer_hash=hashed_customer_commit,
                event="MediationRequested",
                args_bytes=input_MessageId_list,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
            )

            self.market_producer.send(market_msg)

        sys.stdout.flush()

    def postMediation(self, msg):

        allocation_uuid = msg.value().allocation_uuid
        hashed_mediator_output = msg.value().args[0]
        mediator_uuid = msg.value().user_uuid

        self.allocations[allocation_uuid]["mediator"]["commit_hash"] = hashed_mediator_output

        cprint(f"VERIFIER.py - postMediation: mediation posted", "green")
        sys.stdout.flush()
        self.allocations[allocation_uuid]["mediator"]["status"] = "COMPLETED"

        market_msg = MV2.schema.MarketSchema(
            allocation_uuid=allocation_uuid,
            ledger_id=1,  # supposed to be the identifier for a supplier on a give allocation
            user_uuid=mediator_uuid,
            event="MediationCompleted",
            args_bytes=[],
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        self.market_producer.send(market_msg)

        self.clearMarket(allocation_uuid)

    def clearMarket(self, allocation_uuid):

        allocation = self.allocations[allocation_uuid]

        if len(allocation["suppliers"]) == self.outputsPosted[allocation_uuid]:

            cprint(f"VERIFIER.py - clearMarket; is allocation == self.allocations[msg.value().allocation_uuid]?\n"
                   f"{allocation is self.allocations[allocation_uuid]}", "green")
            hashed_customer_commit = allocation["customer"]["commit_hash"]

            if "status" not in allocation["mediator"]:
                self.compareHash(hashed_customer_commit, allocation)
            else:
                mediator_commit = allocation["mediator"]["commit_hash"]
                self.compareHash(mediator_commit, allocation)

        # ------------------------------------------------------------------
        # state tracking TODO: Should emit closed event and be logged on S and C
        # ------------------------------------------------------------------
        if self.cfg.influx_logging:

            c_uuid = allocation["customer"]["uuid"]
            s_uuids = allocation["suppliers"]
            log_msg = {"fields": {"state": self.cfg.State.Closed.value,
                                  "sender": self.cfg.user_uuid,
                                  "allocation": allocation_uuid},
                        "tags": {"uuid": c_uuid}}
            self.influx_logger.write(log_msg)


            for offer_uuid in s_uuids:
                log_msg = {"fields": {"state": self.cfg.State.Closed.value,
                                      "sender": self.cfg.user_uuid,
                                      "allocation": allocation_uuid},
                            "tags": {"uuid": offer_uuid}}
                self.influx_logger.write(log_msg)
        #------------------------------------------------------------------


    def compareHash(self, true_hash, allocation):

        for supplier_uuid in allocation["suppliers"]:
            supplier = allocation["suppliers"][supplier_uuid]
            cprint(f"VERIFIER.py - compareHash; "
                   f"supplier['commit_hash']: {supplier['commit_hash']}"
                   f"true_hash: {true_hash}", "green")

            if supplier["commit_hash"] == true_hash:
                cprint(f"{self.cfg.user_uuid} pay {supplier_uuid}", "green")

                txn = allocation["value"]

                self.sendEther(supplier_uuid, txn)
            else:
                cprint(f"VERIFIER.py - compareHash;"
                       f"fine Supplier: {supplier_uuid}", "green")

        customer_uuid = allocation["customer"]["uuid"]
        if allocation["customer"]["commit_hash"] == true_hash:
            cprint(f"VERIFIER.py - compareHash;"
                   f"Customer {customer_uuid} pays for job", "green")
            #TODO: charge customer and return deposits
        else:
            cprint(f"VERIFIER.py - compareHash;"
                   f"fine Customer: {customer_uuid} ", "green")
            #TODO: take Customer deposit, return Supplier deposit

        sys.stdout.flush()

    def sendEther(self, user_uuid, txn):

        cprint(f"VERIFIER.py - sendEther; \n"
               f"transfer {txn} for: {user_uuid}", "green")
        sys.stdout.flush()

    def eval_transaction(self, consumer, msg):

        print(f"VERIFIER.py - eval_transaction; \n"
              f"eval_transaction: {msg.value()}")
        sys.stdout.flush()

        consumer.acknowledge_cumulative(msg)
        function = msg.value().function
        user_uuid = msg.value().user_uuid

        # call passed function
        getattr(self, function)(msg)


    def stop(self):
        self.pulsar_client.close()
