import socket
import ast
import re
from pprint import pprint as print


def parse(s):
    s = s.decode("ascii") if isinstance(s, bytes) else s
    return ast.literal_eval(re.sub(r"([\w\.\\\s]+)", r'"\1"', s.replace("\\", "\\\\")).replace(";", ","))


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
s.sendto(b'headcall.device.lookup {type:UPS;}', ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'headcall.device.lookup {uid:201412012578@ayi9.com;}',  ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b"{hello;ctag:11111111;cseq:561a9cd4;cmagic:magic11111111;to:201412012578@ayi9.com;}", ("192.168.2.199", 9600))
sid = parse(s.recv(1024))
print(sid)
sid = sid["stag"].encode("ascii")
s.sendto(b'{stag:{};ctag:11111111;cseq:561a9cd5;data:{get_version;};}'.format(sid), ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'{stag:{};ctag:11111111;cseq:561a9cd6;data:{set_msgs:{server:msg.ayi9.com;title:ups;pass:sajdhfbwbfkdhysgevflsdhshvdlkx;device:ups_fc_64_ba_57_a3_b0;};};}'.format(sid), ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'{stag:{};ctag:11111111;cseq:561a9cd7;data:{get_config:{name;network;};};}'.format(sid), ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'{stag:{};ctag:11111111;cseq:561a9cd8;data:{ups_command:S03R9999;noack;};}'.format(sid), ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'{stag:{};ctag:11111111;cseq:561a9cd9;data:{ups_command:C;noack;};}'.format(sid), ("192.168.2.199", 9600))
print(s.recv(1024))
s.sendto(b'{stag:{};ctag:d7763194;cseq:561a9cda;data:{ups_command:QS;};}'.format(sid),  ("192.168.2.199", 9600))
print(s.recv(1024))



