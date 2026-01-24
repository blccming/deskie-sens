import asyncio
import json
from datetime import datetime

import adafruit_scd4x
import board


class SCD4X:
    def __init__(self):
        self.i2c = board.I2C()
        self.scd = adafruit_scd4x.SCD4X(self.i2c)

    def configure(self):
        self.scd.start_periodic_measurement()

    async def get_json_report(self) -> str:
        while not self.scd.data_ready:
            await asyncio.sleep(0.05)

        co2 = await asyncio.to_thread(lambda: self.scd.CO2)
        temp = await asyncio.to_thread(lambda: self.scd.temperature)
        hum = await asyncio.to_thread(lambda: self.scd.relative_humidity)

        report = {
            "co2_ppm": co2,
            "temperature_C": round(temp, 1),
            "humidity_%": round(hum, 1),
            "last_updated": datetime.now().isoformat(),
        }

        return json.dumps(report, indent=4)
