from typing import Tuple


class Line2D:
    """
    Represents an infinite 2D line defined by two points.

    Internally stored in implicit form:
        ax + by + c = 0

    This representation is robust for geometric tests such as
    half-plane classification.
    """

    def __init__(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        x1, y1 = p1
        x2, y2 = p2

        if (x1, y1) == (x2, y2):
            raise ValueError("Points must be different")

        # Coefficients of implicit line equation
        self.a = y1 - y2
        self.b = x2 - x1
        self.c = x1 * y2 - x2 * y1

    # -------------------------------------------------
    def half_plane(self, point: Tuple[float, float], tol: float = 1e-9) -> int:
        """
        Determine which half-plane the point lies in.

        Returns:
            1  -> one side
           -1  -> opposite side
            0  -> on the line
        """
        x, y = point
        value = self.a * x + self.b * y + self.c

        if abs(value) < tol:
            return 0
        return 1 if value > 0 else -1

