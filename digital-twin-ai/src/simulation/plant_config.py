from dataclasses import dataclass, field
from enum import Enum
from typing import List

class StationType(Enum):
    ASSEMBLY = "assembly"
    WELDING = "welding"
    PAINT = "paint"
    INSPECTION = "inspection"
    UNKNOWN = "unknown"

class SensorMaturity(Enum):
    FULL = "full"
    PARTIAL = "partial"
    DARK = "dark"

@dataclass
class StationConfig:
    station_id: str
    expected_cycle_time: float
    sensor_maturity: SensorMaturity
    active_sensors: List[str] = field(default_factory=list)
    station_type: StationType = StationType.UNKNOWN
    buffer_capacity: int = 5  # Default queue size since we can't infer it from flat data