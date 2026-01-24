from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import HLK_LD2410C
from peripherals.SCD4X import SCD4X


class StateMachine:
    def __init__(self):
        self.__radar = HLK_LD2410C()
        self.__air = SCD4X()
        self.__mqtt = MQTT()

    async def run(self):
        # await self.__radar.configure()
        self.__air.configure()

        while True:
            json_payload = await self.__radar.get_json_report()
            self.__mqtt.publish("/radar", json_payload)

            json_payload = self.__air.get_json_report()


#            self.__mqtt.publish("/air", json_payload)
