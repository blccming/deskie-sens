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

    def __init__(self):
        self.__ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=256000,
            timeout=0.1,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
        )
        self.__target_stat: int = 0
        self.__presence: bool = False

    def init(self):
        self.__ser.flush()
        # TODO: radar config here

    # TODO: check response
    def enable_config(self) -> bool:
        return self.config_transceive(0x00FF, 0x0001)

    # TODO: check response
    def disable_config(self) -> bool:
        return self.config_transceive(0x00FE, None)

    # TODO: check response
    def config_reset(self) -> bool:
        return self.config_transceive(0x00A2, None)

    # TODO: check response
    def restart(self) -> bool:
        self.enable_config()
        sleep(0.02)
        return self.config_transceive(0x00A3, None)

    # automatic background noise detection and sensitivity configuration
    def auto_sensitivity(self, measurement_duration) -> bool:
        if measurement_duration < 0:
            raise ValueError("Measurement duration must be non-negative")

        if measurement_duration > 0xFFFF:
            raise ValueError("Measurement duration must be less than 65536")

        return self.config_transceive(0x000B, measurement_duration)

    # STRUCTURE
    # | HEADER | DATA_LENGTH | DATA: CMD WORD | DATA: CMD VALUE | FOOTER |
    def config_transceive(self, cmdwrd: int, cmdval: int | None) -> bool:
        # header and footer are the same for every configuration command
        HEADER = bytearray([0xFD, 0xFC, 0xFB, 0xFA])
        FOOTER = bytearray([0x04, 0x03, 0x02, 0x01])

        # convert integer input to bytes (-> LSB first)
        cmdwrd = cmdwrd.to_bytes(2, byteorder="little")

        cmdval_byte_length = cmdval.bit_length() // 8 + (
            1 if cmdval.bit_length() % 8 != 0 else 0
        )
        cmdval = (
            cmdval.to_bytes(cmdval_byte_length, byteorder="little") if cmdval else None
        )

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

        # receive ACK; TODO: implement ACK handling
        print(f"Received: {self.__ser.read(16).hex()}")
        self.__ser.flush()

        return True
