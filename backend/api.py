import asyncio
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger

from anyio import create_task_group
from bitarray import bitarray
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from lib.binary_packer import BinaryPacker

logger = getLogger(__name__)


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


def not_none(x):
    assert x is not None
    return x


THREAD_POOL = ThreadPoolExecutor(max_workers=not_none(os.cpu_count()) + 1)
CHECKBOXES = bitarray(10000)
SUBSCRIBERS = set()
PENDING_UPDATES = deque()
BATCH_INTERVAL = 0.1  # 100ms


async def process_batched_updates():
    global PENDING_UPDATES
    while True:
        await asyncio.sleep(BATCH_INTERVAL)
        if PENDING_UPDATES:
            updates = PENDING_UPDATES
            PENDING_UPDATES = deque()

            # Apply all updates to CHECKBOXES
            for index, value in updates:
                CHECKBOXES[index] = value

            # Broadcast to all clients
            await broadcast_update()


async def broadcast_update():
    disconnected = set()

    async def send_to_subscriber(websocket):
        try:
            await websocket.send_bytes(CHECKBOXES.tobytes())
        except WebSocketDisconnect:
            disconnected.add(websocket)
        except Exception:
            logger.exception("Error sending to subscriber")
            disconnected.add(websocket)

    async with create_task_group() as tg:
        for websocket in SUBSCRIBERS:
            tg.start_soon(send_to_subscriber, websocket)

    SUBSCRIBERS.difference_update(disconnected)


@api.websocket("/checkboxes")
async def checkboxes_ws(websocket: WebSocket):
    await websocket.accept()
    SUBSCRIBERS.add(websocket)

    try:
        await websocket.send_bytes(CHECKBOXES.tobytes())
        while True:
            message = await websocket.receive_bytes()
            d = await asyncio.get_event_loop().run_in_executor(
                THREAD_POOL, BinaryPacker.unpack, message
            )
            index = d["number"]
            value = d["bit1"]
            PENDING_UPDATES.append((index, value))
    except WebSocketDisconnect:
        pass
    finally:
        SUBSCRIBERS.discard(websocket)


# Start the batching task when the app starts
@api.on_event("startup")
async def startup_event():
    asyncio.create_task(process_batched_updates())
