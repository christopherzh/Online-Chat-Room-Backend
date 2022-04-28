import asyncio

import grpc
from fastapi import FastAPI, WebSocketDisconnect
from grpc_reflection.v1alpha import reflection
from starlette.websockets import WebSocket

from DB import redis_util
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
    return True


@Singleton
class UserConnectionManager:
    def __init__(self):
        self.user_dict: Dict[str, User] = {}
        self.room_dict: Dict[int, str] = {}

    async def connect_with_token(self, websocket: WebSocket, token: str):
        # 需要： 接受连接，验证用户身份
        await websocket.accept()
        if auth_user(token):
            pass
        else:
            await self.disconnect(websocket, need_del_user=False)

    async def disconnect(self, websocket: WebSocket, need_del_user: bool, user_id: Optional[str] = None):
        await websocket.close()
        if need_del_user:
            if user_id is not None:
                self.user_dict.pop(user_id)
            else:
                raise KeyError('User ID must not be None when you need delete user!')

    async def send_personal_msg(self, websocket: WebSocket, user_id: str, msg: str):
        pass

    async def broadcast(self, message: str, app_id: Optional[str] = None):
        pass

    async def handle_receive_msg(self, msg):
        pass


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
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()


app = FastAPI()
user_conn_manager = UserConnectionManager()
redis_controller = redis_util.RedisController()


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
    await redis_controller.register_service()
    asyncio.get_event_loop().create_task(serve())


@app.on_event("shutdown")
def on_shutdown_event():
    redis_controller.unregister_service()


@app.websocket("ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await user_conn_manager.connect_with_token(websocket, token)
    try:
        while True:
            json_data = await websocket.receive_json()
            user_conn_manager.handle_receive_msg(json_data)

    except WebSocketDisconnect:
        user_conn_manager.disconnect()
