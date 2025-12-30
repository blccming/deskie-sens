import re
from time import sleep

import serial


class LD2410C:
    TARGET_STATE_NO_TARGET = 0x00
    TARGET_STATE_MOVING_TARGET = 0x01
    TARGET_STATE_STATIONARY_TARGET = 0x02
    TARGET_STATE_MOVING_AND_STATIONARY_TARGET = 0x03
    TARGET_STATE_BACKGROUND_NOISE_DETECTION = 0x04
    TARGET_STATE_BACKGROUND_NOISE_DETECTION_SUCCESS = 0x05
    TARGET_STATE_BACKGROUND_NOISE_DETECTION_FAIL = 0x06
    TARGET_STATE_UNDEFINED = 0xFF

    def __init__(self):
        self.__ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=256000,
            timeout=0.1,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
        )
        self.__target_stat: int = TARGET_STATE_UNDEFINED
        self.__presence: bool = False

    def init(self):
        self.__ser.flush()

        self.enable_config()

        # TODO: radar config here (with error handling)

        self.disable_config()

    def enable_config(self) -> bool:
        return self.config_transceive(0x00FF, 0x0001) == "0800ff01000001004000"

    def disable_config(self) -> bool:
        return self.config_transceive(0x00FE, None) == "0400fe010000"

    def factory_reset(self) -> bool:
        return self.config_transceive(0x00A2, None) == "0400a2010000"

    def restart(self) -> bool:
        return self.config_transceive(0x00A3, None) == "0400a3010000"

    # automatic background noise detection and sensitivity configuration
    def auto_sensitivity(self, measurement_duration) -> bool:
        if measurement_duration < 0:
            raise ValueError("Measurement duration must be non-negative")

        if measurement_duration > 0xFFFF:
            raise ValueError("Measurement duration must be less than 65536")

        return self.config_transceive(0x000B, measurement_duration)

    # STRUCTURE
    # | HEADER | DATA_LENGTH | DATA: CMD WORD | DATA: CMD VALUE | FOOTER |
    def config_transceive(self, cmdwrd: int, cmdval: int | None) -> str:
        # header and footer are the same for every configuration command
        HEADER = bytearray([0xFD, 0xFC, 0xFB, 0xFA])
        FOOTER = bytearray([0x04, 0x03, 0x02, 0x01])

        # convert integer input to bytes (-> LSB first)
        cmdwrd = cmdwrd.to_bytes(2, byteorder="little")

        if cmdval:
            cmdval_byte_length = cmdval.bit_length() // 8 + (
                1 if cmdval.bit_length() % 8 != 0 else 0
            )
            cmdval = cmdval.to_bytes(cmdval_byte_length, byteorder="little")

        # calculate length of data intra-frame
        data_length = len(cmdwrd) + (len(cmdval) if cmdval else 0)
        data_length = data_length.to_bytes(2, byteorder="little")

        # construct command
        cmd_packet = bytearray()
        cmd_packet.extend(HEADER)
        cmd_packet.extend(data_length)
        cmd_packet.extend(cmdwrd)
        if cmdval:
            cmd_packet.extend(cmdval)
        cmd_packet.extend(FOOTER)

        # send command
        print(f"Sending config frame: {cmd_packet.hex()}")
        self.__ser.write(cmd_packet)

        # receive ACK
        answer = self.__ser.read(32).hex()
        print(f"Received: {answer}")
        self.__ser.flush()

        # get clean answer to return
        try:
            answer_clean = re.search(r"(?<=fdfcfbfa).*?(?=04030201)", answer).group(0)
        except AttributeError:
            answer_clean = None

        return answer_clean
