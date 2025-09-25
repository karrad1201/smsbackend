from typing import Optional
from src.core.domain.entity.orders import Order, OrderCreate
from src.core.domain.dto.order_dto import OrderDTO, OrderCreateDTO

class OrderMapper:
    @staticmethod
    def entity_to_dto(
            order: Order,
            service_name: Optional[str] = None,
            country_name: Optional[str] = None,
            provider_name: Optional[str] = None
    ) -> OrderDTO:
        return OrderDTO(
            id=order.id,
            service=order.service,
            service_name=service_name,
            country_code=order.country_code,
            country_name=country_name,
            phone_number=order.number,
            price=order.price,
            status=order.status,
            provider_id=order.provider_id,
            provider_name=provider_name,
            created_at=order.created_at,
            updated_at=order.updated_at,
            code=order.code,
            activ_id=order.activ_id
        )

    @staticmethod
    def create_dto_to_entity(order_dto: OrderCreateDTO, price: float, provider_id: Optional[int] = None) -> OrderCreate:
        return OrderCreate(
            service=order_dto.service,
            country_code=order_dto.country_code,
            price=price,
            provider_id=provider_id
        )

    @staticmethod
    def entities_to_dto_list(
            orders: list[Order],
            service_names: dict[str, str] = None,
            country_names: dict[str, str] = None,
            provider_names: dict[int, str] = None
    ) -> list[OrderDTO]:
        result = []
        for order in orders:
            service_name = service_names.get(order.service) if service_names else None
            country_name = country_names.get(order.country_code) if country_names else None
            provider_name = provider_names.get(order.provider_id) if provider_names and order.provider_id else None
            result.append(OrderMapper.entity_to_dto(order, service_name, country_name, provider_name))
        return result