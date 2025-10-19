# websocket_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from src.services.order_service import OrderService
from src.core.di import get_order_service
from src.core.logging_config import get_logger
from typing import Optional
import asyncio

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = get_logger(__name__)


@router.websocket("/orders/{order_id}")
async def websocket_order_status(
        websocket: WebSocket,
        order_id: str,
        token: Optional[str] = Query(None),
        order_service: OrderService = Depends(get_order_service)
):
    """WebSocket для отслеживания статуса заказа в реальном времени"""

    try:
        await websocket.accept()
        logger.info(f"WebSocket connection established for order {order_id}")

        if not token:
            await websocket.close(code=1008, reason="Token required")
            return

        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to order {order_id}",
            "order_id": order_id
        })

        # Запускаем периодический опрос статуса
        poll_task = asyncio.create_task(
            poll_order_status_periodically(websocket, order_id, order_service)
        )

        # Основной цикл обработки сообщений от клиента
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received message for order {order_id}: {data}")

                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "message": "pong",
                        "timestamp": "2025-10-16T16:34:47Z"
                    })
                elif data == "force_poll":
                    # Принудительный опрос статуса
                    await force_poll_status(websocket, order_id, order_service)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {data}"
                    })

        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected for order {order_id}")
        finally:
            # Останавливаем периодический опрос
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"WebSocket setup error for order {order_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


async def poll_order_status_periodically(
        websocket: WebSocket,
        order_id: str,
        order_service: OrderService,
        interval: int = 10  # Интервал опроса в секундах
):
    """Периодический опрос статуса заказа"""
    try:
        while True:
            await asyncio.sleep(interval)

            try:
                # Получаем текущий статус заказа
                order = order_service.active_orders.get(order_id)
                if order:
                    await websocket.send_json({
                        "type": "status_update",
                        "order_id": order_id,
                        "status": order.status.value,
                        "external_status": order.external_status,
                        "code": order.code,
                        "phone_number": order.phone_number,
                        "price": order.price,
                        "service": order.service,
                        "service_name": order.service_name,
                        "activ_id": order.activ_id,
                        "timestamp": order.updated_at.isoformat() if order.updated_at else order.created_at.isoformat()
                    })
                else:
                    # Если заказ не найден в активных, отправляем сообщение
                    await websocket.send_json({
                        "type": "status_update",
                        "order_id": order_id,
                        "status": "not_found",
                        "external_status": "NOT_FOUND",
                        "code": None,
                        "phone_number": None,
                        "message": "Order not found in active orders",
                        "timestamp": "2025-10-16T16:34:47Z"
                    })

            except Exception as e:
                logger.error(f"Error polling status for order {order_id}: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Polling error: {str(e)}"
                    })
                except:
                    break

    except asyncio.CancelledError:
        logger.info(f"Polling task cancelled for order {order_id}")
    except Exception as e:
        logger.error(f"Polling task error for order {order_id}: {e}")


async def force_poll_status(
        websocket: WebSocket,
        order_id: str,
        order_service: OrderService
):
    """Принудительный опрос статуса"""
    try:
        # Здесь можно добавить логику принудительного опроса внешнего API
        order = order_service.active_orders.get(order_id)
        if order:
            await websocket.send_json({
                "type": "status_update",
                "order_id": order_id,
                "status": order.status.value,
                "external_status": order.external_status,
                "code": order.code,
                "phone_number": order.phone_number,
                "price": order.price,
                "service": order.service,
                "service_name": order.service_name,
                "activ_id": order.activ_id,
                "timestamp": order.updated_at.isoformat() if order.updated_at else order.created_at.isoformat(),
                "forced": True
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Order not found"
            })
    except Exception as e:
        logger.error(f"Error in force poll for order {order_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Force poll error: {str(e)}"
        })