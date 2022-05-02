import asyncio
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from DB import config
from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc
from ws.user_conn_manager import user_conn_manager, UserConnectionManager


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    def __init__(self, user_connection_manager: UserConnectionManager):
        self.user_conn_manager = user_connection_manager

    def QueryUsersOnline(self, request, context):
        return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=True)

    def SendMsg(self, request, context):
        pass
        # return im_protobuf_pb2.SendMsgRsp()

    async def SendMsgAll(self, request, context):
        res = await self.user_conn_manager.broadcast(request.seq, request.appId, request.userId, request.cms,
                                                     request.type,
                                                     request.msg)
        if res:
            return im_protobuf_pb2.SendMsgAllRsp(retCode=200, errMsg='Success', sendMsgId='')
        else:
            return im_protobuf_pb2.SendMsgAllRsp(retCode=400, errMsg='Fail', sendMsgId='')

    def GetUserList(self, request, context):
        res = self.user_conn_manager.room_dict[request.appId]
        return im_protobuf_pb2.GetUserListRsp(retCode=200, errMsg='Success', userId=res)


async def serve(user_connection_manager):
    # 实例化一个rpc服务，使用协程的方式启动我们的服务
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_names = (
        im_protobuf_pb2.DESCRIPTOR.services_by_name["WebsocketServer"].full_name,
        reflection.SERVICE_NAME,
    )
    server = grpc.aio.server()
    # 添加我们服务
    # server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=40), options=[
    #     ('grpc.so_reuseport', 0),
    #     ('grpc.max_send_message_length', 100 * 1024 * 1024),
    #     ('grpc.max_receive_message_length', 100 * 1024 * 1024),
    #     ('grpc.enable_retries', 1),
    # ])
    im_protobuf_pb2_grpc.add_WebsocketServerServicer_to_server(WebsocketServer(user_connection_manager), server)
    reflection.enable_server_reflection(service_names, server)
    # 配置启动的端口
    await server.start()

    # since server.start() will not block,
    # a sleep-loop is added to keep alive
    try:
        print('wait!!!')
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(None)

if __name__ == '__main__':
    asyncio.run(serve(user_conn_manager))