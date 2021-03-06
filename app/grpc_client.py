#!/usr/bin/evn python
# coding=utf-8

import grpc
from protobuf import im_protobuf_pb2
from protobuf import im_protobuf_pb2_grpc


def run():
    # 连接 rpc 服务器
    with grpc.insecure_channel('localhost:50051') as channel:
        # 通过通道服务一个服务
        stub = im_protobuf_pb2_grpc.AccServerStub(channel)
        # 生成请求我们的服务的函数的时候，需要传递的参数体，它放在hello_pb2里面-请求体为：hello_pb2.HelloRequest对象
        response = stub.QueryUsersOnline(im_protobuf_pb2.QueryUsersOnlineReq(appId=613, userId='zzh'))
        return {'reply',"QueryUsersOnline" + str(response.retCode)}


if __name__ == '__main__':
    print(run())
