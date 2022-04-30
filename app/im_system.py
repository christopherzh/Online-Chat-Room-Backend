from fastapi import FastAPI

import grpc
from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc

from im.im_model import *
from DB.redis_util import RedisController


class GrpcServiceRequester:
    def __init__(self):
        self.websocket_service_host, self.websocket_service_port = RedisController().get_service()

    def query_users_online(self, request: UserOnlineReq):
        with grpc.insecure_channel(self.websocket_service_host + ':' + self.websocket_service_port) as channel:
            # 通过通道服务一个服务
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = await stub.QueryUsersOnline(
                im_protobuf_pb2.QueryUsersOnlineReq(appId=request.app_id, userId=request.user_id))
            return response

    def get_user_list(self, request):
        with grpc.insecure_channel(self.websocket_service_host + ':' + self.websocket_service_port) as channel:
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = await stub.GetUserList(im_protobuf_pb2.GetUserListReq(appId=request.app_id))
            return response

    def send_msg(self, request: MsgToUserReq):
        with grpc.insecure_channel(self.websocket_service_host + ':' + self.websocket_service_port) as channel:
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = await stub.SendMsg(
                im_protobuf_pb2.SendMsgReq(seq=request.seq, appId=request.app_id, userId=request.user_id, cms='msg', type='text',
                                           msg=request.message, isLocal=False))
            return response

    def send_msg_all(self, request: MsgToAllReq):
        with grpc.insecure_channel(self.websocket_service_host + ':' + self.websocket_service_port) as channel:
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = await stub.SendMsgAll(
                im_protobuf_pb2.SendMsgAllReq(seq=request.seq, appId=request.app_id, userId=request.user_id, cms='msg', type='text',
                                           msg=request.message))
            return response


grpc_service_requester = GrpcServiceRequester()
app = FastAPI()


@app.get("/")
async def get_root():
    print("root")


@app.get("/home/index")
async def enter_room():
    # 前端返回不同appID页面
    pass


@app.get("user/online", response_model=UserOnlineResp)
async def check_online_user(request: UserOnlineReq):
    response = grpc_service_requester.query_users_online(request)
    return UserOnlineResp(code=response.retCode, msg=response.errMsg,
                          data=UserOnlineResp.Data(online=response.online, user_id=request.user_id))


@app.get("/user/list", response_model=UserListResp)
async def get_user_list(request: UserListReq):
    response = grpc_service_requester.get_user_list(request)
    return UserListResp(code=response.retCode, msg=response.errMsg,
                        data=UserListResp.Data(user_count=len(response.userId), user_list=response.userId))


@app.post("/user/sendMessage", response_model=MsgToUserResp)
async def send_message(request: MsgToUserReq):
    response = grpc_service_requester.send_msg(request)
    return MsgToUserResp(code=response.retCode, msg=response.errMsg,
                         data=MsgToUserResp.Data(send_results=(response.sendMsgId == 'True')))


@app.post("/user/sendMessageAll", response_model=MsgToAllResp)
async def send_message_all(request: MsgToAllReq):
    response = grpc_service_requester.send_msg_all(request)
    return MsgToUserResp(code=response.retCode, msg=response.errMsg,
                         data=MsgToUserResp.Data(send_results=(response.sendMsgId == 'True')))
