"""
Unit tests for MQTT Client Manager
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMQTTClientManagerReconnect(unittest.TestCase):
    """Test MQTT reconnection logic"""

    @patch('core.mqtt_client.mqtt')
    def test_max_reconnect_attempts(self, mock_mqtt):
        """Test that reconnection stops after max attempts"""
        from core.mqtt_client import MQTTClientManager

        mock_client_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_client_instance
        mock_client_instance.connect.return_value = 0
        mock_client_instance.loop_start.return_value = None

        manager = MQTTClientManager()
        manager._running = True
        manager._max_reconnect_attempts = 3
        manager._reconnect_attempts = 3

        manager._schedule_reconnect()

        self.assertEqual(manager._reconnect_attempts, 3)

    @patch('core.mqtt_client.mqtt')
    def test_reconnect_attempts_increment(self, mock_mqtt):
        """Test that reconnect attempts are counted"""
        from core.mqtt_client import MQTTClientManager

        mock_client_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_client_instance
        mock_client_instance.connect.return_value = 0
        mock_client_instance.loop_start.return_value = None

        manager = MQTTClientManager()
        manager._running = True
        manager._max_reconnect_attempts = 10
        manager._reconnect_attempts = 0

        manager._attempt_reconnect()

        self.assertEqual(manager._reconnect_attempts, 1)

    @patch('core.mqtt_client.mqtt')
    def test_reconnect_attempts_reset_on_success(self, mock_mqtt):
        """Test that reconnect attempts reset on successful connection"""
        from core.mqtt_client import MQTTClientManager

        mock_client_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_client_instance
        mock_client_instance.connect.return_value = 0
        mock_client_instance.loop_start.return_value = None
        mock_client_instance.subscribe.return_value = (0, [])

        manager = MQTTClientManager()
        manager._running = True
        manager._max_reconnect_attempts = 10
        manager._reconnect_attempts = 5

        manager._on_connect(mock_client_instance, None, None, 0)

        self.assertEqual(manager._reconnect_attempts, 0)

    @patch('core.mqtt_client.mqtt')
    def test_no_reconnect_when_not_running(self, mock_mqtt):
        """Test that reconnection is not attempted when running flag is False"""
        from core.mqtt_client import MQTTClientManager

        mock_client_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_client_instance

        manager = MQTTClientManager()
        manager._running = False

        manager._attempt_reconnect()

        mock_client_instance.connect.assert_not_called()


class TestMQTTQoSConfiguration(unittest.TestCase):
    """Test MQTT QoS configuration"""

    def test_qos_constants_defined(self):
        """Test that QoS constants are properly defined"""
        from config import config

        self.assertEqual(config.MQTT_QOS_UP, 2)
        self.assertEqual(config.MQTT_QOS_DOWN, 0)

    @patch('core.mqtt_client.mqtt')
    def test_subscribe_uses_down_qos(self, mock_mqtt):
        """Test that subscription uses configured QoS"""
        from core.mqtt_client import MQTTClientManager
        from config import config

        mock_client_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_client_instance
        mock_client_instance.connect.return_value = 0
        mock_client_instance.loop_start.return_value = None
        mock_client_instance.subscribe.return_value = (0, [])

        manager = MQTTClientManager()
        manager.connect()

        manager.subscribe(manager.down_topic, config.MQTT_QOS_DOWN)

        mock_client_instance.subscribe.assert_called_with(manager.down_topic, config.MQTT_QOS_DOWN)


if __name__ == '__main__':
    unittest.main()
