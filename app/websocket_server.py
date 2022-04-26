from protobuf import im_protobuf_pb2_grpc, im_protobuf_pb2


class WebsocketServer(im_protobuf_pb2_grpc.WebsocketServerServicer):
    async def QueryUsersOnline(self, request, context):
        return im_protobuf_pb2.QueryUsersOnlineRsp(retCode=200, errMsg='Success', online=True)

    def SendMsg(self, request, context):
        pass

    def SendMsgAll(self, request, context):
        pass

    def GetUserList(self, request, context):
        pass