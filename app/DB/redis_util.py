import aioredis

from DB import config


class RedisController:
    def __init__(self):
        self.redis_ip = config.get_ip()
        self.redis_password = config.get_pwd()
        self.connection_services = self.__get_connection(0) #微服务获取
        self.connection_users = self.__get_connection(1) #保存已连接用户信息

    def __get_connection(self, database: int):
        return  aioredis.from_url(
            "redis://" + self.redis_ip, password=self.redis_password, db=database
        )

    async def register_service(self):
        await self.connection_services.sadd('websocket_service_info_list', config.get_localhost()+":8000")

    def unregister_service(self):
        pass

    async def add_user(self, user_id, connection_ip):
        await self.connection_users.set(user_id, connection_ip)

    def get_service(self):
        grpc_ip = '101.43.149.3'
        grpc_port = '50051'
        return grpc_ip, grpc_port

    def get_user_conn_info(self):
        pass

