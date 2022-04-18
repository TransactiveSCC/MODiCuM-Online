import datetime
import multiprocessing
import sys
from termcolor import cprint

import MV2.mediator

import cfg


cfg0 = cfg.Cfg()
cfg0.topic = "mediator_offers"
cfg0.user_uuid = "mediator_1"
finish_event = multiprocessing.Event()


actor = MV2.mediator.Mediator(cfg0, MV2.schema.ResourceSchema)
print(f"Start simulated {cfg0.user_uuid} user")
sys.stdout.flush()


for i in range(1):
    resource_uuid = f"mdtr_rsrc_{i}"
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    start = now + datetime.timedelta(minutes=1)
    end = start + datetime.timedelta(days=1, minutes=2)

    offer = MV2.schema.ResourceSchema(
        user_uuid=cfg0.user_uuid,
        offer_uuid=f"{cfg0.user_uuid}_offer_{i}",
        resource_uuid=resource_uuid,
        start=start.timestamp(),
        end=end.timestamp(),
        cpu=1e6,
        price=1e-6,
        mediators=[cfg0.user_uuid],
        timestamp=now.timestamp(),
        behavior=1.0
    )

    actor.post_offer(offer)
    sys.stdout.flush()

cprint("Mediator is Waiting", "green")
sys.stdout.flush()
finish_event.wait()
cprint("Mediator is Done Waiting", "green")
sys.stdout.flush()
