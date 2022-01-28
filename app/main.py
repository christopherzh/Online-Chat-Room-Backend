from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status, WebSocketDisconnect
from typing import Optional, List
from DB import get_config
from fastapi.responses import HTMLResponse
import aioredis
import time

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <label>Item ID: <input type="text" id="itemId" autocomplete="off" value="foo"/></label>
            <label>Token: <input type="text" id="token" autocomplete="off" value="some-key-token"/></label>
            <button onclick="connect(event)">Connect</button>
            <hr>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = null;
            function connect(event) {
                var itemId = document.getElementById("itemId")
                var token = document.getElementById("token")
                ws = new WebSocket("ws://localhost:8000/api/0/" + itemId.value + "/ws?token=" + token.value+"&client_id="+Number(client_id));
                                redis = new WebSocket("ws://localhost:8000/api/1/"+Number(client_id))
                redis.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


# @app.get("/")
# async def get():
#     return {"message":"Hello!!"}
#
#
# @app.websocket("/api")
# async def chat(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"Message is : {data}")
#
# @app.get("/Redis")
# async def Redis():
#     return {"message":"os.environ.get"}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

class RedisConnectionManager:
    def __init__(self):
        self.redis_pool = {}
        self.pubsub = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    async def conn_redis(self,client_id):
        if self.redis_pool.get(client_id) is None:
            self.redis_pool[client_id] = await aioredis.from_url(
                "redis://" + get_config.get_ip(), password=get_config.get_pwd()
            )
            self.pubsub[client_id] = self.redis_pool[client_id].pubsub()
        if self.pubsub.get(client_id) is not None:
            await self.pubsub[client_id].subscribe("channel:1")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    def disconnect(self,client_id):
        del self.pubsub[client_id]
        del self.redis_pool[client_id]



manager = ConnectionManager()
redis_manager =RedisConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)


async def get_cookie_or_token(
        websocket: WebSocket,
        session: Optional[str] = Cookie(None),
        token: Optional[str] = Query(None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/api/1/{client_id}")
async def websocket_redis(websocket: WebSocket,client_id: Optional[int] = None):
    await redis_manager.connect(websocket)
    await redis_manager.conn_redis(client_id)
    try:
        while True:
            # t1 = time.time()
            message = await redis_manager.pubsub[client_id].get_message(ignore_subscribe_messages=True)
            # print("time for getting msg:", time.time() - t1)
            if message is not None and message['data'].decode('utf-8')[0:13] != str(client_id):
                print(f"(Reader) Message Received: {message}", type(message))
                # await manager.send_personal_message(f"redis:{message['data']}", websocket)
                await manager.send_personal_message(
                    f"Client #{message['data'].decode('utf-8')[0:13]} says: {message['data'].decode('utf-8')[13:]}",
                    websocket)
    except WebSocketDisconnect:
        redis_manager.disconnect(client_id)

@app.websocket("/api/0/{item_id}/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        item_id: str,
        q: Optional[int] = None,
        cookie_or_token: str = Depends(get_cookie_or_token),
        client_id: Optional[int] = None
):
    await manager.connect(websocket)
    try:
        while True:
            t2 = time.time()
            data = await websocket.receive_text()
            print("time for receive text:", time.time() - t2)
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await redis_manager.redis_pool[client_id].publish("channel:1", str(client_id) + data)
            # await websocket.send_text(
            #     f"Session cookie or query token value is: {cookie_or_token}"
            # )
            # if q is not None:
            #     await websocket.send_text(f"Query parameter q is: {q}")
            # await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")

            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
