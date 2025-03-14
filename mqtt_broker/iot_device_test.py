import paho.mqtt.client as mqtt
import json
import time

BROKER = "127.0.0.1"
PORT = 1883
DEVICE_ID_1 = "temperature-sensor-1"
DEVICE_ID_2 = "wet-sensor-2"
DEVICE_ID_3 = "pressure-sensor-3"
REGISTER_TOPIC = "devices/register"

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.connect(BROKER, PORT, 60)
devices = [
    {
        "device_id": DEVICE_ID_1,
        "device_type": "temperature_sensor"
    },
    {
        "device_id": DEVICE_ID_2,
        "device_type": "wet_sensor"
    },
    {
        "device_id": DEVICE_ID_3,
        "device_type": "pressure_sensor"
    },
]
for device in devices:
    mqttc.publish(REGISTER_TOPIC, json.dumps(device))
    print(f"Device {device['device_id']} registered!")


# while True:
#     temp_data = {
#         "device_id": DEVICE_ID,
#         "temperature": 22.5
#     }
#     mqttc.publish(f"devices/{DEVICE_ID}/data", json.dumps(temp_data))
#     time.sleep(5)
