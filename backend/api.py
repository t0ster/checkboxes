import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from uuid import uuid4

from anyio import create_memory_object_stream, create_task_group
from bitarray import bitarray
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from lib.binary_packer import BinaryPacker


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(send_to_all())
    yield


api = FastAPI(lifespan=lifespan)

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
SUBSCRIBERS = set()


# THREAD_POOL = ThreadPoolExecutor()

send_stream, receive_stream = create_memory_object_stream()


async def send_to_all():
    while True:
        msg = await receive_stream.receive()
        for websocket in SUBSCRIBERS:
            if websocket != msg["initiator"]:
                try:
                    await websocket.send_bytes(msg["data"])
                except WebSocketDisconnect:
                    SUBSCRIBERS.remove(websocket)
                    # print("Removed", websocket)
                    return await send_to_all()


@api.websocket("/checkboxes")
async def checkboxes_ws(websocket: WebSocket):
    await websocket.accept()
    SUBSCRIBERS.add(websocket)

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
            await send_stream.send(
                {"initiator": websocket, "data": CHECKBOXES.tobytes()}
            )
    except WebSocketDisconnect:
        pass
