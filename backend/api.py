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


CHECKBOXES = bitarray(10000)
SUBSCRIBERS = set()


def not_none(x):
    assert x is not None
    return x


THREAD_POOL = ThreadPoolExecutor(max_workers=not_none(os.cpu_count()) + 1)


async def broadcast_update(initiator: WebSocket):
    disconnected = set()

    async def send_to_subscriber(websocket):
        if websocket != initiator:
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


BATCH_INTERVAL = 0.1  # 100ms
PENDING_UPDATES = deque()


async def process_batched_updates():
    global PENDING_UPDATES
    while True:
        await asyncio.sleep(BATCH_INTERVAL)
        if PENDING_UPDATES:
            updates = PENDING_UPDATES
            PENDING_UPDATES = deque()
            grouped_updates = {}
            while updates:
                websocket, index, value = updates.popleft()
                if websocket not in grouped_updates:
                    grouped_updates[websocket] = []
                grouped_updates[websocket].append((index, value))

            for websocket, batch in grouped_updates.items():
                for index, value in batch:
                    CHECKBOXES[index] = value
                await broadcast_update(initiator=websocket)


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
            PENDING_UPDATES.append((websocket, index, value))
    except WebSocketDisconnect:
        pass
    finally:
        SUBSCRIBERS.discard(websocket)


# Start the batching task when the app starts
@api.on_event("startup")
async def startup_event():
    asyncio.create_task(process_batched_updates())
