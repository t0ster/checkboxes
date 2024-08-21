import asyncio
from concurrent.futures import ThreadPoolExecutor
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


# THREAD_POOL = ThreadPoolExecutor()


@api.websocket("/checkboxes")
async def checkboxes_ws(websocket: WebSocket):
    await websocket.accept()
    client_id = uuid4()

    async def callback(client_id, data: bytes):
        # print("Sending to", client_id)
        try:
            await websocket.send_bytes(data)
        except WebSocketDisconnect:
            SUBSCRIBERS.pop(client_id, None)

    SUBSCRIBERS[client_id] = callback

    try:
        await websocket.send_bytes(CHECKBOXES.tobytes())
        while True:
            message = await websocket.receive_bytes()
            # d = await asyncio.get_event_loop().run_in_executor(
            #     THREAD_POOL, BinaryPacker.unpack, message
            # )
            d = BinaryPacker.unpack(message)
            index = d["number"]
            value = d["bit1"]
            CHECKBOXES[index] = value
            # for cid, callback in SUBSCRIBERS.items():
            #     if cid != client_id:
            #         await callback(CHECKBOXES.tobytes())
            async with create_task_group() as tg:
                for cid, callback in SUBSCRIBERS.items():
                    if cid != client_id:
                        tg.start_soon(callback, client_id, CHECKBOXES.tobytes())
    except WebSocketDisconnect:
        pass
    finally:
        SUBSCRIBERS.pop(client_id, None)
