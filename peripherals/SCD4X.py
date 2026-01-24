import adafruit_scd4x
import board


class SCD4X:
    def __init__(self):
        self.i2c = board.I2C()
        self.scd = adafruit_scd4x.SCD4X(self.i2c)

    def configure(self):
        self.scd.start_periodic_measurement()

    def get_json_report(self) -> str:
        if self.scd.data_ready:
            print("CO2: %d ppm" % self.scd.CO2)
            print("Temperature: %0.1f *C" % self.scd.temperature)
            print("Humidity: %0.1f %%" % self.scd.relative_humidity)
            print()
