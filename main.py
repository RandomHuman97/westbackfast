from contextlib import asynccontextmanager
from typing import Any
import asyncio
from fastapi import FastAPI, websockets
from gmqtt import Client as MQTTClient

from fastapi_mqtt import FastMQTT, MQTTConfig
from starlette.websockets import WebSocket

mqtt_config = MQTTConfig(
    host="test.mosquitto.org",
    port=1883,
    keepalive=60,
)

# room(str) : busyscore(int)
rooms:dict ={
}
avg_rooms:dict = {}
fast_mqtt = FastMQTT(config=mqtt_config)



@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()

app = FastAPI(lifespan=_lifespan)

@app.websocket("/ws")
async def websocket_rooms(websocket : WebSocket) -> dict:
    """
    Returns the rooms and their busyness score
    expected room format:
    {
        "hallway:int": {
            "section:str": busyness score
        }
    }
    """
    async def send_rooms():
        await websocket.send_json(avg_rooms)
    global websocket_callback
    websocket_callback = send_rooms

    await websocket.accept()
    await websocket.send_json(avg_rooms)
    prev_rooms = {}
    while True:
        await asyncio.sleep(1)

def average_rooms(input_rooms:dict) -> dict:
    if not input_rooms:
        return {"rooms": None, "success": False}
    # get the average first
    sum_busy: int = 0
    sum_len: int = 0

    print(input_rooms)
    for hallway in input_rooms:
        for section, busy in input_rooms[hallway].items():
            sum_busy += busy
            sum_len += 1

    average_busy: float = sum_busy / sum_len

    return_rooms = input_rooms

    for hallway in return_rooms: # normalize the values
        for section, busy in input_rooms[hallway].items():
            return_rooms[hallway][section] = (busy / average_busy / sum_len) * 255  # add extra divide by sum_len to make the average 1
    return return_rooms

# mqtt handlers
@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("/mqtt")  # subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@fast_mqtt.subscribe("west/#", qos=0)
async def room_update(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    global rooms

    area = topic.split("/")
    hallway:str = area[1]
    section:str = area[2]
    if not hallway in rooms:
         rooms[hallway] = {}

    rooms[hallway][section] = int(payload.decode())
    global avg_rooms # update the global variable
    avg_rooms = average_rooms(rooms)

    #fire callback/notify websocket
    await websocket_callback()
@app.get("/")
async def root():
    return {"message": "Hello World"}



