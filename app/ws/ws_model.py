from typing import Dict, Any, Optional

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


class UserEnter(BaseModel):
    pass
    # 有新用户加入，通知房间内所有人


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


class User(BaseModel):
    class UserInfo(BaseModel):
        app_id: str
    user_id: str
    is_auth: bool
    is_login: bool
    user_info: Optional[UserInfo]


