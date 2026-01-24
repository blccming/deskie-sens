import asyncio

from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import HLK_LD2410C
from peripherals.SCD4X import SCD4X


class StateMachine:
    def __init__(self):
        self.__radar = HLK_LD2410C()
        self.__air = SCD4X()
        self.__mqtt = MQTT()

    async def _radar_loop(self) -> None:
        while True:
            radar_json = await self.__radar.get_json_report()
            self.__mqtt.publish("/radar", radar_json)
            await asyncio.sleep(0.01)

    async def _air_loop(self) -> None:
        while True:
            air_json = await self.__air.get_json_report()
            self.__mqtt.publish("/air", air_json)
            await asyncio.sleep(0.01)

    async def run(self):
        # await self.__radar.configure()
        self.__air.configure()

        radar_task = asyncio.create_task(self._radar_loop())
        air_task = asyncio.create_task(self._air_loop())

        await asyncio.gather(radar_task, air_task)
