#!/usr/bin/evn python
# coding=utf-8
import asyncio
from typing import List

import grpc
from protobuf import im_protobuf_pb2
from protobuf import im_protobuf_pb2_grpc
from im.im_model import *
from DB.redis_util import RedisController

def run():
    # 连接 rpc 服务器
    with grpc.insecure_channel('101.43.149.3:50051') as channel:
        # 通过通道服务一个服务
        stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
        # 生成请求我们的服务的函数的时候，需要传递的参数体，它放在hello_pb2里面-请求体为：hello_pb2.HelloRequest对象
        response = stub.QueryUsersOnline(im_protobuf_pb2.QueryUsersOnlineReq(appId=613, userId='zzh'))
        return {'reply',"QueryUsersOnline" + str(response.retCode)}

async def run1():
    res = True
    user_list: List[str] = []
    # for service in await RedisController().get_all_services():
    with grpc.insecure_channel(await RedisController().get_single_service()) as channel:
        stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
        response = stub.GetUserList(im_protobuf_pb2.GetUserListReq(appId=101))
        print(response)
        user_list += response.userId

if __name__ == '__main__':
    # asyncio.run(run1())
    print(run())
