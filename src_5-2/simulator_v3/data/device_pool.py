from typing import Dict, Optional
import threading
import logging

from data.virtual_device import VirtualDevice
from modbus.request_handler import ModbusRequestHandler

logger = logging.getLogger(__name__)


class DevicePool:
    def __init__(self):
        self._devices: Dict[int, VirtualDevice] = {}
        self._handlers: Dict[int, ModbusRequestHandler] = {}
        self._lock = threading.Lock()
        self._initialize_default_devices()

    def _initialize_default_devices(self):
        default_device = VirtualDevice(slave_id=1)
        self.add_device(default_device)
        logger.info("Initialized default device with slave_id=1")

    def add_device(self, device: VirtualDevice) -> bool:
        with self._lock:
            if device.slave_id in self._devices:
                logger.warning(f"Device with slave_id={device.slave_id} already exists, replacing")
            self._devices[device.slave_id] = device
            self._handlers[device.slave_id] = ModbusRequestHandler(device)
            logger.info(f"Added device: slave_id={device.slave_id}")
            return True

    def remove_device(self, slave_id: int) -> bool:
        with self._lock:
            if slave_id in self._devices:
                del self._devices[slave_id]
                if slave_id in self._handlers:
                    del self._handlers[slave_id]
                logger.info(f"Removed device: slave_id={slave_id}")
                return True
            return False

    def get_device(self, slave_id: int) -> Optional[VirtualDevice]:
        with self._lock:
            return self._devices.get(slave_id)

    def get_handler(self, slave_id: int) -> Optional[ModbusRequestHandler]:
        with self._lock:
            return self._handlers.get(slave_id)

    def get_all_slave_ids(self) -> list:
        with self._lock:
            return list(self._devices.keys())

    def device_exists(self, slave_id: int) -> bool:
        with self._lock:
            return slave_id in self._devices

    @property
    def default_device(self) -> Optional[VirtualDevice]:
        return self.get_device(1)

    def __len__(self) -> int:
        with self._lock:
            return len(self._devices)

    def __contains__(self, slave_id: int) -> bool:
        return self.device_exists(slave_id)