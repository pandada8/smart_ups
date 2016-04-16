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
upsctl.py mute [-v]


Options:
    -v            be Verbose
    -h, --help    show this help

"""
import docopt
import protocol
import socket
import threading
import pprint
import logging
import os
import json
import time
import warnings
import random
import functools
import string
from uuid import getnode as get_mac

opt = None
configPath = "~/smart_ups.json" if os.name == "nt" else "~/.config/smart_ups.json"
configPath = os.path.expanduser(configPath)
config = {
    "machines": {}
}

logging.basicConfig(level=logging.DEBUG)

def random_string(length=8):
    return "".join([random.choice(string.hexdigits[:16]) for i in range(length)])

ctag = hex(get_mac())[2:]

class Machine:

    def __init__(self, ip=None, data=None):
        if ip:
            self.ip = ip
        elif data:
            self._load(data)
        else:
            self.ip = None
            warnings.warn("you should provide ip or data for a machine", UserWarning)
        self.logger = logging.getLogger("Machine<{}>".format(self.ip))
        self.sock = None
        self.cseq = None
        self.stag = None

    def __str__(self):
        return "<Machine: {ip}, stag: {stag}, uid: {uid}>".format_map(self)

    def _load(self, data):
        for i in ['ip', 'cseq', 'uid', 'stag']:
            self.__setattr__(i, data[i])

    def get_ctag(self):
        return ctag

    def prepare_sock(self):
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.connect((self.ip, 9600))

    def get_cseq(self):
        if self.cseq:
            self.cseq = "{:08x}".format((int(self.cseq, 16) + 1) % 0x100000000)
        else:
            self.cseq = random_string()
        return self.cseq

    def send_payload(self, data, noack=False):
        self.prepare_sock()
        encoded_payload = protocol.dump(data)
        tried = 0
        while tried < 3:
            try:
                tried += 1
                self.sock.send(encoded_payload)
                self.logger.debug("Sendto {}: {}".format(self.ip, encoded_payload))
                if noack:
                    return
                recv = self.sock.recv(1024)
                self.logger.debug("Recv   {}: {}".format(self.ip, recv))
                answer = protocol.load(recv)
                # TODO: check status
                return answer
            except Exception as e:
                print(e)
                # self.connect()  # FIXME
                continue
        raise Exception("Fail to connect to server")

    def status(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "QS"
            },
        }
        ret = self.send_payload(payload)["data"]["ups_answer"][1:].split("\\ ")
        status = {
            "input": float(ret[0]),
            "output": float(ret[2]),
            "freq": float(ret[4]),
            "load": int(ret[3], 10) / 100,
            "bat": float(ret[5]),
            "flags": ret[7],
            "bat_mode": ret[7][0] == '1',
            "bypass_mode": ret[7][2] == '1',
            "fault": ret[7][3] == '1',
            "test_mode": ret[7][5] == '1',
            "beep": ret[7][7] == '1'
        }
        pprint.pprint(status)
        return status

    def mute(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "Q",
                "noack": True
            },
        }
        self.send_payload(payload, noac=True)
        self.status()

    def unmute(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "BZON"
            },
        }
        self.send_payload(payload)
        self.status()

    def shutdown(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "S02R9999",
                "noack": True
            },
        }
        self.send_payload(payload, noack=True)

    def poweron(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "SON",
                "noack": True
            },
        }

    def test(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),

        }

    def auth(self):
        # this function should run in case we have known the ip and don't know other info
        self.prepare_sock()
        self.sock.send(b"headcall.device.lookup {type:UPS;}")
        ret = self.sock.recv(1024)
        answer = protocol.load(ret.split(b" ")[1])
        self.uid = answer["uid"]
        self.logger.info("Got Echo from {}:{}".format(self.ip, self.uid))
        payload = {
            "hello": True,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "cmagic": "magic"+self.get_ctag(),
            "to": self.uid
        }
        ret = self.send_payload(payload)
        if '200' in ret["ack"]:
            self.stag = ret["stag"]

    def test(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "T",
                "noack": True,
            },
        }
        self.send_payload(payload)

    def cancel_shutdown(self):
        payload = {
            "stag": self.stag,
            "ctag": self.get_ctag(),
            "cseq": self.get_cseq(),
            "data": {
                "ups_command": "C",
                "noack": True,
            },
        }
        self.send_payload(payload, noack=True)


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


def main():
    global opt
    opt = docopt.docopt(__doc__)
    if "-v" in opt:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    for action in ["scan", "list", "stop", "status", "start", "internel", "login", "mute"]:
        if opt[action]:
            load_config()
            globals()["_" + action]()
            save_config()
            return
    print(__doc__)
    return



if __name__ == '__main__':
    m = Machine(ip="192.168.2.198")
    m.auth()
    m.status()
