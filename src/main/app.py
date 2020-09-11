import logging
import json
from collections import defaultdict

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates

from starlette.websockets import WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Notifier:
    """
        Manages chat room sessions and members along with message routing
    """

    def __init__(self):
        self.connections: dict = defaultdict(dict)
        self.generator = self.get_notification_generator()

    async def get_notification_generator(self):
        while True:
            message = yield
            msg = message["message"]
            room_name = message["room_name"]
            await self._notify(msg, room_name)

    def get_members(self, room_name):
        try:
            return self.connections[room_name]
        except Exception:
            return None

    async def push(self, msg: str, room_name: str = None):
        message_body = {"message": msg, "room_name": room_name}
        await self.generator.asend(message_body)

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if self.connections[room_name] == {} or len(self.connections[room_name]) == 0:
            self.connections[room_name] = []
        self.connections[room_name].append(websocket)
        print(f"CONNECTIONS : {self.connections[room_name]}")

    def remove(self, websocket: WebSocket, room_name: str):
        self.connections[room_name].remove(websocket)
        print(
            f"CONNECTION REMOVED\nREMAINING CONNECTIONS : {self.connections[room_name]}"
        )

    async def _notify(self, message: str, room_name: str):
        living_connections = []
        while len(self.connections[room_name]) > 0:

            websocket = self.connections[room_name].pop()
            await websocket.send_text(message)
            living_connections.append(websocket)
        self.connections[room_name] = living_connections


notifier = Notifier()


# controller routes
@app.get("/{room_name}/{user_name}")
async def get(request: Request, room_name, user_name):
    return templates.TemplateResponse(
        "chat_room.html",
        {"request": request, "room_name": room_name, "user_name": user_name},
    )


@app.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket, room_name, background_tasks: BackgroundTasks
):
    await notifier.connect(websocket, room_name)
    try:
        while True:
            data = await websocket.receive_text()
            d = json.loads(data)
            d["room_name"] = room_name

            room_members = (
                notifier.get_members(room_name)
                if notifier.get_members(room_name) is not None
                else []
            )
            if websocket not in room_members:
                print("SENDER NOT IN ROOM MEMBERS: RECONNECTING")
                await notifier.connect(websocket, room_name)

            await notifier._notify(f"{data}", room_name)
    except WebSocketDisconnect:
        notifier.remove(websocket, room_name)
