"""
DTU+Modbus Simulator - Main Entry Point
"""

import logging
import signal
import sys
import threading
import time
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from core.mqtt_client import MQTTClientManager
from core.modbus_master import ModbusMaster
from core.config_manager import ConfigManager, DataConfig
from modbus.tcp_server import ModbusTCPServer
from modbus.request_handler import ModbusRequestHandler
from data.device_pool import DevicePool
from data.virtual_device import VirtualDevice
from data.data_scheduler import DataScheduler, DataCollectionJob
from data.address_segment import AddressSegmentManager, create_default_segments
from protocol.handler import HandlerRegistry
from protocol.heartbeat_handler import HeartbeatHandler
from protocol.module_config_handler import ModuleConfigHandler
from protocol.data_config_handler import DataConfigHandler
from protocol.remote_write_handler import RemoteWriteHandler


logger = logging.getLogger(__name__)


class DTUSimulator:
    def __init__(self):
        self._running = False
        self._pending_data = []

        self.device_pool = DevicePool()
        self.config_manager = ConfigManager()
        self.address_manager: Optional[AddressSegmentManager] = None
        self.mqtt_manager: Optional[MQTTClientManager] = None
        self.modbus_master: Optional[ModbusMaster] = None
        self.modbus_tcp_server: Optional[ModbusTCPServer] = None
        self.data_scheduler: Optional[DataScheduler] = None

        self.handler_registry = HandlerRegistry()
        self.heartbeat_handler: Optional[HeartbeatHandler] = None
        self.module_config_handler: Optional[ModuleConfigHandler] = None
        self.data_config_handler: Optional[DataConfigHandler] = None
        self.remote_write_handler: Optional[RemoteWriteHandler] = None

        self._heartbeat_thread: Optional[threading.Thread] = None
        self._data_upload_thread: Optional[threading.Thread] = None

    def initialize(self, use_address_segments: bool = True, config_file: str = None):
        logger.info("Initializing DTU Simulator...")

        self._setup_logging()
        self._initialize_components()
        self._register_handlers()
        self._setup_device_pool()

        if use_address_segments:
            self._setup_address_segments(config_file)
        else:
            self._setup_default_data_configs()

        self._setup_modbus_tcp_server()
        self._setup_data_scheduler()

        logger.info("DTU Simulator initialized successfully")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def _initialize_components(self):
        self.mqtt_manager = MQTTClientManager()
        self.modbus_master = ModbusMaster()
        self.data_scheduler = DataScheduler(self.modbus_master)

    def _register_handlers(self):
        self.heartbeat_handler = HeartbeatHandler()
        self.module_config_handler = ModuleConfigHandler(self.config_manager)
        self.data_config_handler = DataConfigHandler(self.config_manager)
        self.remote_write_handler = RemoteWriteHandler(self.modbus_master)

        self.handler_registry.register(self.heartbeat_handler)
        self.handler_registry.register(self.module_config_handler)
        self.handler_registry.register(self.data_config_handler)
        self.handler_registry.register(self.remote_write_handler)

        self.mqtt_manager.set_on_message_callback(self._on_downlink_message)

        logger.info("Protocol handlers registered")

    def _setup_device_pool(self):
        # virtual_device.py 中的 _initialize_default_data 已经完成了初始化，这里不再重复设置
        logger.info("Device pool initialized")

    def _setup_default_data_configs(self):
        # 设置默认的数据配置
        default_configs = [
            DataConfig(
                slave_id=1,
                func_code=3,  # 保持寄存器
                start_addr=0,
                quantity=2    # 温度
            ),
            DataConfig(
                slave_id=1,
                func_code=3,
                start_addr=2,
                quantity=1    # 湿度
            ),
            DataConfig(
                slave_id=1,
                func_code=3,
                start_addr=3,
                quantity=4    # 功率
            ),
            DataConfig(
                slave_id=1,
                func_code=3,
                start_addr=7,
                quantity=2    # 电能
            ),
            DataConfig(
                slave_id=1,
                func_code=3,
                start_addr=10,
                quantity=10   # 设备描述，10个寄存器=20字节
            )
        ]
        self.config_manager.update_data_configs(default_configs)
        logger.info(f"Default data configs set: {len(default_configs)} configs")

    def _setup_modbus_tcp_server(self):
        self.modbus_tcp_server = ModbusTCPServer(
            host=config.MODBUS_HOST,
            port=config.MODBUS_PORT
        )

        for slave_id in self.device_pool.get_all_slave_ids():
            device = self.device_pool.get_device(slave_id)
            if device:
                handler = ModbusRequestHandler(device)
                self.modbus_tcp_server.set_device_handler(slave_id, handler)

        logger.info("Modbus TCP server configured")

    def _setup_data_scheduler(self):
        self.data_scheduler.set_on_data_callback(self._on_data_collected)
        self.data_config_handler.config_manager = self.config_manager
        self.config_manager.set_on_data_config_callback(self._on_data_config_updated)
        logger.info("Data scheduler configured")

    def _setup_address_segments(self, config_file: str = None):
        """设置地址段配置"""
        if config_file and os.path.exists(config_file):
            self.address_manager = AddressSegmentManager()
            count = self.address_manager.load_from_file(config_file)
            logger.info(f"Loaded {count} address segments from {config_file}")
        else:
            self.address_manager = create_default_segments()
            logger.info("Using default address segments configuration")

        # 排序地址段
        self.address_manager.sort_segments()
        # 生成变量
        self.address_manager.generate_variables()

        # 加载到设备
        device = self.device_pool.get_device(1)
        if device:
            device.load_address_segments(self.address_manager)
            logger.info("Address segments loaded to virtual device")

            # 从地址段生成数据采集配置
            self._setup_data_configs_from_segments()

    def _setup_data_configs_from_segments(self):
        """从地址段配置生成数据采集配置 - 合并相同区域的连续地址段"""
        if not self.address_manager:
            return

        # 按区域分组
        segments_by_region = {}
        for segment in self.address_manager.get_segments():
            if segment.region not in segments_by_region:
                segments_by_region[segment.region] = []
            segments_by_region[segment.region].append(segment)

        configs = []
        for region, segs in segments_by_region.items():
            if not segs:
                continue
                
            # 找到最小起始地址和最大结束地址
            addrs = []
            for seg in segs:
                addrs.append(seg.start_addr)
                addrs.append(seg.start_addr + seg.length - 1)
                
            start_addr = min(addrs)
            end_addr = max(addrs)
            length = end_addr - start_addr + 1
            
            func_code = AddressSegmentManager.REGION_TO_FUNC_CODE.get(region, 0x03)
            
            data_config = DataConfig(
                slave_id=1,
                func_code=func_code,
                start_addr=start_addr,
                quantity=length
            )
            configs.append(data_config)
            logger.debug(f"Merged region {region}: addr {start_addr}-{end_addr} (len {length}")

        self.config_manager.update_data_configs(configs)
        logger.info(f"Set up {len(configs)} merged data configs from address segments")

    def _on_downlink_message(self, payload: bytes):
        logger.info(f"[DOWNLINK] Received: {payload.hex()}")

        response = self.handler_registry.handle(payload)
        if response:
            logger.info(f"[UPLINK] Sending response: {response.hex()}")
            self.mqtt_manager.publish(self.mqtt_manager.up_topic, response, config.MQTT_QOS_UP)

    def _on_data_collected(self, job_id: str, slave_id: int, func_code: int, start_addr: int, quantity: int, data: bytes):
        logger.debug(f"Data collected: job={job_id}, slave={slave_id}, func={func_code}, addr={start_addr}, qty={quantity}, data={data.hex()}")

        try:
            self._pending_data.append({
                'slave_id': slave_id,
                'func_code': func_code,
                'start_addr': start_addr,
                'quantity': quantity,
                'data': data
            })
        except Exception as e:
            logger.error(f"Error in data collection callback: {e}")

    def _on_data_config_updated(self, configs):
        logger.info(f"Data config updated: {len(configs)} configs")

        if len(configs) == 0:
            logger.warning("CLEARING ALL DATA COLLECTION JOBS - DATA UPLOAD WILL STOP")
        else:
            logger.info(f"Creating {len(configs)} new data collection jobs")

        self.data_scheduler._jobs.clear()

        interval = self.config_manager.get_module_config().send_interval
        if interval <= 0:
            interval = 30

        for i, cfg in enumerate(configs):
            job_id = f"data_job_{i}"
            job = DataCollectionJob(
                job_id=job_id,
                slave_id=cfg.slave_id,
                func_code=cfg.func_code,
                start_addr=cfg.start_addr,
                quantity=cfg.quantity,
                interval=interval
            )
            self.data_scheduler.add_job(job)

        logger.info(f"Created {len(configs)} data collection jobs with interval {interval}s")

    def start(self):
        if self._running:
            logger.warning("Simulator already running")
            return

        self._running = True

        logger.info("Starting DTU Simulator...")

        try:
            self.modbus_tcp_server.start()
            logger.info("Modbus TCP server started")
        except Exception as e:
            logger.error(f"Failed to start Modbus TCP server: {e}")

        if self.mqtt_manager.connect():
            logger.info("MQTT connected")
        else:
            logger.error("Failed to connect to MQTT broker")

        self.data_scheduler.start()
        logger.info("Data scheduler started")

        self._start_heartbeat_loop()
        self._start_data_upload_loop()

        logger.info("DTU Simulator started successfully")

    def _start_heartbeat_loop(self):
        def heartbeat_loop():
            while self._running:
                try:
                    heartbeat_payload = self.heartbeat_handler._handle_heartbeat(bytes([0x00]))
                    if heartbeat_payload and self.mqtt_manager.is_connected():
                        self.mqtt_manager.publish(
                            self.mqtt_manager.up_topic,
                            heartbeat_payload,
                            config.MQTT_QOS_UP
                        )
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")

                time.sleep(config.HEARTBEAT_INTERVAL)

        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _start_data_upload_loop(self):
        def data_upload_loop():
            last_upload_time = 0

            while self._running:
                time.sleep(1)
                if not self.mqtt_manager.is_connected():
                    continue

                try:
                    configs = self.config_manager.get_data_configs()
                    if not configs:
                        # 每30秒输出一次日志，防止刷屏
                        if int(time.time()) % 30 == 0:
                            logger.debug("No data configs - skipping upload")
                        continue

                    current_time = time.time()
                    interval = self.config_manager.get_module_config().send_interval
                    if interval <= 0:
                        interval = 30

                    if current_time - last_upload_time >= interval:
                        self._simulate_data_changes()

                        payload = bytes([0x05])
                        payload += len(configs).to_bytes(2, 'big')

                        for cfg in configs:
                            device = self.device_pool.get_device(cfg.slave_id)
                            if not device:
                                continue

                            if cfg.func_code == 3:
                                data = device.read_holding_registers(cfg.start_addr, cfg.quantity)
                            elif cfg.func_code == 4:
                                data = device.read_input_registers(cfg.start_addr, cfg.quantity)
                            elif cfg.func_code == 1:
                                data = device.read_coils(cfg.start_addr, cfg.quantity)
                            elif cfg.func_code == 2:
                                data = device.read_discrete_inputs(cfg.start_addr, cfg.quantity)
                            else:
                                continue

                            # 功能码转分区号：0x01→0区，0x02→1区，0x03→4区，0x04→3区
                            func_to_type = {
                                0x01: 0x00,
                                0x02: 0x01,
                                0x03: 0x04,
                                0x04: 0x03,
                            }
                            data_type = func_to_type.get(cfg.func_code, cfg.func_code)
                            payload += bytes([cfg.slave_id, data_type])
                            payload += cfg.start_addr.to_bytes(2, 'big')
                            payload += len(data).to_bytes(2, 'big')
                            payload += data

                        if len(payload) > 3:
                            self.mqtt_manager.publish(
                                self.mqtt_manager.up_topic,
                                payload,
                                config.MQTT_QOS_UP
                            )
                            logger.info(f"[UPLINK] Data upload sent: {len(configs)} groups")
                            last_upload_time = current_time

                except Exception as e:
                    logger.error(f"Data upload error: {e}")

        self._data_upload_thread = threading.Thread(target=data_upload_loop, daemon=True)
        self._data_upload_thread.start()

    def _simulate_data_changes(self):
        try:
            device = self.device_pool.get_device(1)
            if device:
                device.simulate_all_data_changes()
        except Exception as e:
            logger.warning(f"Data simulation error: {e}")

    def stop(self):
        logger.info("Stopping DTU Simulator...")
        self._running = False

        if self.data_scheduler:
            self.data_scheduler.stop()

        if self.mqtt_manager:
            self.mqtt_manager.disconnect()

        if self.modbus_tcp_server:
            self.modbus_tcp_server.stop()

        if self.modbus_master:
            self.modbus_master.close_all()

        logger.info("DTU Simulator stopped")

    def wait(self):
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='DTU + Modbus Simulator')
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Address segments configuration file'
    )
    parser.add_argument(
        '--no-segments', '-n',
        action='store_true',
        help='Use legacy configuration instead of address segments'
    )
    args = parser.parse_args()

    simulator = DTUSimulator()

    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        simulator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    simulator.initialize(
        use_address_segments=not args.no_segments,
        config_file=args.config
    )
    simulator.start()
    simulator.wait()


if __name__ == "__main__":
    main()