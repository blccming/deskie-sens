import asyncio
import json
from datetime import datetime

import adafruit_si1145
import board


class SI1145:
    def __init__(self):
        self.i2c = board.I2C()
        self.si = adafruit_si1145.SI1145(self.i2c)

    async def get_json_report(self) -> str:
        vis, ir = await asyncio.to_thread(lambda: self.si.als)
        uv = await asyncio.to_thread(lambda: self.si.uv_index)

        report = {
            "visible": vis,
            "infrared": ir,
            "uv_index": uv,
            "last_updated": datetime.now().isoformat(),
        }

        return json.dumps(report, indent=4)
