from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from gmqtt import Client as MQTTClient

from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig(
    host="test.mosquitto.org",
    port=1883,
    keepalive=60,
)

# room(str) : busyscore(int)
rooms:dict ={
}
fast_mqtt = FastMQTT(config=mqtt_config)

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()

app = FastAPI(lifespan=_lifespan)



# mqtt handlers
@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("/mqtt")  # subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@fast_mqtt.subscribe("west/#", qos=0)
async def room_update(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
	area:List[str] = topic.split("/")
	hallway:str = area[1]
	section:str = area[2]
	if not hallway in rooms:
		 rooms[hallway] = {}

	rooms[hallway][section] = int(payload.decode())
	print(rooms)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/query/")
async def query_rooms():

	# get the average first
	sum_busy = 0
	sum_len = 0
	for hallway in rooms:
		for section, busy in hallway.items():
			sum_len += 1
			sum_busy += busy # add busy score

	average_busy = sum_busy/sum_len
	return_rooms = rooms
	
	for hallway in return_rooms:
		for section, busy in hallway.items():
			section = busy/average_busy
	return return_rooms
