from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from src.core.domain.repository.interfaces import IOrderRepository
from src.core.domain.entity.orders import Order, OrderCreate, OrderUpdate, OrderStatus
from src.infrastructure.database.schemas import OrderORM, StatusTypeORM
from src.core.exceptions.exceptions import NotFoundException
from src.core.logging_config import get_logger


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, id: int) -> Optional[Order]:
        try:
            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.id == id)
            )
            order_orm = result.scalar_one_or_none()

            if not order_orm:
                return None

            return self._orm_to_entity(order_orm)
        except Exception as e:
            self.logger.error(f"Error getting order by id {id}: {e}")
            raise

    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        try:
            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.user_id == user_id)
                .order_by(OrderORM.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            orders_orm = result.scalars().all()

            return [self._orm_to_entity(order_orm) for order_orm in orders_orm]
        except Exception as e:
            self.logger.error(f"Error getting orders for user {user_id}: {e}")
            raise

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Order]:
        try:
            status_result = await self.session.execute(
                select(StatusTypeORM.id).where(StatusTypeORM.code == status)
            )
            status_id = status_result.scalar_one_or_none()

            if not status_id:
                return []

            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.status_id == status_id)
                .order_by(OrderORM.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            orders_orm = result.scalars().all()

            return [self._orm_to_entity(order_orm) for order_orm in orders_orm]
        except Exception as e:
            self.logger.error(f"Error getting orders by status {status}: {e}")
            raise

    async def get_active_orders(self, user_id: int) -> List[Order]:
        try:
            result = await self.session.execute(
                select(StatusTypeORM.id).where(StatusTypeORM.is_final == False)
            )
            non_final_status_ids = [row[0] for row in result.all()]

            if not non_final_status_ids:
                return []

            query = (
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(
                    and_(
                        OrderORM.user_id == user_id,
                        OrderORM.status_id.in_(non_final_status_ids)
                    )
                )
                .order_by(OrderORM.created_at.desc())
            )

            result = await self.session.execute(query)
            orders_orm = result.scalars().all()

            return [self._orm_to_entity(order_orm) for order_orm in orders_orm]
        except Exception as e:
            self.logger.error(f"Error getting active orders for user {user_id}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Order]:
        try:
            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .order_by(OrderORM.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            orders_orm = result.scalars().all()

            return [self._orm_to_entity(order_orm) for order_orm in orders_orm]
        except Exception as e:
            self.logger.error(f"Error getting all orders: {e}")
            raise

    async def create(self, order_create: OrderCreate) -> Order:
        try:
            status_result = await self.session.execute(
                select(StatusTypeORM).where(StatusTypeORM.code == OrderStatus.WAITING_CODE)
            )
            status_orm = status_result.scalar_one()

            order_orm = OrderORM(
                service=order_create.service,
                country_code=order_create.country_code,
                price=order_create.price,
                provider_id=order_create.provider_id,
                status_id=status_orm.id,
                user_id=order_create.user_id,
                client_ip=order_create.client_ip,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(order_orm)
            await self.session.commit()

            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.id == order_orm.id)
            )
            order_orm_with_relations = result.scalar_one()

            return self._orm_to_entity(order_orm_with_relations)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating order: {e}")
            raise

    async def update(self, id: int, order_update: OrderUpdate) -> Optional[Order]:
        try:
            update_data = {"updated_at": datetime.utcnow()}

            if order_update.status:
                status_result = await self.session.execute(
                    select(StatusTypeORM.id).where(StatusTypeORM.code == order_update.status)
                )
                status_id = status_result.scalar_one_or_none()
                if status_id:
                    update_data["status_id"] = status_id

            if order_update.code is not None:
                update_data["code"] = order_update.code

            if order_update.number is not None:
                update_data["number"] = order_update.number

            if order_update.status_id is not None:
                update_data["status_id"] = order_update.status_id

            await self.session.execute(
                update(OrderORM)
                .where(OrderORM.id == id)
                .values(**update_data)
            )
            await self.session.commit()

            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.id == id)
            )
            order_orm = result.scalar_one_or_none()
            if not order_orm:
                return None

            return self._orm_to_entity(order_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating order {id}: {e}")
            raise

    async def update_status(self, order_id: int, status: str, code: Optional[str] = None) -> Optional[Order]:
        try:
            status_result = await self.session.execute(
                select(StatusTypeORM.id).where(StatusTypeORM.code == status)
            )
            status_id = status_result.scalar_one_or_none()

            if not status_id:
                self.logger.error(f"Status {status} not found")
                raise NotFoundException

            update_data = {
                "status_id": status_id,
                "updated_at": datetime.utcnow()
            }

            if code is not None:
                update_data["code"] = code

            await self.session.execute(
                update(OrderORM)
                .where(OrderORM.id == order_id)
                .values(**update_data)
            )
            await self.session.commit()

            # Перезагружаем заказ с отношениями
            result = await self.session.execute(
                select(OrderORM)
                .options(selectinload(OrderORM.status))
                .where(OrderORM.id == order_id)
            )
            order_orm = result.scalar_one_or_none()
            if not order_orm:
                return None

            return self._orm_to_entity(order_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating status for order {order_id}: {e}")
            raise

    async def delete(self, id: int) -> bool:
        try:
            result = await self.session.execute(
                select(OrderORM).where(OrderORM.id == id)
            )
            order_orm = result.scalar_one_or_none()

            if not order_orm:
                return False

            await self.session.delete(order_orm)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting order {id}: {e}")
            raise

    async def get_orders_count_by_user(self, user_id: int) -> int:
        try:
            result = await self.session.execute(
                select(OrderORM.id).where(OrderORM.user_id == user_id)
            )
            return len(result.all())
        except Exception as e:
            self.logger.error(f"Error getting orders count for user {user_id}: {e}")
            raise

    def _orm_to_entity(self, order_orm: OrderORM) -> Order:
        return Order(
            id=order_orm.id,
            user_id=order_orm.user_id,
            provider_id=order_orm.provider_id,
            number=order_orm.number,
            activ_id=order_orm.activ_id,
            code=order_orm.code,
            service=order_orm.service,
            price=float(order_orm.price),
            country_code=order_orm.country_code,
            status=OrderStatus(order_orm.status.code),
            status_id=order_orm.status_id,
            created_at=order_orm.created_at,
            updated_at=order_orm.updated_at,
            client_ip=order_orm.client_ip
        )