# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import im_protobuf_pb2 as im__protobuf__pb2


class AccServerStub(object):
    """The AccServer service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.QueryUsersOnline = channel.unary_unary(
                '/protobuf.AccServer/QueryUsersOnline',
                request_serializer=im__protobuf__pb2.QueryUsersOnlineReq.SerializeToString,
                response_deserializer=im__protobuf__pb2.QueryUsersOnlineRsp.FromString,
                )


class AccServerServicer(object):
    """The AccServer service definition.
    """

    def QueryUsersOnline(self, request, context):
        """查询用户是否在线
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_AccServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'QueryUsersOnline': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryUsersOnline,
                    request_deserializer=im__protobuf__pb2.QueryUsersOnlineReq.FromString,
                    response_serializer=im__protobuf__pb2.QueryUsersOnlineRsp.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'protobuf.AccServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class AccServer(object):
    """The AccServer service definition.
    """

    @staticmethod
    def QueryUsersOnline(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/protobuf.AccServer/QueryUsersOnline',
            im__protobuf__pb2.QueryUsersOnlineReq.SerializeToString,
            im__protobuf__pb2.QueryUsersOnlineRsp.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
