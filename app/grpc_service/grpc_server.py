import grpc
from grpc_reflection.v1alpha import reflection

from DB import config
from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    def __init__(self, user_connection_manager):
        self.user_conn_manager = user_connection_manager

    async def QueryUsersOnline(self, request, context):
        res: bool = await self.user_conn_manager.query_user_online(request.appId, request.userId)
        # TODO: 业务逻辑待优化，目前为若查询不到用户就返回不在线，应考虑用户不存在（不在数据库）的问题
        if res:
            return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=res)
        else:
            return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=res)

    async def SendMsg(self, request, context):
        res: bool = await self.user_conn_manager.send_personal_msg(request.seq, request.appId, request.userId,
                                                                   request.cms,
                                                                   request.type, request.msg, request.isLocal)
        if res:
            return im_protobuf_pb2.SendMsgRsp(retCode=200, errMsg='Success', sendMsgId=request.seq)
        else:
            return im_protobuf_pb2.SendMsgRsp(retCode=404, errMsg='用户不存在', sendMsgId=request.seq)

    async def SendMsgAll(self, request, context):
        res: bool = await self.user_conn_manager.broadcast(request.seq, request.appId, request.userId, request.cms,
                                                           request.type,
                                                           request.msg)
        if res:
            return im_protobuf_pb2.SendMsgAllRsp(retCode=200, errMsg='Success', sendMsgId=request.seq)
        # TODO: 目前不会返回错误信息
        else:
            return im_protobuf_pb2.SendMsgAllRsp(retCode=404, errMsg='Fail', sendMsgId=request.seq)

    def GetUserList(self, request, context):
        res = self.user_conn_manager.get_user_list(request.appId)
        # TODO: 待错误处理
        return im_protobuf_pb2.GetUserListRsp(retCode=200, errMsg='Success', userId=res)


async def serve(user_connection_manager):
    # 实例化一个rpc服务，使用协程的方式启动我们的服务
    service_names = (
        im_protobuf_pb2.DESCRIPTOR.services_by_name["WebsocketServer"].full_name,
        reflection.SERVICE_NAME,
    )
    server = grpc.aio.server()
    im_protobuf_pb2_grpc.add_WebsocketServerServicer_to_server(WebsocketServer(user_connection_manager), server)
    reflection.enable_server_reflection(service_names, server)
    # 配置启动的端口
    server.add_insecure_port('[::]:' + config.get_grpc_port())
    await server.start()

    # since server.start() will not block,
    # a sleep-loop is added to keep alive
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(None)
