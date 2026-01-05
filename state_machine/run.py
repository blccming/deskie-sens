from time import sleep

from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import LD2410C


class StateMachine:
    def __init__(self):
        self.__state = 0
        self.__radar = LD2410C()
        self.__mqtt = MQTT()

    def run(self):
        r = self.__radar
        m = self.__mqtt

        match self.__state:
            case 0:
                if r.init():
                    self.__state = 1
                sleep(0.1)
            case 1:
                r.update()
                m.publish(
                    "ksdm2/LD2410C/test",
                    r.get_data_json(),
                )
            case _:
                pass
