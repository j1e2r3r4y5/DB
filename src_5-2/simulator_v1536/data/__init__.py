"""
Data module - Contains virtual devices and data management
"""

from .virtual_device import VirtualDevice
from .device_pool import DevicePool
from .data_scheduler import DataScheduler, DataCollectionJob
from .data_registry import DataRegistry, DataPoint
from .address_segment import (
    AddressSegment,
    GeneratedVariable,
    AddressSegmentManager,
    create_default_segments
)

__all__ = [
    "VirtualDevice",
    "DevicePool",
    "DataScheduler",
    "DataCollectionJob",
    "DataRegistry",
    "DataPoint",
    "AddressSegment",
    "GeneratedVariable",
    "AddressSegmentManager",
    "create_default_segments",
]