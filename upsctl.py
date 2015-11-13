#!/bin/env python3
"""A Simple ups monitor for the http://www.ayi9.com/zh/'s ups controller

Usage:
upsctl.py scan
upsctl.py list
upsctl.py stop <machine> <-all>
upsctl.py status <machine> <-all>
upsctl.py start <machine> <-all>

Options:
    -v            be Verbose
    -h --help     show this help
"""

import socket
import docopt
import logging
import os
import json

doc = None
configPath = "~/.config/smart_ups.json" if os.name == "nt" else "~/smart_ups.json"
configPath = os.path.expanduser(configPath)
config = {
    "machines": []
}
log = logging.getLogger()


def parse(byte):
    pass


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
        json.dump(config, fp)
        log.debug("Save Config to %s", configPath)


def _stop():
    raise NotImplementedError


def _scan():
    raise NotImplementedError


def _start():
    raise NotImplementedError


def _status():
    raise NotImplementedError


def _list():
    print("Found {} machins".format(len(config["machines"])))
    for i in config["machines"]:
        print(i['ip'])


def main():
    global doc
    doc = docopt.docopt(__doc__)
    for action in ["scan", "list", "stop", "status", "start"]:
        if doc[action]:
            load_config()
            globals()["_" + action]()
            save_config()
            return


if __name__ == '__main__':
    main()
