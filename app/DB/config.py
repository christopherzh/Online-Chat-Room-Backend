import os


def get_conn_url():
    return "redis://" + get_redis_ip()


def get_localhost():
    return os.environ.get("LOCAL_HOST")


def get_redis_ip():
    # return os.environ.get("REDIS_IP")
    return '101.43.149.3'


def get_redis_port():
    return '6379'


def get_grpc_port():
    return '50051'


def get_user():
    return os.environ.get("REDIS_USR")


def get_pwd():
    return os.environ.get("REDIS_PWD")
