import paho.mqtt.client as mqtt
import os
import django
import json
import uuid

from django.utils.timezone import now

from mqtt_broker.iot_device_test import mqttc

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PDP.settings')
django.setup()
from group_police.models import IoTDevice, IoTMessage

class MQTTBrokerListener:
    def __init__(self):
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = on_connect
        self.mqttc.on_message = on_message

        self.mqttc.connect_async("127.0.0.1", 1883, 60)

    def send_message(self, topic, msg):
        self.mqttc.publish(topic, msg)


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Client-listener started working")
    client.subscribe("devices/register")


def on_message(client, userdata, msg):
    message = json.loads(msg.payload)
    try:
        device = IoTDevice.objects.get(
            device_name=message.get('device_id', str(uuid.uuid4())),
            device_type=message.get('device_type', 'unknown_type'),
        )
    except IoTDevice.DoesNotExist:
        device = IoTDevice.objects.create(
            device_name=message.get('device_id', str(uuid.uuid4())),
            device_type=message.get('device_type', 'unknown_type'),
            uid=str(uuid.uuid4()),
        )
    if msg.topic == 'devices/register':
        client.subscribe(f"devices/{device.device_name}/data")
    else:
        IoTMessage.objects.create(
            device=device,
            msg=message,
            topic=msg.topic,
        )
    device.last_seen = now()
    device.save()


MQTT_LISTENER = MQTTBrokerListener()
