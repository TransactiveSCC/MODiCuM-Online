import argparse
import time

import demo_cfg as cfg
import datetime
import multiprocessing
import sys
import uuid
import MV2.customer
import MV2.schema


class CustomerAgent:
    def __init__(self, offer_schedule):

        self.cfg0 = cfg.Cfg()
        self.cfg0.user_uuid = f"customer_{uuid.uuid4().hex}"
        self.cfg0.topic = "customer_offers"
        self.cfg0.mediators = ["mediator_1"]
        self.offers = getattr(self.cfg0, offer_schedule)
        #TODO: Add some logic either to read the mediator_offers channel or have some other way of discovering mediators
        self.finish_event = multiprocessing.Event()

        print(f"Starting {self.cfg0.user_uuid} user")
        sys.stdout.flush()

        self.actor = MV2.customer.Customer(self.cfg0, MV2.schema.ServiceSchema)
        print(f"Started simulated {self.cfg0.user_uuid} user")
        sys.stdout.flush()

    def handle_offers(self):

        for idx, offer in enumerate(self.offers):

            start = datetime.datetime.fromisoformat(offer["start"]).timestamp()
            end = datetime.datetime.fromisoformat(offer["end"]).timestamp()
            delay = float(offer["delay"])
            now = time.time()

            if now > end:
                print(f"{now-end} seconds too late, end has already passed")
                continue

            if start-delay > now:
                wait = start - delay - now
                print(f"{wait} seconds too early, wait to submit offer")
                time.sleep(wait)

            print(f"index: {idx}, start: {start}, end: {end}, now: {now}")

            offer = MV2.schema.ServiceSchema(
                user_uuid=self.cfg0.user_uuid,
                offer_uuid=f"{self.cfg0.user_uuid}_offer_{idx}",
                service_uuid=self.cfg0.service_uuid,
                start=start,
                end=end,
                cpu=1e6,
                rate=.5,  # requests/second 
                price=1e-6,
                replicas=2,
                mediators=self.cfg0.mediators,
                timestamp=now
            )

            self.actor.post_offer(offer)
            sys.stdout.flush()

            # TODO add listener for service end and submit new offer and sleep.

        self.finish_event.wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("offer_schedule", type=str,
                        default="sporadic",
                        help="defines offer schedule")
    args = parser.parse_args()

    CA = CustomerAgent(offer_schedule=args.offer_schedule)
    CA.handle_offers()
