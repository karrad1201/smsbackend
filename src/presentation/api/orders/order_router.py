from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta

from src.core.di import get_current_user, get_order_service, get_user_service
from src.services.order_service import OrderService
from src.services.user_service import UserService
from src.core.domain.entity.user import User
from src.core.domain.dto.order_dto import OrderDTO, OrderCreateDTO, OrderStatusDTO, OrderListDTO
from src.core.domain.dto.history_dto import UserHistoryDTO, DashboardStatsDTO
from src.core.domain.dto.response_dto import StandardResponse, PaginatedResponse
from src.core.exceptions.exceptions import NotFoundException, InsufficientBalanceException
from src.core.logging_config import get_logger

router = APIRouter(prefix="/orders", tags=["orders"])
logger = get_logger(__name__)


@router.post("/create", response_model=OrderDTO)
async def create_order(
        order_data: OrderCreateDTO,
        client_ip: Optional[str] = None,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service),
        user_service: UserService = Depends(get_user_service)
):
    """Создать новый заказ"""
    try:
        user = await user_service.get_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        order = await order_service.create_order(
            order_create_dto=order_data,
            user_id=current_user.id,
            user_balance=user.balance,
            client_ip=client_ip
        )

        return order

    except InsufficientBalanceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/my", response_model=OrderListDTO)
async def get_my_orders(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        orders = await order_service.get_orders_by_user_id(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return orders

    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/active", response_model=List[OrderDTO])
async def get_my_active_orders(
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        orders = await order_service.get_active_orders(current_user.id)
        return orders

    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{order_id}", response_model=OrderDTO)
async def get_order(
        order_id: int,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    """Получить заказ по ID"""
    try:
        order = await order_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{order_id}/status", response_model=OrderDTO)
async def update_order_status(
        order_id: int,
        status_data: OrderStatusDTO,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        order = await order_service.update_order_status(order_id, status_data)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{order_id}", response_model=StandardResponse)
async def delete_order(
        order_id: int,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        success = await order_service.delete_order(order_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return StandardResponse(
            success=True,
            message="Order deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/validate", response_model=dict)
async def validate_order(
        order_data: OrderCreateDTO,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service),
        user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.get_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        validation_result = await order_service.validate_order_creation(
            service=order_data.service,
            country_code=order_data.country_code,
            user_balance=user.balance
        )

        return validation_result

    except Exception as e:
        logger.error(f"Error validating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/history/full", response_model=UserHistoryDTO)
async def get_user_history(
        days: int = Query(30, ge=1, le=365),
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service),
        user_service: UserService = Depends(get_user_service)
):
    """Получить полную историю пользователя (заказы + платежи)"""
    try:
        user = await user_service.get_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        orders = await order_service.get_orders_by_user_id(
            user_id=current_user.id,
            skip=0,
            limit=1000
        )

        # TODO: Добавить получение платежей когда будет PaymentService
        payments = []

        from src.core.domain.mappers.user_mapper import UserMapper
        user_mapper = UserMapper()
        user_profile = user_mapper.entity_to_profile_dto(user)

        return UserHistoryDTO(
            user=user_profile,
            orders=orders.orders,
            payments=payments
        )

    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/dashboard/stats", response_model=DashboardStatsDTO)
async def get_dashboard_stats(
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        orders_response = await order_service.get_orders_by_user_id(
            user_id=current_user.id,
            skip=0,
            limit=1000
        )

        orders = orders_response.orders
        total_orders = len(orders)

        active_orders = await order_service.get_active_orders(current_user.id)
        active_orders_count = len(active_orders)

        total_spent = sum(order.price for order in orders
                          if
                          order.status.value in ["COMPLETED", "USER_CANCELLED_REFUNDED", "PROVIDER_CANCELLED_REFUNDED"])

        last_order = orders[0] if orders else None

        return DashboardStatsDTO(
            total_orders=total_orders,
            active_orders=active_orders_count,
            total_spent=total_spent,
            last_order=last_order
        )

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/history/period")
async def get_orders_by_period(
        start_date: datetime,
        end_date: datetime,
        current_user: User = Depends(get_current_user),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        orders_response = await order_service.get_orders_by_user_id(
            user_id=current_user.id,
            skip=0,
            limit=1000
        )

        filtered_orders = [
            order for order in orders_response.orders
            if start_date <= order.created_at <= end_date
        ]

        return {
            "orders": filtered_orders,
            "total": len(filtered_orders),
            "start_date": start_date,
            "end_date": end_date
        }

    except Exception as e:
        logger.error(f"Error getting orders by period: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/status/{status}", response_model=List[OrderDTO])
async def get_orders_by_status(
        status: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        order_service: OrderService = Depends(get_order_service)
):
    try:
        orders = await order_service.get_orders_by_status(
            status=status,
            skip=skip,
            limit=limit
        )
        return orders

    except Exception as e:
        logger.error(f"Error getting orders by status {status}: {e}")
        raise