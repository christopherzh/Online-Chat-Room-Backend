from fastapi import Cookie, Depends, FastAPI, Query, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


import grpc

from protobuf import im_protobuf_pb2, im_protobuf_pb2_grpc

app = FastAPI()


class UserListReq(BaseModel):
    app_id: int = Field(..., alias='appId')


class UserListResp(BaseModel):
    class Data(BaseModel):
        user_count: int = Field(..., alias='userCount')
        user_list: List[str] = Field(..., alias='userList')

    code: int
    msg: str
    data: Data


class UserOnlineReq(BaseModel):
    app_id: int = Field(..., alias='appId')
    user_id: str = Field(..., alias='userId')


class UserOnlineResp(BaseModel):
    class Data(BaseModel):
        online: bool
        user_id: str = Field(..., alias='userId')

    code: int
    msg: str
    data: Data


class MsgToUserReq(BaseModel):
    app_id: int = Field(..., alias='appId')
    user_id: str = Field(..., alias='userId')
    message: str


class MsgToUserResp(BaseModel):
    class Data(BaseModel):
        send_results: bool = Field(..., alias='sendResults')

    code: int
    msg: str
    data: Data


class MsgToAllReq(BaseModel):
    app_id: int = Field(..., alias='appId')
    user_id: str = Field(..., alias='userId')
    msg_id: str = Field(..., alias='msgId')
    message: str


class MsgToAllResp(BaseModel):
    class Data(BaseModel):
        send_results: bool = Field(..., alias='sendResults')

    code: int
    msg: str
    data: Data


async def send_msg():
    # 连接 rpc 服务器
    with grpc.insecure_channel('101.43.149.3:50051') as channel:
        # 通过通道服务一个服务
        stub = im_protobuf_pb2_grpc.WebsocketServerStub(channel)
        # 生成请求我们的服务的函数的时候，需要传递的参数体，它放在hello_pb2里面-请求体为：hello_pb2.HelloRequest对象
        response = await stub.QueryUsersOnline(im_protobuf_pb2.QueryUsersOnlineReq(appId=613, userId='zzh'))
        return {'reply', "QueryUsersOnline" + str(response.retCode)}


@app.get("/")
async def get_root():
    print("root")


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
