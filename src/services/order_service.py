# order_service.py
from typing import List, Optional, Dict, Set
import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect

from src.core.domain.repository.interfaces import IPriceRepository, IUserRepository
from src.core.domain.entity.orders import OrderStatus
from src.core.domain.dto.order_dto import OrderDTO, OrderCreateDTO, OrderListDTO, ExternalAPIResponse, OrderPollResponse
from src.core.exceptions.exceptions import NotFoundException
from src.core.logging_config import get_logger


class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = get_logger(__name__)

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)
        self.logger.info(f"WebSocket connected for order {order_id}")

    def disconnect(self, websocket: WebSocket, order_id: str):
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        self.logger.info(f"WebSocket disconnected for order {order_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            self.logger.error(f"Error sending WebSocket message: {e}")

    async def broadcast_to_order(self, order_id: str, message: dict):
        if order_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[order_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    self.logger.error(f"Error broadcasting to order {order_id}: {e}")
                    disconnected.add(websocket)

            # Удаляем отключенные соединения
            for websocket in disconnected:
                self.disconnect(websocket, order_id)


class OrderService:
    def __init__(self, price_repo: IPriceRepository, user_repo: IUserRepository):
        self.price_repo = price_repo
        self.user_repo = user_repo
        self.logger = get_logger(__name__)
        self.base_api_url = "https://sms-rooms.com/stubs/handler_api.php"
        self.active_orders: Dict[str, OrderDTO] = {}
        self.websocket_manager = ConnectionManager()

        # Запускаем фоновую задачу для опроса статусов
        self._background_task = None
        self._background_task_started = False

    async def start_background_tasks(self):
        """Запуск фоновых задач при старте приложения"""
        if not self._background_task_started:
            self._background_task = asyncio.create_task(self._poll_orders_background())
            self._background_task_started = True
            self.logger.info("Background order polling task started")

    async def stop_background_tasks(self):
        """Остановка фоновых задач при завершении приложения"""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Background order polling task stopped")

    async def _make_external_api_call(self, params: dict) -> ExternalAPIResponse:
        """Вызов внешнего API с обработкой JSON и текстовых ответов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_api_url, params=params, timeout=30) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        raise Exception(f"API error {response.status}: {response_text}")

                    # Пытаемся парсить как JSON
                    try:
                        response_data = json.loads(response_text)
                        self.logger.info(f"External API JSON response: {response_data}")
                        return ExternalAPIResponse(**response_data)
                    except json.JSONDecodeError:
                        # Если не JSON, пробуем текстовый формат
                        self.logger.info(f"External API text response: {response_text}")

                        # Базовый парсинг текстового ответа для обратной совместимости
                        if ":" in response_text:
                            parts = response_text.split(":")
                            if len(parts) >= 3:
                                return ExternalAPIResponse(
                                    status_code=parts[0],
                                    activationId=parts[1],
                                    phoneNumber=parts[2],
                                    value=response_text
                                )

                        # Если не удалось распарсить, возвращаем как есть
                        return ExternalAPIResponse(
                            status_code=response_text,
                            value=response_text
                        )

        except asyncio.TimeoutError:
            raise Exception("External API timeout")
        except Exception as e:
            self.logger.error(f"External API call failed: {e}")
            raise

    async def _map_external_status_to_internal(self, external_status: str) -> OrderStatus:
        """Маппинг статусов из внешнего API во внутренние"""
        status_mapping = {
            "ACCESS_NUMBER": OrderStatus.PENDING_ORDER,
            "STATUS_WAIT_CODE": OrderStatus.WAITING_CODE,
            "STATUS_OK": OrderStatus.COMPLETED,
            "ACCESS_READY": OrderStatus.WAITING_CODE,
            "ACCESS_RETRY_GET": OrderStatus.WAITING_RETRY_CODE,
            "ACCESS_CANCEL": OrderStatus.USER_CANCELLED_REFUNDED,
            "ACCESS_ACTIVATION": OrderStatus.COMPLETED,
            "NO_NUMBERS": OrderStatus.NO_NUMBERS_REFUNDED,
            "NO_BALANCE": OrderStatus.NO_NUMBERS_REFUNDED,
            "BAD_KEY": OrderStatus.NO_NUMBERS_REFUNDED,
        }
        return status_mapping.get(external_status, OrderStatus.WAITING_CODE)

    async def _poll_orders_background(self):
        """Фоновая задача для автоматического опроса статусов заказов"""
        while True:
            try:
                current_time = datetime.now()
                orders_to_remove = []

                for order_id, order in self.active_orders.items():
                    # Проверяем, не истекло ли время жизни заказа (20 минут)
                    order_age = current_time - order.created_at
                    if order_age.total_seconds() > 1200:  # 20 минут
                        orders_to_remove.append(order_id)
                        self.logger.info(f"Order {order_id} expired, removing from active orders")
                        continue

                    # Опрашиваем только активные заказы (не завершенные)
                    if order.status not in [OrderStatus.COMPLETED, OrderStatus.USER_CANCELLED_REFUNDED,
                                            OrderStatus.FAILED]:
                        try:
                            user = await self.user_repo.get_by_id(order.user_id)
                            if not user or not user.api_key:
                                continue

                            params = {
                                'api_key': user.api_key,
                                'action': 'getStatusV2',
                                'id': order.activ_id
                            }

                            api_response = await self._make_external_api_call(params)
                            new_status = await self._map_external_status_to_internal(api_response.status_code)

                            # Обновляем статус если он изменился
                            if order.status != new_status or order.code != api_response.code:
                                order.status = new_status
                                order.code = api_response.code
                                order.external_status = api_response.status_code
                                order.updated_at = datetime.now()

                                # Отправляем обновление через WebSocket
                                await self.websocket_manager.broadcast_to_order(
                                    order_id,
                                    {
                                        "type": "status_update",
                                        "order_id": order_id,
                                        "status": order.status.value,
                                        "external_status": order.external_status,
                                        "code": order.code,
                                        "phone_number": order.phone_number,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                )

                                self.logger.info(f"Order {order_id} status updated to {new_status}")

                        except Exception as e:
                            self.logger.error(f"Background poll error for order {order_id}: {e}")

                # Удаляем истекшие заказы
                for order_id in orders_to_remove:
                    if order_id in self.active_orders:
                        # Уведомляем WebSocket о истечении времени
                        await self.websocket_manager.broadcast_to_order(
                            order_id,
                            {
                                "type": "order_expired",
                                "order_id": order_id,
                                "message": "Order expired after 20 minutes",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        del self.active_orders[order_id]

                # Ждем 10 секунд перед следующим опросом
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Background polling task error: {e}")
                await asyncio.sleep(30)  # Ждем дольше при ошибке

    async def create_order(
            self,
            order_create_dto: OrderCreateDTO,
            user_id: int,
            user_balance: float,
            client_ip: Optional[str] = None
    ) -> OrderDTO:
        """Создать новый заказ через внешнее API"""
        try:
            # Получаем пользователя и его API ключ
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.api_key:
                raise Exception("User API key not found")

            # Получаем информацию о сервисе для названий
            price_info = await self.price_repo.get_price_for_service_country(
                order_create_dto.service,
                order_create_dto.country_code
            )

            if not price_info or not price_info.available:
                raise NotFoundException("Service is currently unavailable")

            # Проверяем баланс
            if user_balance < (price_info.price or 0):
                raise Exception("Insufficient balance")

            params = {
                'api_key': user.api_key,
                'action': 'getNumberV2',
                'service': order_create_dto.service,
                'country': order_create_dto.country_code
            }

            api_response = await self._make_external_api_call(params)

            if api_response.status_code != "ACCESS_NUMBER":
                error_msg = f"Failed to create order: {api_response.status_code}"
                if api_response.status_code == "NO_BALANCE":
                    error_msg = "Insufficient balance in provider account"
                elif api_response.status_code == "NO_NUMBERS":
                    error_msg = "No numbers available for this service/country"
                elif api_response.status_code == "BAD_KEY":
                    error_msg = "Invalid API key"

                raise Exception(error_msg)

            # Создаем OrderDTO из ответа API
            order_dto = OrderDTO(
                id=api_response.activationId or f"ext_{api_response.activationId}",
                service=order_create_dto.service,
                service_name=price_info.service_name if price_info else order_create_dto.service,
                country_code=order_create_dto.country_code,
                country_name=price_info.country_name if price_info else order_create_dto.country_code,
                phone_number=api_response.phoneNumber,
                price=api_response.priceCharged or (price_info.price if price_info else 0.0),
                status=await self._map_external_status_to_internal(api_response.status_code),
                provider_id=None,
                provider_name="sms-room",
                created_at=datetime.now(),
                code=None,
                activ_id=api_response.activationId,
                external_status=api_response.status_code,
                activation_time=getattr(api_response, 'activationTime', None),
                user_id=user_id
            )

            # Сохраняем в активные заказы
            self.active_orders[order_dto.id] = order_dto

            self.logger.info(f"Order {order_dto.id} created via external API for user {user_id}")
            return order_dto

        except Exception as e:
            self.logger.error(f"Error creating order via external API for user {user_id}: {e}")
            raise

    # Остальные методы остаются без изменений...
    async def poll_order_status(self, order_id: str, user_id: int) -> OrderPollResponse:
        """Опрос статуса заказа из внешнего API"""
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.api_key:
                raise Exception("User API key not found")

            # Проверяем, существует ли заказ и принадлежит ли пользователю
            order = self.active_orders.get(order_id)
            if not order or order.user_id != user_id:
                #raise Exception("Order not found or access denied")
                pass

            # Опрашиваем внешнее API для получения статуса
            params = {
                'api_key': user.api_key,
                'action': 'getStatusV2',
                'id': order_id
            }

            api_response = await self._make_external_api_call(params)

            # Обновляем заказ в памяти
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                order.status = await self._map_external_status_to_internal(api_response.status_code)
                order.code = api_response.code
                order.external_status = api_response.status_code
                order.updated_at = datetime.now()

            return OrderPollResponse(
                status=await self._map_external_status_to_internal(api_response.status_code),
                code=api_response.code,
                phone_number=api_response.phoneNumber,
                external_status=api_response.status_code
            )

        except Exception as e:
            self.logger.error(f"Error polling order status {order_id}: {e}")
            raise

    async def cancel_order(self, order_id: str, user_id: int) -> bool:
        """Отменить заказ через внешнее API"""
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.api_key:
                raise Exception("User API key not found")

            params = {
                'api_key': user.api_key,
                'action': 'setStatus',
                'id': order_id,
                'status': 8  # Отмена активации
            }

            api_response = await self._make_external_api_call(params)

            # Удаляем из активных заказов при успешной отмене
            if api_response.status_code in ["ACCESS_CANCEL", "ACCESS_ACTIVATION"]:
                if order_id in self.active_orders:
                    # Уведомляем WebSocket об отмене
                    await self.websocket_manager.broadcast_to_order(
                        order_id,
                        {
                            "type": "order_cancelled",
                            "order_id": order_id,
                            "message": "Order cancelled successfully",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    del self.active_orders[order_id]
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error canceling order {order_id}: {e}")
            raise

    async def get_order_by_id(self, order_id: str, user_id: int) -> Optional[OrderDTO]:
        """Получить заказ по ID из памяти"""
        try:
            order = self.active_orders.get(order_id)

            # Проверяем принадлежность заказа пользователю
            if order and order.user_id != user_id:
                return None

            return order

        except Exception as e:
            self.logger.error(f"Error getting order {order_id}: {e}")
            raise

    async def get_orders_by_user_id(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> OrderListDTO:
        """Получить список активных заказов пользователя"""
        try:
            # Фильтруем заказы по user_id
            user_orders = [
                order for order in self.active_orders.values()
                if order.user_id == user_id
            ]

            # Сортируем по дате создания (новые сначала)
            user_orders.sort(key=lambda x: x.created_at, reverse=True)

            # Применяем пагинацию
            paginated_orders = user_orders[skip:skip + limit]
            total_count = len(user_orders)

            return OrderListDTO(
                orders=paginated_orders,
                total=total_count,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit
            )
        except Exception as e:
            self.logger.error(f"Error getting orders for user {user_id}: {e}")
            raise

    async def get_active_orders(self, user_id: int) -> List[OrderDTO]:
        """Получить активные заказы пользователя"""
        try:
            # Фильтруем активные заказы (не финальные статусы)
            active_statuses = [
                OrderStatus.PENDING_ORDER,
                OrderStatus.WAITING_CODE,
                OrderStatus.WAITING_RETRY_CODE
            ]

            user_active_orders = [
                order for order in self.active_orders.values()
                if order.user_id == user_id and order.status in active_statuses
            ]

            return user_active_orders
        except Exception as e:
            self.logger.error(f"Error getting active orders for user {user_id}: {e}")
            raise

    async def validate_order_creation(
            self,
            service: str,
            country_code: str,
            user_balance: float
    ) -> dict:
        """Валидация возможности создания заказа"""
        try:
            price_info = await self.price_repo.get_price_for_service_country(service, country_code)

            if not price_info:
                return {
                    "valid": False,
                    "error": "Service not found",
                    "available": False
                }

            if not price_info.available:
                return {
                    "valid": False,
                    "error": "Service unavailable",
                    "available": False,
                    "price": float(price_info.price)
                }

            # Проверяем баланс
            sufficient_balance = user_balance >= float(price_info.price)

            return {
                "valid": sufficient_balance and price_info.available,
                "available": price_info.available,
                "price": float(price_info.price),
                "sufficient_balance": sufficient_balance,
                "service_name": price_info.service_name,
                "country_name": price_info.country_name,
                "required_balance": float(price_info.price),
                "current_balance": user_balance
            }

        except Exception as e:
            self.logger.error(f"Error validating order creation: {e}")
            return {
                "valid": False,
                "error": str(e)
            }



    async def _poll_orders_background_cycle(self):
        """Один цикл опроса заказов (для тестов)"""
        try:
            current_time = datetime.now()
            orders_to_remove = []

            for order_id, order in self.active_orders.items():
                # Проверяем, не истекло ли время жизни заказа (20 минут)
                order_age = current_time - order.created_at
                if order_age.total_seconds() > 1200:  # 20 минут
                    orders_to_remove.append(order_id)
                    self.logger.info(f"Order {order_id} expired, removing from active orders")
                    continue

                # Опрашиваем только активные заказы (не завершенные)
                if order.status not in [OrderStatus.COMPLETED, OrderStatus.USER_CANCELLED_REFUNDED, OrderStatus.FAILED]:
                    try:
                        user = await self.user_repo.get_by_id(order.user_id)
                        if not user or not user.api_key:
                            continue

                        params = {
                            'api_key': user.api_key,
                            'action': 'getStatusV2',
                            'id': order.activ_id
                        }

                        api_response = await self._make_external_api_call(params)
                        new_status = await self._map_external_status_to_internal(api_response.status_code)

                        # Обновляем статус если он изменился
                        if order.status != new_status or order.code != api_response.code:
                            order.status = new_status
                            order.code = api_response.code
                            order.external_status = api_response.status_code
                            order.updated_at = datetime.now()

                            # Отправляем обновление через WebSocket
                            await self.websocket_manager.broadcast_to_order(
                                order_id,
                                {
                                    "type": "status_update",
                                    "order_id": order_id,
                                    "status": order.status.value,
                                    "external_status": order.external_status,
                                    "code": order.code,
                                    "phone_number": order.phone_number,
                                    "timestamp": datetime.now().isoformat()
                                }
                            )

                            self.logger.info(f"Order {order_id} status updated to {new_status}")

                    except Exception as e:
                        self.logger.error(f"Background poll error for order {order_id}: {e}")

            # Удаляем истекшие заказы
            for order_id in orders_to_remove:
                if order_id in self.active_orders:
                    # Уведомляем WebSocket о истечении времени
                    await self.websocket_manager.broadcast_to_order(
                        order_id,
                        {
                            "type": "order_expired",
                            "order_id": order_id,
                            "message": "Order expired after 20 minutes",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    del self.active_orders[order_id]

        except Exception as e:
            self.logger.error(f"Background polling cycle error: {e}")
