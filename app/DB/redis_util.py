import aioredis

from DB import config


class RedisController:
    def __init__(self):
        self.redis_ip = config.get_ip()
        self.redis_password = config.get_pwd()
        self.connection_services = self.__get_connection(0) #微服务获取
        self.connection_users = self.__get_connection(1) #保存已连接用户信息

    async def __get_connection(self, database: int):
        return await aioredis.from_url(
            "redis://" + self.redis_ip, password=self.redis_password, db=database
        )

    def register_service(self):
        self.connection_services.sadd('websocket_service_info_list', self.redis_ip)

    def add_user(self, user_id, connection_ip):
        self.connection_users.set(user_id, connection_ip)

    def get_service(self):
        pass

    def get_user(self):
        pass

