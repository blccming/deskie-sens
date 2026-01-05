## TODO

MQTT
- use MQTT for config -> executing sensor reset etc.

Logging
- add log levels

Docker
- add docker deployment option
- add mosquitto container for testing / no longer being reliant on mosquitto test server

LD2410C
- investigate dropouts in radar read
- test automatic calibration, even though stock calibration seems just fine

SI1145 and SCD40
- initial test implementation
- evaluate sensor
- I2C HAL / parent class?

Waveshare Pico-8SEG-LED
- initial test implementation

Config
- add config file

Home Assistant
- add home assistant support via MQTT (and device configuration via HTTP?)
- add home assistant templates to repo for adding device
