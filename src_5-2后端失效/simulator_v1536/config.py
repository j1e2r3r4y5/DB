"""
Configuration module - Centralized configuration for DTU Simulator
"""

import os


class Config:
    """Configuration class for DTU Simulator"""

    MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_KEEPALIVE = 60
    MQTT_QOS_UP = 2
    MQTT_QOS_DOWN = 0

    DEVICE_SERIAL = os.getenv("DEVICE_SERIAL", "A1B2C3D4")
    UP_TOPIC = f"/dtu/{DEVICE_SERIAL}/up"
    DOWN_TOPIC = f"/dtu/{DEVICE_SERIAL}/down"

    MODBUS_HOST = os.getenv("MODBUS_HOST", "127.0.0.1")
    MODBUS_PORT = int(os.getenv("MODBUS_PORT", "502"))
    MODBUS_TIMEOUT = 5.0
    MODBUS_POOL_SIZE = 3

    HEARTBEAT_INTERVAL = 30
    DATA_UPLOAD_INTERVAL = 30

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DEFAULT_SLAVE_ID = 1

    FUNCTION_CODES = {
        "HEARTBEAT": 0x00,
        "MODULE_CONFIG_QUERY": 0x01,
        "MODULE_CONFIG_UPLOAD": 0x01,
        "DOWNLOAD_MODULE_CONFIG": 0x02,
        "MODULE_CONFIG_RESULT": 0x02,
        "DATA_CONFIG_QUERY": 0x03,
        "DATA_CONFIG_UPLOAD": 0x03,
        "DOWNLOAD_DATA_CONFIG": 0x04,
        "CONFIG_RESULT": 0x04,
        "DATA_UPLOAD": 0x05,
        "REMOTE_WRITE": 0x06,
    }

    REGION_TO_FUNC_CODE = {
        0: 0x01,
        1: 0x02,
        3: 0x04,
        4: 0x03,
    }

    # 按照分析报告中的示例变量地址定义
    # 变量1: 温度(float32), 地址 0, 2 个寄存器
    SLAVE_1_HOLDING_REG_TEMPERATURE = 0
    # 变量2: 湿度(int16), 地址 2, 1 个寄存器
    SLAVE_1_HOLDING_REG_HUMIDITY = 2
    # 变量3: 功率(float64), 地址 3, 4 个寄存器
    SLAVE_1_HOLDING_REG_POWER = 3
    # 变量4: 累计电能(int32), 地址 7, 2 个寄存器
    SLAVE_1_HOLDING_REG_ENERGY = 7
    # 变量5: 开关状态(bool), 线圈地址 0
    SLAVE_1_COIL_SWITCH = 0
    # 变量6: 设备描述(string), 地址 10, 10 个寄存器
    SLAVE_1_HOLDING_REG_DEVICE_DESC = 10

    DEFAULT_SLAVE_1_REGISTERS = {
        "temperature": {"addr": SLAVE_1_HOLDING_REG_TEMPERATURE, "type": 4, "init_value": 250},
        "humidity": {"addr": SLAVE_1_HOLDING_REG_HUMIDITY, "type": 4, "init_value": 600},
        "power": {"addr": SLAVE_1_HOLDING_REG_POWER, "type": 4, "init_value": 1500},
        "energy": {"addr": SLAVE_1_HOLDING_REG_ENERGY, "type": 4, "init_value": 1000},
    }

    DEFAULT_SLAVE_1_COILS = {
        "switch": {"addr": SLAVE_1_COIL_SWITCH, "init_value": 1},
    }

    DEFAULT_TEST_DATA = {
        "temperature": {"addr": 0, "type": 4, "init_value": 250, "min": 200, "max": 300},
        "humidity": {"addr": 2, "type": 4, "init_value": 600, "min": 500, "max": 700},
        "switch": {"addr": 0, "type": 0, "init_value": 1},
        "power": {"addr": 3, "type": 4, "init_value": 15000, "min": 14000, "max": 16000},
        "energy": {"addr": 7, "type": 4, "init_value": 100000, "min": 90000, "max": 110000},
    }


config = Config()
