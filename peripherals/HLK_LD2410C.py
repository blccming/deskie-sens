import re
import time

import serial


class LD2410C:
    def __init__(self):
        self.__ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=256000,
            timeout=0.1,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
        )

        self.__t_state: int = -1
        self.__t_moving_distance: int = -1
        self.__t_moving_energy: int = -1
        self.__t_stationary_distance: int = -1
        self.__t_stationary_energy: int = -1
        self.__t_detection_distance: int = -1
        self.__last_update_unix: float = -1.0

    def init(self) -> bool:
        self.__ser.flush()

        if not self.__enable_config():
            return False

        if not self.set_bluetooth(False):
            return False

        if not self.__disable_config():
            return False

        return True

    def set_bluetooth(self, enable: bool) -> bool:
        return (
            self.__config_transceive(0x00A4, (0x0100 if enable else 0x0000))
            == "0400a4010000"
        )

    def factory_reset(self) -> bool:
        return self.__config_transceive(0x00A2, None) == "0400a2010000"

    def restart(self) -> bool:
        return self.__config_transceive(0x00A3, None) == "0400a3010000"

    # automatic background noise detection and sensitivity configuration
    def auto_sensitivity(self, measurement_duration) -> bool:
        if measurement_duration < 0:
            raise ValueError("Measurement duration must be non-negative")

        if measurement_duration > 0xFFFF:
            raise ValueError("Measurement duration must be less than 65536")

        return (
            self.__config_transceive(0x000B, measurement_duration) == "04000b010000"
        )  # TODO: test this

    def __enable_config(self) -> bool:
        return self.__config_transceive(0x00FF, 0x0001) == "0800ff01000001004000"

    def __disable_config(self) -> bool:
        return self.__config_transceive(0x00FE, None) == "0400fe010000"

    """
    CONFIGURE RADAR
    """

    # STRUCTURE
    # | HEADER | DATA_LENGTH | DATA: CMD WORD | DATA: CMD VALUE | FOOTER |
    def __config_transceive(self, cmdwrd: int, cmdval: int | None) -> str | None:
        # header and footer are the same for every configuration command
        HEADER = bytearray([0xFD, 0xFC, 0xFB, 0xFA])
        FOOTER = bytearray([0x04, 0x03, 0x02, 0x01])

        # convert integer input to bytes (-> LSB first)
        cmdwrd_bytes = cmdwrd.to_bytes(2, byteorder="little")

        # data length = length of cmdwrd + length of cmdval (if it exists)
        data_length = len(cmdwrd_bytes)

        # cmdval can be none
        cmdval_bytes = b""
        if cmdval is not None:
            cmdval_byte_length = cmdval.bit_length() // 8 + (
                1 if cmdval.bit_length() % 8 != 0 else 0
            )
            cmdval_byte_length = max(cmdval_byte_length, 2)
            cmdval_bytes = cmdval.to_bytes(cmdval_byte_length, byteorder="little")
            data_length += cmdval_byte_length

        data_length = data_length.to_bytes(2, byteorder="little")

        # construct command
        cmd_packet = bytearray()
        cmd_packet.extend(HEADER)
        cmd_packet.extend(data_length)
        cmd_packet.extend(cmdwrd_bytes)
        if cmdval is not None:
            cmd_packet.extend(cmdval_bytes)
        cmd_packet.extend(FOOTER)

        # send command
        print(f"Sending config frame: {cmd_packet.hex()}")
        self.__ser.write(cmd_packet)

        # receive ACK
        answer = self.__ser.read_until(b"\x04\x03\x02\x01").hex()
        print(f"Received: {answer}")

        # get clean answer to return
        answer_regex = re.search(r"(?<=fdfcfbfa).*?(?=04030201)", answer)

        answer_clean = answer_regex.group(0) if answer_regex is not None else None

        return answer_clean

    """
    READ PERIODIC RADAR OUTPUT
    """

    def __read_target_state(self) -> str | None:
        radar_report = self.__ser.read_until(b"\xf8\xf7\xf6\xf5").hex()
        print(f"Radar read: {radar_report}")
        # only get intra-frame data
        # -> target data between the head (0xAA) and tail (0x55), see 2.3.1 in serial communiation docs
        report_regex = re.search(r"(?<=aa).*?(?=5500f8f7f6f5)", radar_report)

        report_clean = report_regex.group(0) if report_regex is not None else None

        return report_clean

    def __bytes_parser(self, byte_str: str) -> int:
        actual_bytes = bytes.fromhex(byte_str)
        return int.from_bytes(actual_bytes, "little")

    # TODO: investigate dropouts
    def update(self) -> bool:
        data_frame = self.__read_target_state()
        print(data_frame)

        if data_frame is None:
            return False

        # parsing return radar data
        self.__t_state = int(data_frame[:2], 16)
        self.__t_moving_distance = self.__bytes_parser(data_frame[2:6])
        self.__t_moving_energy = int(data_frame[6:8], 16)
        self.__t_stationary_distance = self.__bytes_parser(data_frame[8:12])
        self.__t_stationary_energy = int(data_frame[12:14], 16)
        self.__t_detection_distance = self.__bytes_parser(data_frame[14:18])

        self.__last_update_unix = time.time()

        # TODO: remove later, debugging output
        print(
            f"--- Parsed frame ---\n"
            f"State                 : 0x{data_frame[:2]}    → {self.__t_state_str(self.__t_state)}\n"
            f"Moving distance       : 0x{data_frame[2:6]}   → {self.__t_moving_distance}\n"
            f"Moving energy         : 0x{data_frame[6:8]}   → {self.__t_moving_energy}\n"
            f"Stationary distance   : 0x{data_frame[8:12]}  → {self.__t_stationary_distance}\n"
            f"Stationary energy     : 0x{data_frame[12:14]} → {self.__t_stationary_energy}\n"
            f"Detection distance    : 0x{data_frame[14:18]} → {self.__t_detection_distance}\n"
            f"Last Update           : {self.__last_update_unix}\n"
        )

        return True

    def __t_state_str(self, state: int) -> str:
        match state:
            case 0x00:
                return "None"
            case 0x01:
                return "Moving"
            case 0x02:
                return "Stationary"
            case 0x03:
                return "Moving and stationary"
            case 0x04:
                return "Doing noise detection"
            case 0x05:
                return "Noise detection succeeded"
            case 0x06:
                return "Noise detection failed"
            case _:
                return "Unknown"
