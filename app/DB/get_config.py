import os
def get_conn_url():
    return "redis://"+get_ip()
def get_localhost():
    return os.environ.get("LOCAL_HOST")
def get_ip():
    return os.environ.get("REDIS_IP")
def get_user():
    return os.environ.get("REDIS_USR")
def get_pwd():
    return os.environ.get("REDIS_PWD")

