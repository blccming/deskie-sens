import asyncio
from time import sleep

from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import HLK_LD2410C


class StateMachine:
    def __init__(self):
        self.__radar = HLK_LD2410C()
        self.__mqtt = MQTT()

    async def run(self):
        while True:
            json_payload = await self.__radar.get_json_report()
            self.__mqtt.publish("/radar", json_payload)
