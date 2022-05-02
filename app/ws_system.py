import asyncio

from fastapi import FastAPI, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

from grpc_service import grpc_server
from DB.redis_util import redis_controller
from ws.user_conn_manager import UserConnectionManager
from ws.ws_model import *

app = FastAPI()
user_conn_manager=UserConnectionManager()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def on_startup():
    await redis_controller.register_service()
    asyncio.create_task(grpc_server.serve(user_conn_manager))
    print('服务启动')


@app.on_event("shutdown")
async def on_shutdown_event():
    await redis_controller.unregister_service()
    print('服务关停')


@app.get("/")
async def get_root():
    return {'root': 'root'}


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
