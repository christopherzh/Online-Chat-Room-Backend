import aioredis

from DB import config


class RedisController:
    def __init__(self):
        self.redis_ip = config.get_redis_ip()
        self.redis_password = config.get_pwd()
        self.connection_services = self.__get_connection(0)  # 微服务获取
        self.connection_users = self.__get_connection(1)  # 保存已连接用户信息

    def __get_connection(self, database: int):
        return aioredis.from_url(
            "redis://" + self.redis_ip+':'+config.get_redis_port(), password=self.redis_password, db=database
        )

    async def register_service(self):
        await self.connection_services.sadd('websocket_service_list',
                                            config.get_localhost() + ":" + config.get_grpc_port())
        print(await self.connection_services.smembers('websocket_service_list'))

    async def unregister_service(self):
        await self.connection_services.srem('websocket_service_list',
                                            config.get_redis_ip() + ":" + config.get_grpc_port())

    async def get_service(self):
        # grpc_ip = '101.43.149.3'
        # grpc_port = '50051'
        # return grpc_ip, grpc_port
        return await self.connection_services.srandmember('websocket_service_list')

    async def add_user(self, user_id: str):
        await self.connection_users.hset('user_connect_info', user_id, config.get_localhost()+':'+config.get_grpc_port())
        print('redis:', await self.connection_users.hgetall('user_connect_info'))

    async def del_user(self, user_id: str):
        await self.connection_users.hdel('user_connect_info', user_id)
        print('redis:',await self.connection_users.hgetall('user_connect_info'))

    async def del_all_users(self):
        await self.connection_users.delete('user_connect_info')

    async def get_user(self, user_id: str):
        await self.connection_users.hget('user_connect_info', user_id)
