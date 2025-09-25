from pydantic import BaseModel
from typing import List
from src.core.domain.dto.order_dto import OrderDTO
from src.core.domain.entity.payment import Payment
from src.core.domain.dto.user_dto import UserProfileDTO

class UserHistoryDTO(BaseModel):
    user: UserProfileDTO
    orders: List[OrderDTO]
    payments: List[Payment]

class DashboardStatsDTO(BaseModel):
    total_orders: int
    active_orders: int
    total_spent: float
    last_order: OrderDTO