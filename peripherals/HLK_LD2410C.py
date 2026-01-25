import json
from datetime import datetime

from aio_ld2410 import LD2410


class HLK_LD2410C:
    def __init__(self):
        self.port = "/dev/ttyS0"

    async def configure(self) -> None:
        async with LD2410(self.port) as device:
            async with device.configure():
                device.reset_to_factory()
                device.set_bluetooth_mode(False)

    async def get_json_report(self) -> str:
        report = {}

        async with LD2410(self.port) as device:
            rep = await device.get_next_report()
            rep = rep.basic

            report["state"] = rep.target_status  # figure out the output
            report["detection_distance"] = rep.detection_distance

            report["moving"] = {
                "distance": rep.moving_distance,
                "energy": rep.moving_energy,
            }

            report["static"] = {
                "distance": rep.static_distance,
                "energy": rep.static_energy,
            }

            report["last_updated"] = datetime.now().isoformat()

        return json.dumps(report, indent=4)
