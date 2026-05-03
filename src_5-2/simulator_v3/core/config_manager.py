"""
Config Manager - Manages module configuration and data configuration
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import config


logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    """Data configuration for a collection point"""
    slave_id: int
    func_code: int
    start_addr: int
    quantity: int

    def __str__(self):
        return f"DataConfig(slave={self.slave_id}, func={self.func_code}, addr={self.start_addr}, qty={self.quantity})"


@dataclass
class ModuleConfig:
    """Module configuration"""
    send_mode: int = 0
    config_data: int = 0x001E
    baud: int = 0x05

    @property
    def send_interval(self) -> int:
        """Get send interval from config_data"""
        return self.config_data

    def __str__(self):
        return f"ModuleConfig(mode={self.send_mode}, interval={self.send_interval}s, baud={self.baud})"


class ConfigManager:
    """
    Config Manager - Manages module and data configurations

    Features:
    - Thread-safe configuration access
    - Default module configuration
    - Dynamic data configuration updates
    """

    def __init__(self):
        self._module_config = ModuleConfig()
        self._data_configs: List[DataConfig] = []
        self._lock = threading.Lock()

        self._on_data_config_callback: Optional[callable] = None

        logger.info(f"ConfigManager initialized with default module config: {self._module_config}")

    def get_module_config(self) -> ModuleConfig:
        """Get current module configuration"""
        with self._lock:
            return self._module_config

    def update_module_config(self, send_mode: int, config_data: int, baud: int):
        """Update module configuration"""
        with self._lock:
            old_interval = self._module_config.send_interval
            self._module_config = ModuleConfig(
                send_mode=send_mode,
                config_data=config_data,
                baud=baud,
            )
            new_interval = self._module_config.send_interval
            logger.info(f"Module config updated: interval changed from {old_interval}s to {new_interval}s")
            logger.debug(f"Module config: {self._module_config}")

    def get_data_configs(self) -> List[DataConfig]:
        """Get current data configurations"""
        with self._lock:
            return list(self._data_configs)

    def update_data_configs(self, configs: List[DataConfig]):
        """Update data configurations"""
        with self._lock:
            old_count = len(self._data_configs)
            self._data_configs = configs
            logger.info(f"Data config updated: {old_count} -> {len(configs)} configs")
            for i, cfg in enumerate(configs):
                logger.debug(f"  Config[{i}]: {cfg}")

        if self._on_data_config_callback:
            self._on_data_config_callback(configs)

    def clear_data_configs(self):
        """Clear all data configurations"""
        with self._lock:
            old_count = len(self._data_configs)
            self._data_configs = []
            logger.info(f"Data config cleared: {old_count} configs removed")

    def set_on_data_config_callback(self, callback: callable):
        """Set callback for data config updates"""
        self._on_data_config_callback = callback

    def has_data_configs(self) -> bool:
        """Check if there are data configurations"""
        with self._lock:
            return len(self._data_configs) > 0

    def add_data_config(self, config: 'DataConfig'):
        """Add a single data configuration"""
        with self._lock:
            for existing in self._data_configs:
                if (existing.slave_id == config.slave_id and
                    existing.func_code == config.func_code and
                    existing.start_addr == config.start_addr):
                    logger.debug(f"Data config already exists, skipping: {config}")
                    return
            self._data_configs.append(config)
            logger.info(f"Added data config: {config}")

    def remove_data_config(self, slave_id: int, func_code: int, start_addr: int) -> bool:
        """Remove a specific data configuration"""
        with self._lock:
            for i, cfg in enumerate(self._data_configs):
                if cfg.slave_id == slave_id and cfg.func_code == func_code and cfg.start_addr == start_addr:
                    del self._data_configs[i]
                    logger.info(f"Removed data config: {cfg}")
                    return True
            return False
