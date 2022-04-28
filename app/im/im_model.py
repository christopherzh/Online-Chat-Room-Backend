from typing import Optional, Any, Dict, Set, List

from pydantic import BaseModel, Field


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
