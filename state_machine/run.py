from enum import IntEnum
from time import sleep

from comms.mqtt import MQTT
from peripherals.HLK_LD2410C import LD2410C


class States(IntEnum):
    INIT = 0
    MEASURE = 1
    PUBLISH = 2


class StateMachine:
    def __init__(self):
        self.__state = 0
        self.__radar = LD2410C()
        self.__mqtt = MQTT()

    def run(self):
        r = self.__radar
        m = self.__mqtt

        match self.__state:
            case States.INIT:
                if r.init():
                    self.__state = States.MEASURE
                sleep(0.1)
            case States.MEASURE:
                if r.update():
                    self.__state = States.PUBLISH
            case States.PUBLISH:
                m.publish(
                    "/radar",
                    r.get_json(),
                )
                self.__state = States.MEASURE
            case _:
                pass
