import asyncio
from uuid import uuid4

from anyio import create_task_group
from bitarray import bitarray
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from lib.binary_packer import BinaryPacker

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/")
async def home():
    from uvloop import EventLoopPolicy

    assert isinstance(asyncio.get_event_loop_policy(), EventLoopPolicy)
    return {"message": "Hello World"}


CHECKBOXES = bitarray(10000)
SUBSCRIBERS = {}


@api.websocket("/checkboxes")
async def checkboxes_ws(websocket: WebSocket):
    await websocket.accept()
    client_id = uuid4()

    SUBSCRIBERS[client_id] = websocket.send_bytes

    try:
        await websocket.send_bytes(CHECKBOXES.tobytes())
        while True:
            message = await websocket.receive_bytes()
            d = BinaryPacker.unpack(message)
            index = d["number"]
            value = d["bit1"]
            CHECKBOXES[index] = value
            async with create_task_group() as tg:
                for cid, callback in SUBSCRIBERS.items():
                    if cid != client_id:
                        tg.start_soon(callback, CHECKBOXES.tobytes())
    except WebSocketDisconnect:
        pass
    finally:
        SUBSCRIBERS.pop(client_id, None)
