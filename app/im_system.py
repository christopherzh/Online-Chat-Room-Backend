from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from grpc_service.grpc_client import grpc_service_requester
from im.im_model import *

# TODO: 用户鉴权与登录信息入库
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
    return {'root': 'root'}


@app.get("/home/index")
async def enter_room():
    # 前端返回不同appID页面
    pass


@app.get("/user/online", response_model=UserOnlineResp)
async def check_online_user(appId: int, userId: str):
    response = await grpc_service_requester.query_users_online(appId, userId)
    return UserOnlineResp(code=response.retCode, msg=response.errMsg,
                          data=UserOnlineResp.Data(online=response.online, userId=userId))


@app.get("/user/list", response_model=UserListResp)
async def get_user_list(appId: int):
    response = await grpc_service_requester.get_user_list(appId)
    return UserListResp(code=response['retCode'], msg=response['errMsg'],
                        data=UserListResp.Data(userCount=len(response['userList']), userList=response['userList']))


@app.post("/user/sendMessage", response_model=MsgToUserResp)
async def send_message(request: MsgToUserReq):
    response = await grpc_service_requester.send_msg(request, 'msg', 'text', False)
    return MsgToUserResp(code=response.retCode, msg=response.errMsg,
                         data=MsgToUserResp.Data(sendResults=True))


@app.post("/user/sendMessageAll", response_model=MsgToAllResp)
async def send_message_all(request: MsgToAllReq):
    response = await grpc_service_requester.send_msg_all(request, 'msg', 'text')
    if response:
        return MsgToAllResp(code=200, msg='Success',
                            data=MsgToAllResp.Data(sendResults=True))
    else:
        return MsgToAllResp(code=400, msg='Fail',
                            data=MsgToAllResp.Data(sendResults=False))
