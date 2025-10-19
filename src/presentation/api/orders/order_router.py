# order_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from src.core.di import get_current_user, get_order_service, get_user_service
from src.services.order_service import OrderService
from src.services.user_service import UserService
from src.core.domain.entity.user import User
from src.core.domain.dto.order_dto import OrderDTO, OrderCreateDTO, OrderStatusDTO, OrderListDTO, OrderPollResponse
from src.core.domain.dto.history_dto import UserHistoryDTO, DashboardStatsDTO
from src.core.domain.dto.response_dto import StandardResponse
from src.core.exceptions.exceptions import NotFoundException
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
    """Создать новый заказ через внешнее API"""
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

    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )


@router.get("/{order_id}/poll", response_model=OrderPollResponse)
async def poll_order_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Опрос статуса заказа из внешнего API"""
    try:
        result = await order_service.poll_order_status(order_id, current_user.id)
        return result

    except Exception as e:
        logger.error(f"Error polling order status {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error polling order status: {str(e)}"
        )


@router.post("/{order_id}/cancel", response_model=StandardResponse)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Отменить заказ через внешнее API"""
    try:
        success = await order_service.cancel_order(order_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel order"
            )

        return StandardResponse(
            success=True,
            message="Order cancelled successfully"
        )

    except Exception as e:
        logger.error(f"Error canceling order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling order: {str(e)}"
        )


@router.get("/my", response_model=OrderListDTO)
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Получить список активных заказов пользователя"""
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
    """Получить активные заказы пользователя"""
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
    order_id: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Получить заказ по ID"""
    try:
        order = await order_service.get_order_by_id(order_id, current_user.id)
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


@router.post("/validate", response_model=dict)
async def validate_order(
    order_data: OrderCreateDTO,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service)
):
    """Валидация заказа перед созданием"""
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


# Эндпоинты, которые больше не поддерживаются
@router.put("/{order_id}/status", response_model=OrderDTO)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusDTO,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Этот эндпоинт больше не поддерживается - статусы обновляются только через внешнее API"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Direct status updates not supported. Use polling instead."
    )


@router.delete("/{order_id}", response_model=StandardResponse)
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Этот эндпоинт больше не поддерживается - используйте cancel вместо delete"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Use cancel endpoint instead of delete for external API orders"
    )


# Упрощенные версии остальных эндпоинтов
@router.get("/history/full", response_model=UserHistoryDTO)
async def get_user_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service)
):
    """Получить историю пользователя (только активные заказы)"""
    try:
        user = await user_service.get_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        orders_response = await order_service.get_orders_by_user_id(
            user_id=current_user.id,
            skip=0,
            limit=1000
        )

        from src.core.domain.mappers.user_mapper import UserMapper
        user_mapper = UserMapper()
        user_profile = user_mapper.entity_to_profile_dto(user)

        return UserHistoryDTO(
            user=user_profile,
            orders=orders_response.orders,
            payments=[]  # Платежи пока не поддерживаются
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
    """Получить статистику dashboard (только по активным заказам)"""
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

        # Для внешних заказов считаем потраченными завершенные
        total_spent = sum(order.price for order in orders if order.status.value == "COMPLETED")

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