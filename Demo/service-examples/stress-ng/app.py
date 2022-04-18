import random
import multiprocessing
from subprocess import PIPE, run
import sys
import time


def run_app(input_msg):
    cpucount = multiprocessing.cpu_count()
    max_executions = 1
    i = 0

    msgnum = input_msg.msgnum

    while True:
        cores = random.randrange(1, cpucount)
        timemeasure = random.randrange(1, 2)  # 1 to 2 second
        vmsize = random.randrange(10, 200)  # 10M to 200M
        command = f'stress-ng --cpu {cores} --timeout {timemeasure} --vm 1 --vm-bytes {vmsize}M'
        commandlist = command.split()
        print(f'running {command}, msgnum: {msgnum}, execution:{i}')
        sys.stdout.flush()
        result = run(commandlist, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        print(result.returncode, result.stdout, result.stderr)
        sys.stdout.flush()
        sleepvalue = random.randrange(1, 2)  # sleep for 1 to 2 second
        print(f'sleeping for {sleepvalue}')
        sys.stdout.flush()
        time.sleep(sleepvalue)
        i = i+1
        if i >= max_executions:
            break

    output = input_msg.value * 2

    return output
