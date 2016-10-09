#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016, EMC, Inc.

"""
This script is to do Secure Erase (SE) on a compute node
Four methods/tools are integrated in this scripts
A log file will be created for each disk to be erased named after disk name, like sdx.log
"""

import subprocess
import argparse
import time
import json

ARG_PARSER = argparse.ArgumentParser(description='RackHD secure-erase argument')

ARG_PARSER.add_argument("-i", action="store", type=str,
                        help="Disks to be erased with arguments")

ARG_PARSER.add_argument("-d", action="store", default=10, type=int,
                        help="Specify secure erase tool, "
                             "scrub, hdpram, sg_format, sg_sanitize are supported")


ARG_LIST = ARG_PARSER.parse_args()
TASK_ID = ARG_LIST.i
percentage = 1
payload = {"taskId": TASK_ID, "progress": {"percentage": "1%", "msg": "Secure erase started"}}

while 1:
    cmd = 'curl -X POST -H "Content-Type:application/json" -d \'{}\' http://172.31.128.1:9080/api/1.1/notification'.format(json.dumps(payload))
    subprocess.call(cmd, shell=True)
    output = subprocess.check_output("ps aux | grep secure_erase.py | sed \"/grep/d\"", shell=True)
    if not output:
        payload["percentage"] = "100%"
        payload["msg"] = "Secure erase finished"
        break
    percentage += 1
    payload["progress"]["percentage"] = str(percentage) + "%"
    payload["progress"]["msg"] = "This is the " + str(percentage) + "th poll, secure erase is running"
    time.sleep(ARG_LIST.d)
