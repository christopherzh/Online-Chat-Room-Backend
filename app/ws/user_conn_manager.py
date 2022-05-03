import time

from DB import config
from DB.redis_util import redis_controller
from im.im_model import *
from .ws_model import *
from grpc_service.grpc_client import grpc_service_requester


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

    async def connect_with_token(self, websocket: WebSocket, token: str):
        # 需要： 接受连接，验证用户身份
        await websocket.accept()
        print("接受连接")
        auth_result = auth_user(token)
        if auth_result is None:
            await websocket.close(code=1005)
            return None
        self.user_dict[auth_result] = User(user_id=auth_result, is_auth=True, is_login=False, ws=websocket)
        print('建立用户连接后,user_dict:', self.user_dict)
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
        cms = 'exit'
        msg_type = 'text'
        msg = ''
        await self.broadcast(seq, app_id, user_id, cms, msg_type, msg)
        await grpc_service_requester.send_msg_all(
            MsgToAllReq(seq=seq, appId=app_id, userId=user_id, msgId=seq, message=msg), cms, msg_type,
            config.get_localhost() + ':' + config.get_grpc_port())

    async def disconnect_all_users(self):
        for user_id in self.user_dict:
            await self.disconnect(user_id)

    async def query_user_online(self, app_id: int, user_id: str) -> bool:
        if user_id in self.user_dict:
            return True
        else:
            connect_info = await redis_controller.get_user(user_id)
            if connect_info is not None:
                return True
        return False

    def get_user_list(self, app_id: int) -> List[str]:
        if app_id in self.room_dict:
            res = self.room_dict[app_id]
        else:
            res = []
        return res

    async def send_personal_msg(self, seq: str, app_id: int, user_id: str, cms: str, type: str, msg: str,
                                is_local: bool) -> bool:
        if user_id in self.user_dict:
            await self.user_dict[user_id].ws.send_json(SendMsgToClient(seq=seq, cmd=cms,
                                                                       response=SendMsgToClient.Response(code=200,
                                                                                                         code_msg='Success',
                                                                                                         data=SendMsgToClient.Response.Data(
                                                                                                             target=user_id,
                                                                                                             type=type,
                                                                                                             msg=msg,
                                                                                                             msg_from=''))).dict())
            return True
        elif not is_local:
            connect_info = await redis_controller.get_user(user_id)
            if connect_info is not None:
                await grpc_service_requester.send_msg(
                    MsgToUserReq(seq=seq, appId=app_id, userId=user_id, message=msg), cms, type, True,
                    connect_info)
                return True
        return False

    async def broadcast(self, seq: str, app_id: int, user_id: str, cms: str, type: str, msg: str) -> bool:
        if app_id not in self.room_dict:
            return True
        for user in self.room_dict[app_id]:
            if user == user_id:
                pass
            else:
                await self.user_dict[user].ws.send_json(SendMsgToClient(seq=seq, cmd=cms,
                                                                        response=SendMsgToClient.Response(code=200,
                                                                                                          code_msg='Success',
                                                                                                          data=SendMsgToClient.Response.Data(
                                                                                                              target='',
                                                                                                              type=type,
                                                                                                              msg=msg,
                                                                                                              msg_from=user_id))).dict())
        return True

    async def handle_login_msg(self, json_data: LoginReq):
        print('login_json:', json_data)
        user_id: str = json_data.data.user_id
        app_id: int = json_data.data.app_id
        self.user_dict[user_id].user_info = User.UserInfo(app_id=app_id)
        self.user_dict[user_id].is_login = True
        await redis_controller.add_user(user_id)
        print('登陆后user_dict', self.user_dict)

        if app_id not in self.room_dict:
            self.room_dict[app_id] = list()
        self.room_dict[app_id].append(user_id)
        print('登录后room_dict', self.room_dict)

        # 向所有房间内所有用户发送enter消息
        seq: str = json_data.seq + '-enter'
        cms = 'enter'
        msg_type = 'text'
        msg = ''
        await self.broadcast(seq, app_id, user_id, cms, msg_type, msg)
        await grpc_service_requester.send_msg_all(
            MsgToAllReq(seq=seq, appId=app_id, userId=user_id, msgId=seq, message=msg), cms, msg_type,
            config.get_localhost() + ':' + config.get_grpc_port())
