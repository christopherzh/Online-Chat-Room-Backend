import asyncio
import signal
import time
from typing import Union, List

import grpc
from fastapi import FastAPI, WebSocketDisconnect
from grpc_reflection.v1alpha import reflection
from starlette.websockets import WebSocket

from DB import config
from DB.redis_util import RedisController
from protobuf import im_protobuf_pb2_grpc, im_protobuf_pb2
from ws.ws_model import *

redis_controller = RedisController()


class Singleton:
    def __init__(self, cls):
        self.__instance = {}
        self.__cls = cls

    def __call__(self):
        if self.__cls not in self.__instance:
            self.__instance[self.__cls] = self.__cls()
        return self.__instance[self.__cls]


# @Singleton
# class RoomManager:
#     def __init__(self):
#         self.room_dict = Dict[int, List[str]]
#
#     def add_room(self, app_id: str):
#         self.room_dict[app_id] = []
#
#     def del_room(self,app_id:str):
#         pass


def auth_user(token: str):
    return token


@Singleton
class UserConnectionManager:
    def __init__(self):
        self.user_dict: Dict[str, User] = {}
        self.room_dict: Dict[int, List[str]] = {}

    def get_user_list(self, app_id):
        pass

    async def connect_with_token(self, websocket: WebSocket, token: str):
        # 需要： 接受连接，验证用户身份
        await websocket.accept()
        print("接受连接")
        auth_result = auth_user(token)
        if auth_result is None:
            await websocket.close(code=1005)
            return None
        self.user_dict[auth_result] = User(user_id=auth_result, is_auth=True, is_login=False, ws=websocket)
        print('建立用户连接后,user_dict:',self.user_dict)
        return auth_result

    async def disconnect(self, user_id: str):
        print("删除用户map")

        if self.user_dict[user_id].is_login:
            await redis_controller.del_user(user_id)
            app_id = self.user_dict[user_id].user_info.app_id
            self.room_dict[app_id].remove(user_id)
            print('删除后room_map:', self.room_dict)

        if user_id in self.user_dict:
            self.user_dict.pop(user_id)
        print('删除后user_map:', self.user_dict)


        # 向所有房间内所有用户发送exit消息
        seq = str(time.time())
        await self.broadcast(seq, app_id, user_id, 'exit', 'text', "")
        res = True
        send_results = ''  # grpc服务返回 sendMsgId，内容为发送失败的用户列表
        for service in await redis_controller.get_all_services():
            # if True:
            if service != config.get_localhost() + ':' + config.get_grpc_port():
                with grpc.insecure_channel(service) as channel:
                    stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
                    response = stub.SendMsgAll(
                        im_protobuf_pb2.SendMsgAllReq(seq=seq + '-exit', appId=app_id, userId=user_id,
                                                      cms='exit', type='text',
                                                      msg=''))
                    res = res and (response.retCode == '200') and (response.errMsg == 'Success')

    async def disconnect_all_users(self):
        for user_id in self.user_dict:
            await self.disconnect(user_id)

    async def send_personal_msg(self, websocket: WebSocket, user_id: str, msg: str) -> bool:
        pass

    async def broadcast(self, seq: str, app_id: int, user_id: str, cms: str, type: str, msg: str) -> bool:
        for user in self.room_dict[app_id]:
            if user == user_id:
                pass
            else:
                await self.user_dict.get(user).ws.send_json(SendMsgToClient(seq=seq, cmd=cms,
                                                                            response=SendMsgToClient.Response(code=200,
                                                                                                              code_msg='Success',
                                                                                                              data=SendMsgToClient.Response.Data(
                                                                                                                  target='',
                                                                                                                  type=type,
                                                                                                                  msg=msg,
                                                                                                                  msg_from=user_id))).dict())
        return True

    # async def handle_login(self,json_data:LoginReq):
    #
    # async def handle_enter(self,json_data:SendMsgToClient):
    async def handle_login_msg(self, json_data: LoginReq):
        print('login_json:',json_data)
        user_id: str = json_data.data.user_id
        app_id: int = json_data.data.app_id
        self.user_dict[user_id].user_info = User.UserInfo(app_id=app_id)
        self.user_dict[user_id].is_login = True
        await redis_controller.add_user(user_id)
        print('登陆后user_dict',self.user_dict)

        if app_id not in self.room_dict:
            self.room_dict[app_id] = list()
        self.room_dict[app_id].append(user_id)
        print('登录后room_dict',self.room_dict)

        # 向所有房间内所有用户发送enter消息
        await self.broadcast(json_data.seq + '-enter', app_id, user_id, 'enter', 'text', "")
        res = True
        for service in await redis_controller.get_all_services():
            # if True:
            if service != config.get_localhost() + ':' + config.get_grpc_port():
                with grpc.insecure_channel(service) as channel:
                    stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
                    response = stub.SendMsgAll(
                        im_protobuf_pb2.SendMsgAllReq(seq=str(time.time()) + '-enter', appId=app_id, userId=user_id,
                                                      cms='enter', type='text',
                                                      msg=''))
                    res = res and (response.retCode == '200') and (response.errMsg == 'Success')



async def serve(user_connection_manager):
    # 实例化一个rpc服务，使用协程的方式启动我们的服务
    service_names = (
        im_protobuf_pb2.DESCRIPTOR.services_by_name["WebsocketServer"].full_name,
        reflection.SERVICE_NAME,
    )
    server = grpc.aio.server()
    # 添加我们服务
    im_protobuf_pb2_grpc.add_WebsocketServerServicer_to_server(WebsocketServer(user_connection_manager), server)
    reflection.enable_server_reflection(service_names, server)
    # 配置启动的端口
    server.add_insecure_port('[::]:' + config.get_grpc_port())
    await server.start()
    await server.wait_for_termination()


app = FastAPI()
user_conn_manager = UserConnectionManager()


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    def __init__(self, user_connection_manager:UserConnectionManager):
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



@app.on_event('startup')
async def on_startup():
    asyncio.get_event_loop().create_task(serve(user_conn_manager))
    await redis_controller.register_service()
    print('服务启动')


@app.on_event("shutdown")
async def on_shutdown_event():
    await redis_controller.unregister_service()
    print('服务关停')


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    connect_result = await user_conn_manager.connect_with_token(websocket, token)
    if connect_result is not None:
        try:
            while True:
                json_data = await websocket.receive_json()
                if json_data['cmd'] == 'login':
                    await user_conn_manager.handle_login_msg(LoginReq(**json_data))
                elif json_data['cmd'] == 'heartbeat':
                    print('heartbeat')
                elif json_data['cmd'] == 'ping':
                    print('ping')

        except WebSocketDisconnect:
            await user_conn_manager.disconnect(connect_result)
