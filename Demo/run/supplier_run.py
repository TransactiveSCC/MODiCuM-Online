import datetime
import multiprocessing
import argparse
import sys
import time
import uuid

import demo_cfg as cfg
import MV2.supplier
import MV2.schema


class SupplierAgent:
    def __init__(self, offer_schedule, behavior, Ps):

        self.cfg0 = cfg.Cfg()
        self.cfg0.user_uuid = f"supplier_{uuid.uuid4().hex}"
        self.cfg0.topic = "supplier_offers"
        self.cfg0.mediators = ["mediator_1"]
        self.cfg0.strategy["behavior"] = behavior
        self.cfg0.strategy["P(s)"] = Ps

        self.offers = getattr(self.cfg0, offer_schedule)
        # TODO: Add some logic either to read the mediator_offers channel or have some other way of discovering mediators
        self.finish_event = multiprocessing.Event()

        self.actor = MV2.supplier.Supplier(self.cfg0, MV2.schema.ResourceSchema)
        print(f"Start simulated {self.cfg0.user_uuid} user")
        sys.stdout.flush()

    def handle_offers(self):

        for idx, offer in enumerate(self.offers):

            start = datetime.datetime.fromisoformat(offer["start"]).timestamp()
            end = datetime.datetime.fromisoformat(offer["end"]).timestamp()
            delay = float(offer["delay"])
            now = time.time()

            if end < now:
                print(f"{now-start} seconds too late, end has already passed")
                continue

            if start-delay > now:
                wait = start - delay - now
                print(f"{wait} seconds too early, wait to submit offer")
                time.sleep(wait)

            print(f"index: {idx}, start: {start}, end: {end}, now: {now}")

            resource_uuid = f"resource_{idx}"


            offer = MV2.schema.ResourceSchema(
                user_uuid=self.cfg0.user_uuid,
                offer_uuid=f"{self.cfg0.user_uuid}_offer_{idx}",
                resource_uuid=resource_uuid,
                start=start,
                end=end,
                cpu=1e9,
                price=1e-6,
                mediators=self.cfg0.mediators,
                timestamp=now
            )

            self.actor.post_offer(offer)
            sys.stdout.flush()

        self.finish_event.wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("offer_schedule", type=str,
                        default="sporadic",
                        help="defines offer schedule")
    parser.add_argument("--num_offers", type=str,)
    parser.add_argument("behavior", default="nominal",
                        help="Flag to select particular behavior logic")
    parser.add_argument("--Ps", type=str, default="1.0",
                        help="Probability, used for deciding whether to process input or not")
    args = parser.parse_args()

    SA = SupplierAgent(offer_schedule=args.offer_schedule,
                       behavior=args.behavior,
                       Ps=float(args.Ps))

    SA.handle_offers()
