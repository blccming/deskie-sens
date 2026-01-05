import json
import re
import time

import serial


class LD2410C:
    def __init__(self):
        self.__ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=256000,
            timeout=0.5,
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
        self.__last_update_human_readable: str = ""

    def init(self) -> bool:
        self.__ser.flush()

        print("enabling config")
        if not self.__enable_config():
            return False

        print("factory rest")
        if not self.factory_reset():
            return False

        print("setting ble")
        if not self.set_bluetooth(False):
            return False

        print("enabling restarting")
        if not self.restart():
            return False

        time.sleep(0.5)

        print("disabling config")
        if not self.__disable_config():
            pass  # radar doesn't seem to answer, so return is False

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
            return False

        if measurement_duration > 0xFFFF:
            return False

        return self.__config_transceive(0x000B, measurement_duration) == "04000b010000"

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
        print(f"Received: {answer}\n")

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
        self.__last_update_human_readable = time.ctime()

        # TODO: remove later, debugging output
        print(
            f"--- Parsed frame ---\n"
            f"State                 : 0x{data_frame[:2]}    → {self.__t_state_str()}\n"
            f"Moving distance       : 0x{data_frame[2:6]}   → {self.__t_moving_distance}\n"
            f"Moving energy         : 0x{data_frame[6:8]}   → {self.__t_moving_energy}\n"
            f"Stationary distance   : 0x{data_frame[8:12]}  → {self.__t_stationary_distance}\n"
            f"Stationary energy     : 0x{data_frame[12:14]} → {self.__t_stationary_energy}\n"
            f"Detection distance    : 0x{data_frame[14:18]} → {self.__t_detection_distance}\n"
            f"Last Update           : {self.__last_update_unix}\n"
        )

        return True

    def __t_state_str(self) -> str:
        match self.__t_state:
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

    """
    MAKE DATA AVAILABLE TO STATE MACHINE
    """

    def get_last_updated(self) -> str:
        return str(self.__last_update_human_readable)

    def get_data_json(self) -> str:
        data = {}

        data["state"] = self.__t_state_str()
        data["detection_distance"] = self.__t_detection_distance

        data["moving"] = {
            "state": self.__t_state == 0x01 or self.__t_state == 0x03,
            "distance": self.__t_moving_distance,
            "energy": self.__t_moving_energy,
        }

        data["stationary"] = {
            "state": self.__t_state == 0x02 or self.__t_state == 0x03,
            "distance": self.__t_stationary_distance,
            "energy": self.__t_stationary_energy,
        }

        data["last_update"] = self.__last_update_human_readable
        data["last_update_unix"] = self.__last_update_unix

        return json.dumps(data, indent=4)
