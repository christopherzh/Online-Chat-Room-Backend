from typing import Optional, Any, Dict, Set, List

import grpc
from grpc_reflection.v1alpha import reflection
import asyncio

from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status, WebSocketDisconnect

from DB import config
from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc
from websocket_server import WebsocketServer

from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    class Data(BaseModel):
        user_id: str = Field(..., alias='userId')
        app_id: int = Field(..., alias='appId')

    seq: str
    cmd: str
    data: Data


class LoginResp(BaseModel):
    class Response(BaseModel):
        code: int
        code_msg: str = Field(..., alias='codeMsg')
        data: Any

    seq: str
    cmd: str
    response: Response


class HeartBeat(BaseModel):
    seq: str
    cmd: str
    data: Dict[str, Any]


class SendMsgToClient(BaseModel):
    class Response(BaseModel):
        class Data(BaseModel):
            target: str
            type: str
            msg: str
            from_: str = Field(..., alias='from')

        code: int
        code_msg: str = Field(..., alias='codeMsg')
        data: Data

    seq: str
    cmd: str
    response: Response


app = FastAPI()


class UserStoreInfo(BaseModel):
    pass


class User():
    user_id: str
    status: int
    ws: WebSocket

class Singleton:
    def __init__(self, cls):
        self.__instance = {}
        self.__cls = cls

    def __call__(self):
        if self.__cls not in self.__instance:
            self.__instance[self.__cls] = self.__cls()
        return self.__instance[self.__cls]


@Singleton
class UserManager:
    def __init__(self):
        self.user_dict: Dict[str, User] = {}


@Singleton
class RoomManager:
    def __init__(self):
        self.room_dict = Dict[int, List[str]]

    def add_room(self, app_id: str):
        self.room_dict[app_id] = []

    def del_room(self,app_id:str):
        pass


@Singleton
class WebsocketManager:
    def __init__(self):
        pass

    async def connect(self, websocket: WebSocket, client_id):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id):
        del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str,app_id:Optional[str]=None):
        for connection in self.active_connections:
            await self.active_connections[connection].send_text(message)


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


@app.on_event('startup')
async def on_startup():
    asyncio.get_event_loop().create_task(serve())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    pass
    # await manager.connect(websocket, client_id)
    # await manager.send_personal_message(str(config.get_localhost()), websocket)
    # try:
    #     while True:
    #         data = await websocket.receive_text()
    #         await manager.send_personal_message(f"你说了: {data}", websocket)
    #
    # except WebSocketDisconnect:
    #     manager.disconnect(client_id)
    #     await manager.broadcast(f"Client #{client_id} left the chat")
