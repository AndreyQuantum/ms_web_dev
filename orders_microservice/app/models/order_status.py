from __future__ import annotations

import enum


class OrderStatus(str, enum.Enum):

    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
