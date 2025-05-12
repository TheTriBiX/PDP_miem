import pytest
from unittest.mock import Mock, patch, call
import json
from iot_device import IoTDevice  # Замените на ваш модуль


class TestIoTDevice:
    @pytest.fixture
    def device(self):
        with patch('paho.mqtt.client.Client') as mock_mqtt:
            device = IoTDevice("test.broker")
            device.client = mock_mqtt.return_value
            yield device

    def test_initialization(self, device):
        """Проверка генерации данных устройства"""
        assert len(device.device_data["mac"].split(":")) == 6
        assert len(device.device_data["ip"].split(".")) == 4
        assert len(device.device_data["serial"]) == 32

    def test_connection_setup(self, device):
        """Проверка подписки на топик регистрации при подключении"""
        device.client.on_connect(None, None, None, 0)
        device.client.subscribe.assert_called_with("devices/register")

    def test_handle_registration(self, device):
        """Тест обработки регистрационного сообщения"""
        test_payload = json.dumps({
            "subscribe_topic": "sensors/temperature",
            "jwt": "test_token_123"
        })

        # Симулируем входящее сообщение
        msg_mock = Mock()
        msg_mock.topic = "devices/register"
        msg_mock.payload.decode.return_value = test_payload

        device.on_message(None, None, msg_mock)

        # Проверяем подписку на новый топик
        device.client.subscribe.assert_called_with("sensors/temperature")
        assert "sensors/temperature" in device.subscribed_topics

        # Проверяем сохранение JWT
        assert device.jwt_token == "test_token_123"

    def test_publish_with_jwt(self, device):
        """Проверка добавления JWT в заголовки"""
        device.jwt_token = "secure_token_abc"
        test_message = json.dumps({"status": "ok"})

        device.publish("test/topic", test_message)

        device.client.publish.assert_called_with(
            "test/topic",
            test_message,
            properties={'Authorization': 'Bearer secure_token_abc'}
        )

    def test_message_handling_with_jwt(self, device):
        """Тест обработки сообщения с существующим JWT"""
        device.jwt_token = "test_jwt_123"
        msg_mock = Mock()
        msg_mock.topic = "sensors/temperature"
        msg_mock.payload.decode.return_value = json.dumps({"command": "read"})

        device.on_message(None, None, msg_mock)

        expected_response = {
            "device_data": device.device_data,
            "jwt": "test_jwt_123",
            "message": "Processing your request"
        }
        device.client.publish.assert_called_with(
            "sensors/temperature/response",
            json.dumps(expected_response)
        )

    def test_message_handling_without_jwt(self, device):
        """Тест обработки сообщения без JWT"""
        device.jwt_token = None
        msg_mock = Mock()
        msg_mock.topic = "sensors/humidity"
        msg_mock.payload.decode.return_value = json.dumps({"command": "read"})

        device.on_message(None, None, msg_mock)

        expected_response = {
            "device_data": device.device_data,
            "message": "No auth token available"
        }
        device.client.publish.assert_called_with(
            "sensors/humidity/response",
            json.dumps(expected_response)
        )

    @patch('time.sleep')
    def test_periodic_status_updates(self, mock_sleep, device):
        """Тест периодической отправки статуса"""
        device.start()
        device.publish("devices/status", json.dumps(device.device_data))

        # Симулируем 2 цикла отправки
        device.client.publish.reset_mock()
        device.run_periodic_updates(interval=0.1, max_cycles=2)

        assert device.client.publish.call_count == 2
        calls = [
            call("devices/status", json.dumps(device.device_data)),
            call("devices/status", json.dumps(device.device_data))
        ]
        device.client.publish.assert_has_calls(calls)

    def test_invalid_registration_message(self, device, caplog):
        """Тест обработки некорректного сообщения регистрации"""
        msg_mock = Mock()
        msg_mock.topic = "devices/register"
        msg_mock.payload.decode.return_value = "invalid_json"

        device.on_message(None, None, msg_mock)

        assert "Invalid JSON received" in caplog.text


if __name__ == "__main__":
    pytest.main(["-v"])