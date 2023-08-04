# SPDX-License-Identifier: GPL-3.0+
# Copyright (C) 2020 nlscc

import argparse
import os
import base64
import xml.etree.ElementTree as ET
from tqdm import tqdm

from . import request
from . import crypt
from . import fusclient
from . import versionfetch

def main():
    client = fusclient.FUSClient()
    subfolders = [ f.path for f in os.scandir(".") if f.is_dir() and "-" in f.name ]
    latest = ""
    latest_csc = ""
    latest_date = "0"
    for subfolder in subfolders:
        fw_list = []
        fw_list_mm = []
        fw_list_nn = []
        cache_fw = "sadfasd"
        info = open(subfolder + "/csc.txt", "r+")
        for line in info.read().splitlines():
            try:
                csc = line.split("csc: ")[1].split(" fw_version:")[0]
                old_fw_version = line.split("fw_version: ")[1].split(" os_version:")[0]
            except:
                csc = line
                old_fw_version = "A"
            cache_fw = old_fw_version
            path, filename, size, fw_version, os_version = getbinaryfile(client, old_fw_version, subfolder[2:], csc)
            # garbage error handle
            if old_fw_version != fw_version:
                for str in filename.split("_"):
                    if len(str) == 14:
                        build_date = str
                        break
                if int(build_date) > int(latest_date):
                    latest = fw_version
                    latest_csc = csc
                    latest_date = build_date
                fw_list.append("csc: " + csc + " fw_version: " + fw_version + " os_version: " + os_version + " build_date: " + build_date)
                if "6." in os_version:
                    fw_list_mm.append("csc: " + csc + " fw_version: " + fw_version + " os_version: " + os_version + " build_date: " + build_date)
                if "7." in os_version:
                    fw_list_nn.append("csc: " + csc + " fw_version: " + fw_version + " os_version: " + os_version + " build_date: " + build_date)
        info.seek(0)
        info.truncate()
        info.write("\n".join(fw_list))
        info.close()
        if fw_list:
            latest_fw = sorted(fw_list, key=lambda x:x[-14:None])[-1]
        f = open(subfolder + "/available", "w")
        f.write(latest_fw.split("fw_version: ")[1].split(" os_version:")[0] + "\n" + latest_fw.split("csc: ")[1].split(" fw_version:")[0] + "\n" + latest_fw.split("build_date: ")[1])
        f.close()
        if fw_list_mm:
            latest_fw_mm = sorted(fw_list_mm, key=lambda x:x[-14:None])[-1]
            f = open(subfolder + "/available_mm", "w")
            
            f.write(latest_fw_mm.split("fw_version: ")[1].split(" os_version:")[0] + "\n" + latest_fw_mm.split("csc: ")[1].split(" fw_version:")[0] + "\n" + latest_fw_mm.split("build_date: ")[1])
            f.close()
        if fw_list_nn:
            latest_fw_nn = sorted(fw_list_nn, key=lambda x:x[-14:None])[-1]
            f = open(subfolder + "/available_nn", "w")
            f.write(latest_fw_nn.split("fw_version: ")[1].split(" os_version:")[0] + "\n" + latest_fw_nn.split("csc: ")[1].split(" fw_version:")[0] + "\n" + latest_fw_nn.split("build_date: ")[1])
            f.close()
    f = open("latest", "w")
    f.write(latest + "\n" + latest_csc + "\n" + latest_date)
    f.close()

def initdownload(client, filename):
    req = request.binaryinit(filename, client.nonce)
    resp = client.makereq("NF_DownloadBinaryInitForMass.do", req)

def getbinaryfile(client, fw, model, region):
    req = request.binaryinform(fw, model, region, client.nonce)
    resp = client.makereq("NF_DownloadBinaryInform.do", req)
    root = ET.fromstring(resp)
    status = int(root.find("./FUSBody/Results/Status").text)
    if status == 200:
        filename = root.find("./FUSBody/Put/BINARY_NAME/Data").text
        if filename is None:
            raise Exception("DownloadBinaryInform failed to find a firmware bundle")
        size = int(root.find("./FUSBody/Put/BINARY_BYTE_SIZE/Data").text)
        path = root.find("./FUSBody/Put/MODEL_PATH/Data").text
        # ADD_LATEST_FW_VERSION, ADD_LATEST_DISPLAY_VERSION -> latest u can get by clicking update in phone while having "old_vc"
        # CURRENT_DISPLAY_VERSION -> fw we pinged with
        # LATEST_DISPLAY_VERSION -> newest firmware, same as LATEST_FW_VERSION ???
        fw_version = root.find("./FUSBody/Results/LATEST_FW_VERSION/Data").text
        os_version = root.find("./FUSBody/Put/LATEST_OS_VERSION/Data").text
    else:
        print(model + " " + region)
        path = "asdf"
        filename = "asdf"
        size = 0
        fw_version = fw
        os_version = "6"
    return path, filename, size, fw_version, os_version
