
import re
from pyparsing import *

__all__ = ["parse", "dump"]
def elemAction(i, t, ret):
    if len(ret) == 1:
        ret.append(True)
    return ret

def obj_like(i, t, ret):
    key = ret[::2]
    value = ret[1::2]
    return dict(zip(key, value))

obj = Forward()
elem_member = Word(alphanums + "@.\\ _").leaveWhitespace()
elem = elem_member + Optional(Suppress(":") + (elem_member | obj)) + Suppress(";")
elem.parseAction = [elemAction]
obj << Suppress("{") + ZeroOrMore(elem) + Suppress("}")
obj.parseAction = [obj_like]

def parse(text):
    if isinstance(text, bytes) or isinstance(text, bytearray):
        text = text.decode("ascii")
    return obj.parseString(text).asList()[0]

def dump(o):
    return _dump(o).encode("ascii")


def _dump(o):
    def conv(i, j):
        if isinstance(j, bool):
            return str(i) + ";"
        else:
            return str(i) + ":" + _dump(j) + ";"
    # o should be a dict
    if isinstance(o, dict):
        return "{" + ''.join([conv(k, v) for k, v in o.items()]) + "}"
    else:
        return str(o)