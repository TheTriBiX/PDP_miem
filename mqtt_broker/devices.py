import json
import uuid
import paho.mqtt.client as mqtt
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IoTDevice")


class IoTDevice:
    def __init__(self, broker_address):
        self.client = mqtt.Client(client_id=f"device_{uuid.uuid4().hex[:6]}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.broker = broker_address
        self.jwt_token = None
        self.subscribed_topics = set()

        # Генерация данных устройства
        self.device_data = {
            "mac": ":".join([f"{random.randint(0x00, 0xff):02x}" for _ in range(6)]),
            "ip": ".".join(map(str, (random.randint(0, 255) for _ in range(4)))),
            "serial": uuid.uuid4().hex
        }

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to broker {self.broker}")
        # Подписка на топик регистрации при подключении
        self.subscribe("devices/register")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        logger.info(f"Received message on {topic}: {payload}")

        if topic == "devices/register":
            self.handle_registration(payload)
        else:
            self.handle_custom_topic(topic, payload)

    def handle_registration(self, payload):
        try:
            data = json.loads(payload)
            # Подписка на новый топик из сообщения
            new_topic = data.get("subscribe_topic")
            if new_topic:
                self.subscribe(new_topic)

            # Сохранение JWT токена
            if "jwt" in data:
                self.jwt_token = data["jwt"]
                logger.info("JWT token updated")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")

    def handle_custom_topic(self, topic, payload):
        # Обработка сообщений в кастомных топиках
        logger.info(f"Processing message in {topic}")

        # Отправка ответа с JWT если есть
        if self.jwt_token:
            response = {
                "device_data": self.device_data,
                "jwt": self.jwt_token,
                "message": "Processing your request"
            }
        else:
            response = {
                "device_data": self.device_data,
                "message": "No auth token available"
            }

        self.publish(f"{topic}/response", json.dumps(response))

    def subscribe(self, topic):
        if topic not in self.subscribed_topics:
            self.client.subscribe(topic)
            self.subscribed_topics.add(topic)
            logger.info(f"Subscribed to {topic}")

    def publish(self, topic, message):
        # Добавляем JWT в заголовки если есть
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        self.client.publish(topic, payload=message, properties=headers)
        logger.info(f"Published to {topic}: {message}")

    def start(self):
        self.client.connect(self.broker)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    # Пример использования
    device = IoTDevice("mqtt.eclipseprojects.io")
    device.start()

    try:
        while True:
            # Имитация периодической отправки данных
            device.publish("devices/status", json.dumps(device.device_data))
            time.sleep(30)

    except KeyboardInterrupt:
        device.stop()
        logger.info("Device stopped")