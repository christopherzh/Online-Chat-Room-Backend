import asyncio
import signal
import time
from typing import Union

import grpc
from fastapi import FastAPI, WebSocketDisconnect
from grpc_reflection.v1alpha import reflection
from starlette.websockets import WebSocket

from DB import config
from DB.redis_util import RedisController
from protobuf import im_protobuf_pb2_grpc, im_protobuf_pb2
from ws.ws_model import *


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
    return '马远'


@Singleton
class UserConnectionManager:
    def __init__(self):
        self.user_dict: Dict[str, User] = {}
        self.room_dict: Dict[int, str] = {}

    async def connect_with_token(self, websocket: WebSocket, token: str):
        # 需要： 接受连接，验证用户身份
        await websocket.accept()
        print("接受连接")
        auth_result = auth_user(token)
        if auth_result is None:
            await websocket.close(code=1005)
            return None
        self.user_dict[auth_result] = User(user_id=auth_result, is_auth=True, is_login=False)
        await redis_controller.add_user(auth_result)
        print(self.user_dict)
        return auth_result

    async def disconnect(self, user_id: str):
        print("删除用户map")
        if user_id in self.user_dict:
            self.user_dict.pop(user_id)
        # else:
        #     raise KeyError('User ID does not exist!')
        await redis_controller.del_user(user_id)
        print('user_map:', self.user_dict)

    async def disconnect_all_users(self):
        for user_id in self.user_dict:
            await self.disconnect(user_id)

    async def send_personal_msg(self, websocket: WebSocket, user_id: str, msg: str):
        pass

    async def broadcast(self, message: str, app_id: Optional[str] = None):
        pass

    async def handle_receive_msg(self, json_data):
        try:
            if json_data['cmd'] == 'login':
                self.user_dict[json_data['data']['userId']].user_info = User.UserInfo(app_id=json_data['data']['appId'])
                self.user_dict[json_data['data']['userId']].is_login = True
                print(self.user_dict[json_data['data']['userId']])
            elif json_data['cmd'] == 'heartbeat':
                print('heartbeat')
            elif json_data['cmd'] == 'ping':
                print('ping')
        except Exception as e:
            print(e)


async def serve():
    # 实例化一个rpc服务，使用协程的方式启动我们的服务
    service_names = (
        im_protobuf_pb2.DESCRIPTOR.services_by_name["WebsocketServer"].full_name,
        reflection.SERVICE_NAME,
    )
    server = grpc.aio.server()
    # 添加我们服务
    im_protobuf_pb2_grpc.add_WebsocketServerServicer_to_server(WebsocketServer(), server)
    reflection.enable_server_reflection(service_names, server)
    # 配置启动的端口
    server.add_insecure_port('[::]:' + config.get_grpc_port())
    await server.start()
    await server.wait_for_termination()


app = FastAPI()
user_conn_manager = UserConnectionManager()
redis_controller = RedisController()


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    def QueryUsersOnline(self, request, context):
        return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=True)

    def SendMsg(self, request, context):
        pass
        # return im_protobuf_pb2.SendMsgRsp()

    def SendMsgAll(self, request, context):
        pass
        # return im_protobuf_pb2.SendMsgRsp()

    def GetUserList(self, request, context):
        pass
        # return im_protobuf_pb2.GetUserListRsp()


@app.on_event('startup')
async def on_startup():
    asyncio.get_event_loop().create_task(serve())
    await redis_controller.register_service()
    print('服务启动')


@app.on_event("shutdown")
async def on_shutdown_event():
    await redis_controller.unregister_service()
    # for task in asyncio.Task.all_tasks():
    #     print('cancelling the task {}: {}'.format(id(task), task.cancel()))
    print('服务关停')


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    connect_result = await user_conn_manager.connect_with_token(websocket, token)
    if connect_result is not None:
        try:
            while True:
                json_data = await websocket.receive_json()
                await user_conn_manager.handle_receive_msg(json_data)
        except WebSocketDisconnect:
            await user_conn_manager.disconnect(connect_result)
