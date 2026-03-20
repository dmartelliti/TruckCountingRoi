from dataclasses import dataclass as dataclass
from pydantic.dataclasses import dataclass as dataclass_typed_attributes_check
from typing import Tuple


@dataclass_typed_attributes_check()
@dataclass(slots=True)
class BBoxDto:
    x1: float
    y1: float
    x2: float
    y2: float

    img_shape: Tuple[int, int]  # (height, width)

    def __post_init__(self):
        if self.x2 < self.x1 or self.y2 < self.y1:
            raise ValueError("Invalid bbox coordinates")

    # -------- Pixel Space --------

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) * 0.5

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) * 0.5

    @property
    def center_pixel(self) -> tuple[float, float]:
        return self.cx, self.cy

    # -------- Cartesian Space --------

    @property
    def center_cartesian(self) -> tuple[float, float]:
        """
        Convierte el centro desde coordenadas de imagen
        (origen arriba-izquierda)
        a coordenadas cartesianas
        (origen abajo-izquierda)
        """
        h, _ = self.img_shape
        x = self.cx
        y = h - self.cy
        return x, y

    # -------- Geometría --------

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def xyxy(self):
        return (
            round(self.x1, 2),
            round(self.y1, 2),
            round(self.x2, 2),
            round(self.y2, 2),
        )

    @property
    def xywh(self):
        return (
            round(self.cx, 2),
            round(self.cy, 2),
            round(self.width, 2),
            round(self.height, 2),
        )

