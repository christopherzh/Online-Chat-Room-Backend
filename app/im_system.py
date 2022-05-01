from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


import grpc

from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc

from im.im_model import *
from DB.redis_util import RedisController


class GrpcServiceRequester:
    def __init__(self):
        self.redis_controller = RedisController()

    def query_users_online(self, app_id: int, user_id: str):
        websocket_service = self.redis_controller.get_single_service()
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
        print(res)
        print(user_list)
        if res:
            # return {'code':200,'msg':'Success','data':{'userCount':len(user_list),'userList':user_list}}
            return UserListResp(code=200, msg='Success',
                                data=UserListResp.Data(userCount=len(user_list), userList=user_list))
        else:
            return UserListResp(code=400, msg='Fail',
                                data=UserListResp.Data(userCount=0, userList=[]))

    def send_msg(self, request: MsgToUserReq):
        websocket_service = self.redis_controller.get_single_service()
        with grpc.insecure_channel(websocket_service) as channel:
            stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
            response = stub.SendMsg(
                im_protobuf_pb2.SendMsgReq(seq=request.seq, appId=request.app_id, userId=request.user_id, cms='msg',
                                           type='text',
                                           msg=request.message, isLocal=False))
            return response

    async def send_msg_all(self, request: MsgToAllReq):
        res = True
        for service in await self.redis_controller.get_all_services():
            with grpc.insecure_channel(service) as channel:
                stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
                response = stub.SendMsgAll(
                    im_protobuf_pb2.SendMsgAllReq(seq=request.seq, appId=request.app_id, userId=request.user_id,
                                                  cms='msg', type='text',
                                                  msg=request.message))
                res = res and (response.retCode == 200) and (response.errMsg == 'Success')
        if res:
            return MsgToAllResp(code=200, msg='Success',
                                data=MsgToAllResp.Data(sendResults=True))
        else:
            return MsgToAllResp(code=400, msg='Fail',
                                data=MsgToAllResp.Data(sendResults=False))


grpc_service_requester = GrpcServiceRequester()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_root():
    print("root")


@app.get("/home/index")
async def enter_room():
    # 前端返回不同appID页面
    pass


@app.get("user/online", response_model=UserOnlineResp)
async def check_online_user(appId: int, userId: str):
    response = grpc_service_requester.query_users_online(appId, userId)
    return UserOnlineResp(code=response.retCode, msg=response.errMsg,
                          data=UserOnlineResp.Data(online=response.online, userId=userId))


@app.get("/user/list", response_model=UserListResp)
async def get_user_list(appId: int):
    return await grpc_service_requester.get_user_list(appId)


@app.post("/user/sendMessage", response_model=MsgToUserResp)
async def send_message(request: MsgToUserReq):
    response = grpc_service_requester.send_msg(request)
    return MsgToUserResp(code=response.retCode, msg=response.errMsg,
                         data=MsgToUserResp.Data(sendResults=response.sendMsgId))


@app.post("/user/sendMessageAll", response_model=MsgToAllResp)
async def send_message_all(request: MsgToAllReq):
    return await grpc_service_requester.send_msg_all(request)
