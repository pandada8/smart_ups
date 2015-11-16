#!/bin/env python3
"""A Simple ups monitor for the http://www.ayi9.com/zh/'s ups controller

Usage:
upsctl.py scan [-v]
upsctl.py list [-v]
upsctl.py login [-v]
upsctl.py stop [machine] ... [--all] [-v]
upsctl.py status [machine] ... [--all] [-v]
upsctl.py start [machine] ... [--all] [-v]
upsctl.py internel [-v]


Options:
    -v            be Verbose
    -h, --help    show this help

"""

import socket
import docopt
import threading
import logging
import os
import json
import time
from parse import parse, dump
import random
import string
from uuid import getnode as get_mac

opt = None
configPath = "~/smart_ups.json" if os.name == "nt" else "~/.config/smart_ups.json"
configPath = os.path.expanduser(configPath)
config = {
    "machines": {}
}
log = logging.getLogger()


def random_string(length=8):
    return "".join([random.choice(string.hexdigits[:16]) for i in range(length)])


def add_number(s):
    return "{:08x}".format((int(s, 16) + 1) % 0x100000000)


def seq(machine):
    if machine.get("cseq"):
        machine['cseq'] = add_number(machine["cseq"])
    else:
        machine["cseq"] = add_number("0")
    return machine["cseq"]

def split_string(s, step):
    i = 0
    for i in range(0, len(s), 2):
        yield s[i:i+2]


def _login():
    mac = hex(get_mac())[2:]
    machine = "ups_" + "_".join(split_string(mac, 2))
    payload = {
        "msgno": int(time.time()),
        "title": "login",
        "from": machine,
        "timeout": 150
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    sock.connect(("59.56.64.74", 6600))
    sock.send(dump(payload))
    ret = parse(sock.recv(1024))
    print(ret)

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

    if not config.get("ctag"):
        config["ctag"] = random_string()



def save_config():
    with open(configPath, "w") as fp:
        json.dump(config, fp, indent=4, ensure_ascii=False)
        log.debug("Save Config to %s", configPath)


def get_machines():
    global config, opt
    if '--all' in config:
        return config["machines"].values()
    else:
        ret = []
        machines = {m['uid']: m for m in config['machines']}
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
        sock.settimeout(2)
        start = time.time()
        while time.time() - start < 10:
            try:
                payload, ip = sock.recvfrom(1024)
                ip, _ = ip
                _, payload = payload.split(b" ", 1)
                uid = parse(payload)["uid"]
                result[uid] = {
                    "ip": ip,
                    "uid": uid
                }
            except socket.timeout:
                break

    # Start a new Thread to run the listener
    t = threading.Thread(target=finding, args=(sock, ))
    t.start()
    while t.is_alive():
        font = r"-\|/"[int(time.time()*20)%4]
        print("\rScanning {}".format(font), end="")
        time.sleep(0.05)
    config["machines"] = result
    print("\rFinish scanning")
    print("Found {} ups".format(len(result)))

    print("Connecting...")
    for _, j in config["machines"].items():
        payload = {
            "hello": True,
            "ctag": config["ctag"],
            "cseq": hex(int(time.time()))[2:],
            "cmagic": "magic"+config["ctag"],
            "to": j['uid']
        }
        sock.sendto(dump(payload), (j['ip'], 9600))
    for i in range(len(config['machines'])):
        payload, ip = sock.recvfrom(1024)
        payload = parse(payload)
        if payload['ack'].startswith("200"):
            uid = payload['to']
            config['machines'][uid]['stag'] = payload['stag']
            config['machines'][uid]["cseq"] = payload["cseq"]
            print("Connect to {} successfully".format(ip[0]))
    sock.close()

def _start():
    raise NotImplementedError


def _status():
    if "--all" not in config and "<machine>" not in config:
        config["--all"] = True
    machines = get_machines()
    for i in machines:
        if not i.get("stag"):
            print("{uid} doesn't have a stag".format(**i))
            continue
        print("{uid} ({ip} {stag})".format(**i))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.connect((i['ip'], 9600))
        payload = {
            "stag": i["stag"],
            "ctag": config['ctag'],
            "cseq": seq(i),
            "data": {
                "ups_command": "QS"
            },
        }
        # print(payload)
        sock.send(dump(payload))
        ret = parse(sock.recv(1024))
        # print(ret)
        v_in, _, v_out, _, _, v_bat, _, _ = ret["data"]["ups_answer"][1:].split("\\ ")
        print("In: {}V  Out: {}V  Bat: {}V".format(v_in, v_out, v_bat))
        sock.close()

def _list():
    nums = len(config["machines"])
    if nums == 0:
        print("No Machine")
        return
    print("Found {} machines\n".format(nums))
    print("IP\t\t\tstag\t\tMachine UID")
    for i, j in config["machines"].items():
        data = j.copy()
        if not data.get('stag'):
            data['stag'] = None
        print("{ip}\t\t{stag}\t{uid}".format(**data))

def _internel():
    import pprint
    print("The Config")
    print("Location", configPath)
    pprint.pprint(config)

def main():
    global opt
    opt = docopt.docopt(__doc__)
    if "-v" in opt:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    for action in ["scan", "list", "stop", "status", "start", "internel", "login"]:
        if opt[action]:
            load_config()
            globals()["_" + action]()
            save_config()
            return
    print(__doc__)
    return


if __name__ == '__main__':
    main()
