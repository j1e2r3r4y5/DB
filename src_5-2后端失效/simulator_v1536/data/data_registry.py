from typing import Dict, List, Optional, Callable
import threading
import logging

logger = logging.getLogger(__name__)


class DataRegistry:
    def __init__(self):
        self._data_points: Dict[str, 'DataPoint'] = {}
        self._lock = threading.Lock()
        self._on_change_callback: Optional[Callable[['DataPoint'], None]] = None

    def register(
        self,
        point_id: str,
        slave_id: int,
        func_code: int,
        start_addr: int,
        quantity: int,
        name: str = "",
        unit: str = "",
        data_type: str = "uint16"
    ) -> bool:
        with self._lock:
            if point_id in self._data_points:
                logger.warning(f"Data point {point_id} already registered")
                return False

            point = DataPoint(
                point_id=point_id,
                slave_id=slave_id,
                func_code=func_code,
                start_addr=start_addr,
                quantity=quantity,
                name=name,
                unit=unit,
                data_type=data_type
            )
            self._data_points[point_id] = point
            logger.info(f"Registered data point: {point_id}")
            return True

    def unregister(self, point_id: str) -> bool:
        with self._lock:
            if point_id in self._data_points:
                del self._data_points[point_id]
                logger.info(f"Unregistered data point: {point_id}")
                return True
            return False

    def get(self, point_id: str) -> Optional['DataPoint']:
        with self._lock:
            return self._data_points.get(point_id)

    def get_all(self) -> List['DataPoint']:
        with self._lock:
            return list(self._data_points.values())

    def get_by_slave(self, slave_id: int) -> List['DataPoint']:
        with self._lock:
            return [dp for dp in self._data_points.values() if dp.slave_id == slave_id]

    def get_by_func_code(self, func_code: int) -> List['DataPoint']:
        with self._lock:
            return [dp for dp in self._data_points.values() if dp.func_code == func_code]

    def set_value(self, point_id: str, value: any):
        with self._lock:
            point = self._data_points.get(point_id)
            if point:
                point.update_value(value)
                if self._on_change_callback:
                    self._on_change_callback(point)

    def set_on_change_callback(self, callback: Callable[['DataPoint'], None]):
        self._on_change_callback = callback

    def clear(self):
        with self._lock:
            self._data_points.clear()
            logger.info("Cleared all data points")

    def __len__(self) -> int:
        with self._lock:
            return len(self._data_points)

    def __contains__(self, point_id: str) -> bool:
        return self.get(point_id) is not None


class DataPoint:
    def __init__(
        self,
        point_id: str,
        slave_id: int,
        func_code: int,
        start_addr: int,
        quantity: int,
        name: str = "",
        unit: str = "",
        data_type: str = "uint16"
    ):
        self.point_id = point_id
        self.slave_id = slave_id
        self.func_code = func_code
        self.start_addr = start_addr
        self.quantity = quantity
        self.name = name
        self.unit = unit
        self.data_type = data_type
        self._value: any = None
        self._last_update: Optional[float] = None
        self._lock = threading.Lock()

    def update_value(self, value: any):
        with self._lock:
            self._value = value
            import time
            self._last_update = time.time()

    @property
    def value(self) -> any:
        with self._lock:
            return self._value

    @property
    def last_update(self) -> Optional[float]:
        with self._lock:
            return self._last_update

    def __repr__(self) -> str:
        return f"DataPoint(id={self.point_id}, name={self.name}, value={self._value})"