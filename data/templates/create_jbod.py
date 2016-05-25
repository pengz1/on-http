#!/usr/bin/env python

# Copyright 2015, EMC, Inc.

'''
This script is to delete RAID and create JBOD for each physical disk of a virtual disk with RAID
'''
import subprocess
import argparse
import json
import re
import time
from os import path as path

ARG_PARSER = argparse.ArgumentParser(description=
                                     'delete virtual disk and create JBODs for physical disks')
ARG_PARSER.add_argument("-d", action="append", default=[], type=str, help="Create JBOD")
ARG_PARSER.add_argument("-v", action="store", default="lsi", type=str,
                        help="Identify RAID controller vendor")
ARG_LIST = ARG_PARSER.parse_args()
RAID_VENDOR_LIST = ["lsi", "dell"]  ##RackHD supported RAID controller vendor list

def create_jbod(disk, tool):
    '''
    Create JBOD for each physical disk under a virtual disk.
    :param disk: a dictionary contains disk argument
    :param tool: tools used for JBOD creation, storcli and perccli are supported
    :return: a list contains disk OS names, like ["/dev/sda", "/dev/sdb", ...]
    '''
    for slot_id in disk["sid"]:
        cmd = [tool, slot_id, "set", "jbod"]
        exit_code = subprocess.call(cmd, shell=False)
        assert exit_code == 0, "Can't create JBOD for drive " + slot_id
    time.sleep(1)  #Wait 1 second for OS to scan new drives
    disk_list = []
    scsi_id_bits = disk["scsi"].split(":")
    #map jbod to disk device name with JBOD
    for did in disk["did"]:
        #scsi id is used to map virtual disk to new JBOD
        #scsi id is made up of adapter:scsi:dev:lun as below:
        #   adapter id [host]: controller ID, ascending from 0.
        #       Usually c0 for one controller in server Megaraid info
        #   scsi id [bus]: a number of 0-7 or 0-15.
        #       Usually different for RAID(like 2) and JBOD(like 0)
        #   device id [target]: displayed as DID in Megaraid for each physical drives.
        #   LUN id [LUN]: Logic Unit Numbers, LUN is not used for drive mapping
        scsi_info = scsi_id_bits[:]
        scsi_info[2] = str(did)
        anti_patten = re.compile(":".join(scsi_info[0:3]))  #anti-patten to exclude scsi id for RAID
        scsi_info[1] = '[0-9]*'
        patten = re.compile(":".join(scsi_info[0:3]))
        cmd = ["ls", "-l", "/dev/disk/by-path"]
        lines = subprocess.check_output(cmd, shell=False).split("\n")
        #example for "ls -l /dev/disk/by-path" console output
        #   total 0
        #   drwxr-xr-x 2 root root 300 May 19 03:15 ./
        #   drwxr-xr-x 5 root root 100 May 16 04:43 ../
        #   lrwxrwxrwx 1 root root   9 May 19 03:06 pci-0000:06:00.0-scsi-0:2:0:0 -> ../../sdf
        #   lrwxrwxrwx 1 root root  10 May 19 03:06 pci-0000:06:00.0-scsi-0:2:0:0-part1 -> ../../sdf1
        #   lrwxrwxrwx 1 root root  10 May 19 02:31 pci-0000:06:00.0-scsi-0:2:1:0 -> ../../sda
        disk_name = ''
        for line in lines:
            if patten.search(line) and not anti_patten.search(line) and line.find("part") == -1:
            #lines contain part is partition info
                disk_name = line.split("/")[-1]
        assert disk_name, "Disk OS name is not found for did " + str(did)
        disk_list.append("/dev/" + disk_name)
    return disk_list

if __name__ == '__main__':

    disk_argument_list = []
    #ARG_LIST.d should include at least following items as a string
    #   {
    #   "devName": "/dev/sdx"
    #   "sid": "/c0/e252/sx"
    #   "did": "0"
    #   "vd": "/c0/vx"
    #   "scsi": "0:0:0"
    #   }
    for argu in ARG_LIST.d:
        disk_argument_list.append(json.loads(argu))
    assert disk_argument_list != [], "no disk arguments includes"

    #Idenfity tools used for raid operation
    raid_controller_vendor = ARG_LIST.v
    assert raid_controller_vendor in RAID_VENDOR_LIST, "RAID controller vendor info is invalid"
    if raid_controller_vendor == "lsi":
        tool_path = "/opt/MegaRAID/storcli/storcli64"
    else:
        tool_path = "/opt/MegaRAID/perccli/perccli64"
    assert path.exists(tool_path), "Overlay doesn't include tool path: " + tool_path

    disk_list_with_jbod = []
    for disk_argument in disk_argument_list:
        #if vd doesn't exit, push disk directly into disk list
        if not disk_argument["vd"]:
            disk_list_with_jbod.append(disk_argument["diskName"])
        else:
            command = [tool_path, "/c0", "set", "jbod=on"]
            exit_status = subprocess.call(command, shell=False)
            assert exit_status == 0, "Failed to enable jbod"
            command = [tool_path, disk_argument["vd"], "del", "force"]
            #force option will delete MBR and other items
            exit_status = subprocess.call(command, shell=False)
            assert exit_status == 0, "Failed to run delete raid commands"
            disk_list_with_jbod = disk_list_with_jbod + create_jbod(disk_argument, tool_path)
    print disk_list_with_jbod

