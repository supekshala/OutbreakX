import dataclasses
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Coordinate():
    longitude: float
    latitude: float

    def __repr__(self) -> str:
        return f"Long: {self.longitude}    Lat: {self.latitude}"

    def as_tuple(self) -> tuple:
        return (self.longitude, self.latitude)