from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status, WebSocketDisconnect
from typing import Optional, Dict

import aioredis
import time

import grpc
from grpc_reflection.v1alpha import reflection
import asyncio

import grpc_client
from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc
from DB import get_config

app = FastAPI()


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    async def QueryUsersOnline(self, request, context):
        return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=True)


async def serve():
    # 实例化一个rpc服务，使用协程的方式启动我们的服务
    service_names = (
        im_protobuf_pb2.DESCRIPTOR.services_by_name["AccServer"].full_name,
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


class ClientManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id):
        del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await self.active_connections[connection].send_text(message)


class RedisConnectionManager:
    def __init__(self):
        self.redis_pool = {}
        self.pubsub = {}

    async def conn_redis(self, client_id):
        if self.redis_pool.get(client_id) is None:
            self.redis_pool[client_id] = await aioredis.from_url(
                "redis://" + get_config.get_ip(), password=get_config.get_pwd()
            )
            self.pubsub[client_id] = self.redis_pool[client_id].pubsub()
            await self.pubsub[client_id].subscribe("channel:1")

    def disconnect(self, client_id):
        del self.pubsub[client_id]
        del self.redis_pool[client_id]


class RedisController:
    def __init__(self):
        self.redis_ip = get_config.get_ip()
        self.redis_password = get_config.get_pwd()
        self.connection_services = self.__get_connection(0)
        self.connection_users = self.__get_connection(1)

    def __get_connection(self, database: int):
        return await aioredis.from_url(
            "redis://" + self.redis_ip, password=self.redis_password, db=database
        )

    def register_service(self):
        self.connection_services.sadd('service_ips', self.redis_ip)

    def add_user(self, user_id, connection_ip):
        self.connection_users.set(user_id, connection_ip)


class ClientHelper:
    pass


def decodeWebsocketData():
    pass


manager = ClientManager()
redis_controller = RedisController()
redis_manager = RedisConnectionManager()


async def register_pubsub(client_id, websocket):
    # pool = aioredis.ConnectionPool.from_url("redis://" + get_config.get_ip(), password=get_config.get_pwd(), max_connections=20)
    # redis = aioredis.Redis(connection_pool=pool)
    await redis_manager.conn_redis(client_id)
    while 1:
        message = await redis_manager.pubsub[client_id].get_message(ignore_subscribe_messages=True)
        if message is not None and message['data'].decode('utf-8')[0:13] != str(client_id):
            print(f"(Reader) Message Received: {message}", type(message))
            await manager.send_personal_message(
                f"用户 #{message['data'].decode('utf-8')[0:13]} 说了: {message['data'].decode('utf-8')[13:]}",
                websocket)


async def get_cookie_or_token(
        websocket: WebSocket,
        session: Optional[str] = Cookie(None),
        token: Optional[str] = Query(None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.on_event('startup')
async def on_startup():
    asyncio.get_event_loop().create_task(serve())


@app.get("/")
async def get_root():
    return grpc_client.run()

@app.get("/home/index")
async def enter_room():
    pass

@app.get("/user/list")
async def get_user_list():
    pass

@app.get("user/online")
async def check_online_user():
    pass

@app.post("/user/sendMessageAll")
async def send_message_all():
    pass

@app.post("/user/sendMessage")
async def send_message():
    pass

@app.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        item_id: str,
        q: Optional[int] = None,
        cookie_or_token: str = Depends(get_cookie_or_token),
        client_id: Optional[int] = None
):
    await manager.connect(websocket, client_id)
    await manager.send_personal_message(str(get_config.get_localhost()), websocket)
    loop = asyncio.get_event_loop()
    loop.create_task(register_pubsub(client_id, websocket))
    try:
        while True:
            t2 = time.time()
            data = await websocket.receive_text()
            print("time for receive text:", time.time() - t2)
            await manager.send_personal_message(f"你说了: {data}", websocket)
            await redis_manager.redis_pool[client_id].publish("channel:1", str(client_id) + data)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(f"Client #{client_id} left the chat")
