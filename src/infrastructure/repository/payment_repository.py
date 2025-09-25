from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc
from typing import List, Optional
from datetime import datetime

from src.core.domain.repository.interfaces import IPaymentRepository
from src.core.domain.entity.payment import Payment, PaymentCreate, PaymentUpdate, PaymentStatus
from src.infrastructure.database.schemas import PaymentORM
from src.core.exceptions.exceptions import DatabaseException
from src.core.logging_config import get_logger


class PaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, id: int) -> Optional[Payment]:
        try:
            result = await self.session.execute(
                select(PaymentORM).where(PaymentORM.id == id)
            )
            payment_orm = result.scalar_one_or_none()

            return self._orm_to_entity(payment_orm) if payment_orm else None
        except Exception as e:
            self.logger.error(f"Error getting payment by id {id}: {e}")
            raise DatabaseException(f"Failed to get payment: {e}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        try:
            result = await self.session.execute(
                select(PaymentORM)
                .order_by(desc(PaymentORM.created_at))
                .offset(skip)
                .limit(limit)
            )
            payments_orm = result.scalars().all()

            return [self._orm_to_entity(payment_orm) for payment_orm in payments_orm]
        except Exception as e:
            self.logger.error(f"Error getting all payments: {e}")
            raise DatabaseException(f"Failed to get payments: {e}")

    async def create(self, entity: PaymentCreate) -> Payment:
        try:
            payment_orm = PaymentORM(
                user_id=entity.user_id,
                amount=entity.amount,
                status=entity.status.value if hasattr(entity.status, 'value') else entity.status,
                cash_register=entity.cash_register,
                invoice_id=entity.invoice_id,
                transaction_hash=entity.transaction_hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(payment_orm)
            await self.session.commit()
            await self.session.refresh(payment_orm)

            return self._orm_to_entity(payment_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating payment: {e}")
            raise DatabaseException(f"Failed to create payment: {e}")

    async def update(self, id: int, entity: PaymentUpdate) -> Optional[Payment]:
        try:
            update_data = {
                "updated_at": datetime.utcnow()
            }

            if entity.status is not None:
                update_data["status"] = entity.status.value if hasattr(entity.status, 'value') else entity.status
            if entity.transaction_hash is not None:
                update_data["transaction_hash"] = entity.transaction_hash
            if entity.invoice_id is not None:
                update_data["invoice_id"] = entity.invoice_id
            if entity.cash_register is not None:
                update_data["cash_register"] = entity.cash_register

            if not update_data:
                return await self.get_by_id(id)

            result = await self.session.execute(
                update(PaymentORM)
                .where(PaymentORM.id == id)
                .values(**update_data)
                .returning(PaymentORM)
            )

            payment_orm = result.scalar_one_or_none()
            if not payment_orm:
                return None

            await self.session.commit()
            return self._orm_to_entity(payment_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating payment {id}: {e}")
            raise DatabaseException(f"Failed to update payment: {e}")

    async def delete(self, id: int) -> bool:
        try:
            result = await self.session.execute(
                update(PaymentORM)
                .where(PaymentORM.id == id)
                .values(
                    status=PaymentStatus.CANCELLED.value,
                    updated_at=datetime.utcnow()
                )
            )

            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting payment {id}: {e}")
            raise DatabaseException(f"Failed to delete payment: {e}")

    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        try:
            result = await self.session.execute(
                select(PaymentORM)
                .where(PaymentORM.user_id == user_id)
                .order_by(desc(PaymentORM.created_at))
                .offset(skip)
                .limit(limit)
            )
            payments_orm = result.scalars().all()

            return [self._orm_to_entity(payment_orm) for payment_orm in payments_orm]
        except Exception as e:
            self.logger.error(f"Error getting payments for user {user_id}: {e}")
            raise DatabaseException(f"Failed to get user payments: {e}")

    async def get_by_invoice_id(self, invoice_id: str) -> Optional[Payment]:
        try:
            result = await self.session.execute(
                select(PaymentORM).where(PaymentORM.invoice_id == invoice_id)
            )
            payment_orm = result.scalar_one_or_none()

            return self._orm_to_entity(payment_orm) if payment_orm else None
        except Exception as e:
            self.logger.error(f"Error getting payment by invoice_id {invoice_id}: {e}")
            raise DatabaseException(f"Failed to get payment by invoice: {e}")

    async def get_by_status(self, status: PaymentStatus, skip: int = 0, limit: int = 100) -> List[Payment]:
        try:
            status_value = status.value if hasattr(status, 'value') else status

            result = await self.session.execute(
                select(PaymentORM)
                .where(PaymentORM.status == status_value)
                .order_by(desc(PaymentORM.created_at))
                .offset(skip)
                .limit(limit)
            )
            payments_orm = result.scalars().all()

            return [self._orm_to_entity(payment_orm) for payment_orm in payments_orm]
        except Exception as e:
            self.logger.error(f"Error getting payments by status {status}: {e}")
            raise DatabaseException(f"Failed to get payments by status: {e}")

    async def get_user_payment_by_status(self, user_id: int, status: PaymentStatus) -> List[Payment]:
        try:
            status_value = status.value if hasattr(status, 'value') else status

            result = await self.session.execute(
                select(PaymentORM)
                .where(
                    and_(
                        PaymentORM.user_id == user_id,
                        PaymentORM.status == status_value
                    )
                )
                .order_by(desc(PaymentORM.created_at))
            )
            payments_orm = result.scalars().all()

            return [self._orm_to_entity(payment_orm) for payment_orm in payments_orm]
        except Exception as e:
            self.logger.error(f"Error getting user {user_id} payments by status {status}: {e}")
            raise DatabaseException(f"Failed to get user payments by status: {e}")

    async def update_status(self, payment_id: int, status: PaymentStatus, transaction_hash: Optional[str] = None) -> \
            Optional[Payment]:
        try:
            update_data = {
                "status": status.value if hasattr(status, 'value') else status,
                "updated_at": datetime.utcnow()
            }

            if transaction_hash:
                update_data["transaction_hash"] = transaction_hash

            result = await self.session.execute(
                update(PaymentORM)
                .where(PaymentORM.id == payment_id)
                .values(**update_data)
                .returning(PaymentORM)
            )

            payment_orm = result.scalar_one_or_none()
            if not payment_orm:
                return None

            await self.session.commit()
            return self._orm_to_entity(payment_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating payment status for {payment_id}: {e}")
            raise DatabaseException(f"Failed to update payment status: {e}")

    def _orm_to_entity(self, payment_orm: PaymentORM) -> Payment:
        return Payment(
            id=payment_orm.id,
            user_id=payment_orm.user_id,
            amount=float(payment_orm.amount),
            status=PaymentStatus(payment_orm.status),
            cash_register=payment_orm.cash_register,
            invoice_id=payment_orm.invoice_id,
            transaction_hash=payment_orm.transaction_hash,
            created_at=payment_orm.created_at,
            updated_at=payment_orm.updated_at
        )
