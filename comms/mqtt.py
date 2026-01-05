import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


class MQTT:
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # reconnect subscriptions here

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))

    def __init__(self):
        self.__mqttc = mqtt.Client(CallbackAPIVersion.VERSION2)
        self.__mqttc.on_connect = self.on_connect
        self.__mqttc.on_message = self.on_message
        self.__mqttc.connect("test.mosquitto.org", 1883, 60)

    def publish(self, topic: str, payload: str):
        self.__mqttc.loop_start()
        self.__mqttc.publish(topic, payload, qos=0)
        self.__mqttc.loop_stop()
