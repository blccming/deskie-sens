# from gpiozero import LED

from peripherals.HLK_LD2410C import LD2410C

radar = LD2410C()
radar.init()

radar.restart()

while True:
    pass
