# Smart UPS

最近买了一个国产的(长得很山寨的)UPS用来给寝室断电后供电, 让人好奇的是这个ups自带了一个ARM板,可以插网线并使用手机(安卓)进行控制.这个仓库包含了一些对 apk 逆向和 tcpdump 结果分析的脚本

## Contents

* scripts: 用于pc控制的python脚本.
* protocol.md: 协议分析

## Introduction

所有的消息交换通过 UDP 进行，ups的服务发现通过udp multicast实现。基本流程是

1.  手机客户端发送 multicast 包
    内容为 `headcall.device.lookup {type:UPS;}`
    返回 `headcall.device.report {type:UPS;uid:201412012578@ayi9.com;name:UPS;}`

    同时也可以见到参数为 uid 的multicast包，初步断定为用来寻找已知ups的ip以便于直接通讯

2.  进入客户端与ups单独通信阶段
    客户端发送hello包
    `{hello;ctag:bc0ab8b2;cseq:561a9cd4;cmagic:magicbc0ab8b2;to:201412012578@ayi9.com;}`
    ctag 似乎只是单纯的一个八位字符串。
    cseq 代表客户端发包的id，在返回包中也有这个参数
    cmagic 目前只为 'magic'+ ctag
    to uid

    成功的话
    `{ack:200\a OK;stag:8d15918a;hello;ctag:11111111;cseq:561a9cd4;cmagic:magic11111111;to:201412012578@ayi9.com;}`
    将原包加上 stag 和 ack 返回
    ack标示状态
    stag为session id， 需要包含在后续的会话中

3. 一些操作
a