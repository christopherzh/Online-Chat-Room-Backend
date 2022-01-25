from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import os
app = FastAPI()

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get():
    return {"message":"Hello!!"}


@app.websocket("/api")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message is : {data}")

# @app.get("/test")
# async def test():
#     return {"message":os.environ.get("DOCKER_ID")}