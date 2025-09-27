from typing import List, Optional
from src.core.domain.repository.interfaces import IOrderRepository, IPriceRepository, IUserRepository
from src.core.domain.entity.orders import Order, OrderCreate, OrderUpdate
from src.core.domain.dto.order_dto import OrderDTO, OrderCreateDTO, OrderStatusDTO, OrderListDTO
from src.core.domain.mappers.order_mapper import OrderMapper
from src.core.exceptions.exceptions import NotFoundException, InsufficientBalanceException
from src.core.logging_config import get_logger


class OrderService:
    def __init__(self, order_repo: IOrderRepository, price_repo: IPriceRepository, user_repo: IUserRepository):
        self.order_repo = order_repo
        self.price_repo = price_repo
        self.user_repo = user_repo
        self.order_mapper = OrderMapper()
        self.logger = get_logger(__name__)

    async def get_order_by_id(self, order_id: int) -> Optional[OrderDTO]:
        """Получить заказ по ID"""
        try:
            order = await self.order_repo.get_by_id(order_id)
            if not order:
                return None

            service_name, country_name, provider_name = await self._get_order_additional_data(order)

            return self.order_mapper.entity_to_dto(
                order,
                service_name,
                country_name,
                provider_name
            )
        except Exception as e:
            self.logger.error(f"Error getting order {order_id}: {e}")
            raise

    async def get_orders_by_user_id(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> OrderListDTO:
        """Получить список заказов пользователя"""
        try:
            orders = await self.order_repo.get_by_user_id(user_id, skip, limit)

            service_names, country_names, provider_names = await self._get_orders_additional_data(orders)

            order_dtos = self.order_mapper.entities_to_dto_list(
                orders,
                service_names,
                country_names,
                provider_names
            )

            total_count = await self.order_repo.get_orders_count_by_user(user_id)

            return OrderListDTO(
                orders=order_dtos,
                total=total_count,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit
            )
        except Exception as e:
            self.logger.error(f"Error getting orders for user {user_id}: {e}")
            raise

    async def get_orders_by_status(
            self,
            status: str,
            skip: int = 0,
            limit: int = 100
    ) -> List[OrderDTO]:
        try:
            orders = await self.order_repo.get_by_status(status, skip, limit)
            service_names, country_names, provider_names = await self._get_orders_additional_data(orders)
            return self.order_mapper.entities_to_dto_list(
                orders,
                service_names,
                country_names,
                provider_names
            )
        except Exception as e:
            self.logger.error(f"Error getting orders by status {status}: {e}")
            raise

    async def get_active_orders(self, user_id: int) -> List[OrderDTO]:
        try:
            orders = await self.order_repo.get_active_orders(user_id)
            service_names, country_names, provider_names = await self._get_orders_additional_data(orders)
            return self.order_mapper.entities_to_dto_list(
                orders,
                service_names,
                country_names,
                provider_names
            )
        except Exception as e:
            self.logger.error(f"Error getting active orders for user {user_id}: {e}")
            raise

    async def get_all_orders(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[OrderDTO]:
        try:
            orders = await self.order_repo.get_all(skip, limit)
            service_names, country_names, provider_names = await self._get_orders_additional_data(orders)
            return self.order_mapper.entities_to_dto_list(
                orders,
                service_names,
                country_names,
                provider_names
            )
        except Exception as e:
            self.logger.error(f"Error getting all orders: {e}")
            raise

    async def create_order(
            self,
            order_create_dto: OrderCreateDTO,
            user_id: int,
            user_balance: float,
            client_ip: Optional[str] = None
    ) -> OrderDTO:
        """Создать новый заказ"""
        try:
            price_info = await self.price_repo.get_price_for_service_country(
                order_create_dto.service,
                order_create_dto.country_code
            )

            if not price_info:
                raise NotFoundException(
                    f"Service {order_create_dto.service} for country {order_create_dto.country_code} not found"
                )

            if not price_info.available:
                raise NotFoundException("Service is currently unavailable")

            if user_balance < float(price_info.price):
                raise InsufficientBalanceException(
                    f"Insufficient balance. Required: {price_info.price}, available: {user_balance}"
                )

            order_create_entity = OrderCreate(
                service=order_create_dto.service,
                country_code=order_create_dto.country_code,
                price=float(price_info.price),
                provider_id=getattr(price_info, 'provider_id', None),
                user_id=user_id,
                client_ip=client_ip
            )

            order = await self.order_repo.create(order_create_entity)
            await self.user_repo.update_balance(user_id, -float(price_info.price))

            service_name, country_name, provider_name = await self._get_order_additional_data(order)

            self.logger.info(f"Order {order.id} created for user {user_id}")
            return self.order_mapper.entity_to_dto(
                order,
                service_name,
                country_name,
                provider_name
            )

        except Exception as e:
            self.logger.error(f"Error creating order for user {user_id}: {e}")
            raise

    async def update_order_status(
            self,
            order_id: int,
            status_dto: OrderStatusDTO
    ) -> Optional[OrderDTO]:
        """Обновить статус заказа"""
        try:
            order = await self.order_repo.update_status(
                order_id,
                status_dto.status.value,
                status_dto.code
            )
            if not order:
                return None

            service_name, country_name, provider_name = await self._get_order_additional_data(order)
            return self.order_mapper.entity_to_dto(
                order,
                service_name,
                country_name,
                provider_name
            )
        except Exception as e:
            self.logger.error(f"Error updating status for order {order_id}: {e}")
            raise

    async def update_order(
            self,
            order_id: int,
            order_update: OrderUpdate
    ) -> Optional[OrderDTO]:
        """Обновить заказ"""
        try:
            order = await self.order_repo.update(order_id, order_update)
            if not order:
                return None

            service_name, country_name, provider_name = await self._get_order_additional_data(order)
            return self.order_mapper.entity_to_dto(
                order,
                service_name,
                country_name,
                provider_name
            )
        except Exception as e:
            self.logger.error(f"Error updating order {order_id}: {e}")
            raise

    async def delete_order(self, order_id: int) -> bool:
        """Удалить заказ"""
        try:
            return await self.order_repo.delete(order_id)
        except Exception as e:
            self.logger.error(f"Error deleting order {order_id}: {e}")
            raise

    async def get_user_orders_count(self, user_id: int) -> int:
        """Получить количество заказов пользователя"""
        try:
            return await self.order_repo.get_orders_count_by_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting orders count for user {user_id}: {e}")
            raise

    async def validate_order_creation(
            self,
            service: str,
            country_code: str,
            user_balance: float
    ) -> dict:
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

    async def _get_order_additional_data(self, order: Order) -> tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            price_info = await self.price_repo.get_price_for_service_country(
                order.service,
                order.country_code
            )

            service_name = price_info.service_name if price_info else None
            country_name = price_info.country_name if price_info else None
            provider_name = getattr(price_info, 'provider_name', None) if price_info else None

            return service_name, country_name, provider_name
        except Exception as e:
            self.logger.warning(f"Error getting additional data for order {order.id}: {e}")
            return None, None, None

    async def _get_orders_additional_data(self, orders: List[Order]) -> tuple[dict, dict, dict]:
        service_names = {}
        country_names = {}
        provider_names = {}

        for order in orders:
            try:
                price_info = await self.price_repo.get_price_for_service_country(
                    order.service,
                    order.country_code
                )

                if price_info:
                    service_names[order.service] = price_info.service_name
                    country_names[order.country_code] = price_info.country_name
                    if hasattr(price_info, 'provider_name') and price_info.provider_name and order.provider_id:
                        provider_names[order.provider_id] = price_info.provider_name
            except Exception as e:
                self.logger.warning(f"Error getting additional data for order {order.id}: {e}")
                continue

        return service_names, country_names, provider_names