#!/bin/env python3
"""A Simple ups monitor for the http://www.ayi9.com/zh/'s ups controller

Usage:
upsctl.py scan
upsctl.py list
upsctl.py stop <machine>... <-all>
upsctl.py status <machine>... <-all>
upsctl.py start <machine>... <-all>

Options:
    -v            be Verbose
    -h --help     show this help
"""

import socket
import docopt
import threading
import logging
import os
import json
import time
from parse import parse, dump

opt = None
configPath = "~/.config/smart_ups.json" if os.name == "nt" else "~/smart_ups.json"
configPath = os.path.expanduser(configPath)
config = {
    "machines": []
}
log = logging.getLogger()


def load_config():
    global config
    if os.path.exists(configPath):
        with open(configPath) as fp:
            log.debug("Load config from %s", configPath)
            try:
                config = json.load(fp)
            except:
                print("Fail to load the config, please check the config file")
                raise SystemError
    else:
        log.debug("Not Found config file, %s", configPath)


def save_config():
    with open(configPath, "w") as fp:
        json.dump(config, fp, indent=4, ensure_ascii=False)
        log.debug("Save Config to %s", configPath)


def get_machines():
    global config, opt
    if opt['--all']:
        return config["machines"]
    else:
        ret = []
        machines = {m['ip']: m for m in config['machines']}
        for i in opt["<machine>"]:
            if i in machines:
                ret.append(machines)
            else:
                print("Can't find {}".format(i))
        return ret

def _stop():
    raise NotImplementedError


def _scan():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(b'headcall.device.lookup {type:UPS;}', ("255.255.255.255", 9600))
    t = time.time()
    sock.settimeout(1)
    result = {}
    def finding(sock):
        sock.settimeout(10)
        start = time.time()
        while time.time() - start < 10:
            try:
                payload, ip = sock.recvfrom(1024)
                ip, _ = ip
                _, payload = payload.split(b" ", 1)
                uid = parse(payload)["uid"]
                result[ip] = {
                    "ip": ip,
                    "uid": uid
                }
            except socket.timeout:
                break

    # Start a new Thread to run the listener
    t = threading.Thread(target=finding, args=(sock, ))
    t.start()
    while t.is_alive():
        font = r"-\|/"[int(time.time()*10)%4]
        print("\rScanning {}".format(font), end="")
        time.sleep(0.1)
    config["machines"] = result
    print("\rFinish scanning")
    print("Found {} ups".format(len(result)))






def _start():
    raise NotImplementedError


def _status():
    raise NotImplementedError


def _list():
    nums = len(config["machines"])
    if nums == 0:
        print("No Machine")
        return
    print("Found {} machines\n".format(nums))
    print("IP\t\t\tMachine UID")
    for i, j in config["machines"].items():
        print("{ip}\t\t{uid}".format(**j))


def main():
    global opt
    opt = docopt.docopt(__doc__)
    if "-v" in opt:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    for action in ["scan", "list", "stop", "status", "start"]:
        if opt[action]:
            load_config()
            globals()["_" + action]()
            save_config()
            return


if __name__ == '__main__':
    main()
