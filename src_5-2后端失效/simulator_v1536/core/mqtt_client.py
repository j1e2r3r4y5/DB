"""
MQTT Client Manager - Handles MQTT connection and messaging
"""

import logging
import threading
import time
from typing import Optional, Callable

import paho.mqtt.client as mqtt

from config import config


logger = logging.getLogger(__name__)


class MQTTClientManager:
    """
    MQTT Client Manager - Manages MQTT connection, subscription, and messaging

    Features:
    - Automatic reconnection with exponential backoff
    - QoS 0/2 support for down/uplink
    - Thread-safe publishing
    - Connection state tracking
    """

    def __init__(
        self,
        broker: str = None,
        port: int = None,
        client_id: str = None,
        up_topic: str = None,
        down_topic: str = None,
    ):
        self.broker = broker or config.MQTT_BROKER
        self.port = port or config.MQTT_PORT
        self.client_id = client_id or f"dtu_sim_{config.DEVICE_SERIAL}_{int(time.time())}"
        self.up_topic = up_topic or config.UP_TOPIC
        self.down_topic = down_topic or config.DOWN_TOPIC

        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._running = False
        self._on_message_callback: Optional[Callable] = None

        self._reconnect_delay = 5
        self._max_reconnect_delay = 60
        self._max_reconnect_attempts = 10
        self._reconnect_attempts = 0
        self._lock = threading.Lock()

        logger.info(f"MQTTClientManager initialized: {self.broker}:{self.port}")

    def connect(self) -> bool:
        """Connect to MQTT Broker"""
        try:
            self._client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv311,
                clean_session=True,
            )

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            self._client.on_subscribe = self._on_subscribe

            self._client.keepalive = config.MQTT_KEEPALIVE
            self._client.reconnect_delay_set(min_delay=self._reconnect_delay, max_delay=self._max_reconnect_delay)

            logger.info(f"Connecting to MQTT broker: {self.broker}:{self.port}")
            self._client.connect(self.broker, self.port, keepalive=config.MQTT_KEEPALIVE)
            self._client.loop_start()

            self._running = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT Broker"""
        with self._lock:
            self._running = False
            if self._client:
                try:
                    self._client.loop_stop()
                    self._client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting MQTT: {e}")
                finally:
                    self._client = None
                    self._connected = False
        logger.info("Disconnected from MQTT broker")

    def publish(self, topic: str, payload: bytes, qos: int = 2) -> bool:
        """Publish message to topic"""
        if not self._connected:
            logger.warning("Cannot publish: not connected")
            return False

        with self._lock:
            try:
                result = self._client.publish(topic, payload, qos)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"Published to {topic}: {payload.hex()}")
                    return True
                else:
                    logger.error(f"Failed to publish: {mqtt.error_string(result.rc)}")
                    return False
            except Exception as e:
                logger.error(f"Error publishing: {e}")
                return False

    def subscribe(self, topic: str = None, qos: int = 2) -> bool:
        """Subscribe to topic"""
        topic = topic or self.down_topic
        if not self._client:
            logger.error("Cannot subscribe: client not initialized")
            return False

        try:
            result, _ = self._client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to {topic} with QoS {qos}")
                return True
            else:
                logger.error(f"Failed to subscribe: {mqtt.error_string(result)}")
                return False
        except Exception as e:
            logger.error(f"Error subscribing: {e}")
            return False

    def set_on_message_callback(self, callback: Callable):
        """Set callback for received messages"""
        self._on_message_callback = callback

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self._connected = True
            self._reconnect_delay = 5
            self._reconnect_attempts = 0
            logger.info("MQTT connected successfully")

            self.subscribe(self.down_topic, config.MQTT_QOS_DOWN)
        else:
            reason_codes = {
                1: "Protocol version mismatch",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }
            logger.error(f"MQTT connection failed: {rc} - {reason_codes.get(rc, 'Unknown')}")
            self._connected = False

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        logger.warning(f"MQTT disconnected with code {rc}")
        self._connected = False

        if self._running and rc != 0:
            self._schedule_reconnect()

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """MQTT subscribe callback"""
        logger.info(f"Subscribed successfully, granted QoS: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            logger.info(f"[DOWNLINK] Topic: {msg.topic}, QoS: {msg.qos}, Payload: {msg.payload.hex()}")

            if self._on_message_callback:
                self._on_message_callback(msg.payload)
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    def _schedule_reconnect(self):
        """Schedule reconnection with exponential backoff"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached. Giving up.")
            return

        delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
        logger.info(f"Scheduling reconnect in {delay} seconds... (attempt {self._reconnect_attempts + 1}/{self._max_reconnect_attempts})")
        threading.Timer(delay, self._attempt_reconnect).start()

    def _attempt_reconnect(self):
        """Attempt to reconnect"""
        if not self._running:
            return

        self._reconnect_attempts += 1
        logger.info(f"Attempting MQTT reconnection... (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})")
        if self.connect():
            logger.info("Reconnected successfully")
        else:
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached. Giving up.")
                return
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            self._schedule_reconnect()
