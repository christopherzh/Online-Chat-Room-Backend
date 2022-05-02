import grpc

from protobuf import im_protobuf_pb2_grpc, im_protobuf_pb2
from im.im_model import *


class GrpcServiceRequester:
    def __init__(self, redis_controller):
        self.redis_controller = redis_controller

    async def query_users_online(self, app_id: int, user_id: str):
        websocket_service = await self.redis_controller.get_single_service()
        with grpc.insecure_channel(websocket_service) as channel:
            # 通过通道服务一个服务
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = stub.QueryUsersOnline(
                im_protobuf_pb2.QueryUsersOnlineReq(appId=app_id, userId=user_id))
            return response

    async def get_user_list(self, app_id: int):
        res = True
        user_list: List[str] = []
        for service in await self.redis_controller.get_all_services():
            with grpc.insecure_channel(service) as channel:
                stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
                response = stub.GetUserList(im_protobuf_pb2.GetUserListReq(appId=app_id))
                res = res and (response.retCode == 200) and (response.errMsg == 'Success')
                user_list += response.userId
        print('当前房间user_list:', user_list)
        return res, user_list

    def send_msg(self, request: MsgToUserReq, cms: str, msg_type: str, is_local: bool, service: str):
        with grpc.insecure_channel(service) as channel:
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = stub.SendMsg(
                im_protobuf_pb2.SendMsgReq(seq=request.seq, appId=request.app_id, userId=request.user_id, cms=cms,
                                           type=msg_type,
                                           msg=request.message, isLocal=is_local))
            return response

    async def send_msg_all(self, request: MsgToAllReq, cms: str, msg_type: str, exclude_service: Optional[str] = None):
        res = True
        for service in await self.redis_controller.get_all_services():
            if service != exclude_service:
                with grpc.insecure_channel(service) as channel:
                    stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
                    response = stub.SendMsgAll(
                        im_protobuf_pb2.SendMsgAllReq(seq=request.seq, appId=request.app_id, userId=request.user_id,
                                                      cms=cms, type=msg_type,
                                                      msg=request.message))
                    res = res and (response.retCode == 200) and (response.errMsg == 'Success')

        return res
