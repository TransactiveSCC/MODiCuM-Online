import datetime
import hashlib
import time

import cfg

class Cfg(cfg.Cfg):
    def __init__(self):
        super(Cfg, self).__init__()

    # CONFIG FOR DEMO
    # Supplier behavior - honest, wrongNth, noNth, extraNth
    strategy = {"behavior": "honest",
                "P(s)": 1}

    # APP CONFIG
    topic = "customer_offers"
    window = 60
    # image_name = "stress-ng-app"
    # version = "v2"
    service_uuid = "frame-sink"
    input_uuid = "frame-source"
    last_input = "last7777777777777777777777777777"
    # TODO: replace with hashlib.sha256(app_input).hexdigest()
    #  where app_input is the img_bytes of the last jpg.

    # Customer behavior
    # - honest: commit list matches check list
    # - dishonest: commit list does not match check list
    # commit_list = [6, 4, 6, 4, 6]
    # check_list = [6, 4, 6, 4, 6]
    commit_list = ['7ed7e492467ccad8dc2dd8876e9e0725867a3064b2903961bba2884fdc68a66b_6',
                   'd91ec2b1dfd69c916f2f6fdd314afff239cba45fc93fffadb4c6f7b4f347233e_4',
                   'eceb5b08f4b667568db75ccf6f1a260905c6babc7dcc6530f61f0c73f29c72f7_6',
                   '6a92de3dfc6a50591ca747c69a637d6f7f52ebf456731dde4c890cb252f5fe8d_4',
                   '9a349c9744350c288628856a6a8987d3c8757946b6daf738eb6024ac805309c4_6']

    check_list = ['7ed7e492467ccad8dc2dd8876e9e0725867a3064b2903961bba2884fdc68a66b',
                  'd91ec2b1dfd69c916f2f6fdd314afff239cba45fc93fffadb4c6f7b4f347233e',
                  'eceb5b08f4b667568db75ccf6f1a260905c6babc7dcc6530f61f0c73f29c72f7',
                  '6a92de3dfc6a50591ca747c69a637d6f7f52ebf456731dde4c890cb252f5fe8d',
                  '9a349c9744350c288628856a6a8987d3c8757946b6daf738eb6024ac805309c4']


    # -------------------------------------
    # Sporadic offer schedule configuration
    # -------------------------------------
    tmp_delay = datetime.timedelta(hours=0, minutes=3, seconds=0)  # how long prior to start should offer be submitted
    tmp_start = (datetime.datetime.utcnow() + tmp_delay)
    tmp_duration = datetime.timedelta(hours=1, minutes=0, seconds=0)  # How long service should run
    tmp_end = tmp_start + tmp_duration
    # start = "2021-10-15T12:28:00-05:00"
    # end = "2021-10-15T14:32:00-05:00
    delay = tmp_delay.total_seconds()
    start = tmp_start.isoformat()
    end = tmp_end.isoformat()
    # print(f"\033[92m start: {start}, end: {end}, delay: {delay} \033[00m")
    sporadic = [
        {"delay": delay,
         "start": start,
         "end": end},
    ]

    # -------------------------------------
    # long offer schedule configuration
    # -------------------------------------
    tmp_delay = datetime.timedelta(hours=0, minutes=3, seconds=0)  # how long prior to start should offer be submitted
    tmp_start = (datetime.datetime.utcnow() + tmp_delay)
    tmp_duration = datetime.timedelta(hours=1, minutes=0, seconds=0)  # How long service should run
    tmp_end = tmp_start + tmp_duration
    # start = "2021-10-15T12:28:00-05:00"
    # end = "2021-10-15T14:32:00-05:00
    delay = tmp_delay.total_seconds()
    start = tmp_start.isoformat()
    end = tmp_end.isoformat()
    # print(f"\033[92m start: {start}, end: {end}, delay: {delay} \033[00m")
    long = [
        {"delay": delay,
         "start": start,
         "end": end},
    ]

    # -------------------------------------
    # multi-offer schedule configuration
    # -------------------------------------
    num_offers = 3
    multi = []
    tmp_delay = datetime.timedelta(hours=0, minutes=3, seconds=0)  # how long prior to start should offer be submitted
    tmp_start = (datetime.datetime.utcnow() + tmp_delay)
    for i in range(num_offers):
        tmp_start = tmp_start + tmp_delay
        tmp_duration = datetime.timedelta(hours=1, minutes=0, seconds=0)  # How long service should run
        tmp_end = tmp_start + tmp_duration
        delay = tmp_delay.total_seconds()
        start = tmp_start.isoformat()
        end = tmp_end.isoformat()
        multi.append({"delay": delay,
                      "start": start,
                      "end": end})

    # -------------------------------------
    # supplier multi-offer schedule configuration
    # -------------------------------------
    num_soffers = 4
    multi_s = []
    tmp_delay = datetime.timedelta(hours=0, minutes=0, seconds=5)  # how long prior to start should offer be submitted
    tmp_start = (datetime.datetime.utcnow() + tmp_delay)
    for i in range(num_soffers):
        tmp_start = tmp_start + tmp_delay
        tmp_duration = datetime.timedelta(hours=2, minutes=0, seconds=0)  # How long service should run
        tmp_end = tmp_start + tmp_duration
        delay = tmp_delay.total_seconds()
        start = tmp_start.isoformat()
        end = tmp_end.isoformat()
        multi_s.append({"delay": delay,
                        "start": start,
                        "end": end})

    # -------------------------------------
    # supplier long offer schedule configuration
    # -------------------------------------
    num_soffers = 1
    long_s = []
    tmp_delay = datetime.timedelta(hours=0, minutes=0, seconds=5)  # how long prior to start should offer be submitted
    tmp_start = (datetime.datetime.utcnow() + tmp_delay)
    for i in range(num_soffers):
        tmp_start = tmp_start + tmp_delay
        tmp_duration = datetime.timedelta(hours=2, minutes=0, seconds=0)  # How long service should run
        tmp_end = tmp_start + tmp_duration
        delay = tmp_delay.total_seconds()
        start = tmp_start.isoformat()
        end = tmp_end.isoformat()
        long_s.append({"delay": delay,
                        "start": start,
                        "end": end})

if __name__ == '__main__':
    cfg0 = Cfg()
    print(cfg0.input_list)

