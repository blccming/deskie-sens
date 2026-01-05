### deskie-sens
This project aims to create a Raspberry Pi HAT and supporting software to extend the Raspberry Pi's functionality to being a sensor hub/bearer. I aim to implement a variety of sensors and other peripherals and making them accessible via an API and to Home Assistant for home automation. I plan to use the Pi with its HAT as a desk clock to add to its sensor-bearing functionality.

#### Current state of development
- Evaluating hardware options
- Designing software architecture
- Implementing sensor drivers

#### Setup steps for development at this stage
- In `raspi-config` enable serial port and disable serial login shell (or enable_uart=1 in config.txt)
- Execute these commands
```sh
sudo apt update && apt upgrade -y
sudo apt install python3-serial python3-paho-mqtt
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
