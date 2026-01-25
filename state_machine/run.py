import asyncio

from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import HLK_LD2410C
from peripherals.SCD4X import SCD4X
from peripherals.SI1145 import SI1145


class StateMachine:
    def __init__(self):
        self.__presence = HLK_LD2410C()
        self.__air = SCD4X()
        self.__light = SI1145()
        self.__mqtt = MQTT()

    async def _presence_loop(self) -> None:
        while True:
            presence_json = await self.__presence.get_json_report()
            self.__mqtt.publish("/presence", presence_json)
            await asyncio.sleep(0.1)

    async def _i2c_loop(self) -> None:
        while True:
            air_json = await self.__air.get_json_report()
            self.__mqtt.publish("/air", air_json)
            await asyncio.sleep(2.0)

            light_json = await self.__light.get_json_report()
            self.__mqtt.publish("/light", light_json)
            await asyncio.sleep(2.0)

    async def run(self):
        # await self.__presence.configure()
        self.__air.configure()

        presence_task = asyncio.create_task(self._presence_loop())
        i2c_task = asyncio.create_task(self._i2c_loop())

        await asyncio.gather(presence_task, i2c_task)
