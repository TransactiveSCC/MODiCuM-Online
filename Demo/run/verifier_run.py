import multiprocessing
import sys
from termcolor import cprint

import MV2.verifier

import cfg

cfg0 = cfg.Cfg()
cfg0.user_uuid = "verifier"
verifier = MV2.verifier.Verifier(cfg0)
finish_event = multiprocessing.Event()

cprint("verifier is Waiting", "cyan")
sys.stdout.flush()
finish_event.wait()
cprint("verifier is Done Waiting", "cyan")
sys.stdout.flush()




