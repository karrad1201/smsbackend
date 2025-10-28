from src.core.domain.repository.interfaces import IPaymentRepository, IUserRepository
from src.core.domain.entity.payment import Payment, PaymentCreate, PaymentStatus
from src.core.logging_config import get_logger
from typing import List, Optional


class PaymentService:
    def __init__(self, payment_repo: IPaymentRepository, user_repo: IUserRepository):
        self.payment_repo = payment_repo
        self.user_repo = user_repo
        self.logger = get_logger(__name__)

    async def get_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        return await self.payment_repo.get_by_user_id(user_id, skip, limit)

    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        return await self.payment_repo.get_by_id(payment_id)

    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        return await self.payment_repo.create(payment_data)

    async def update_payment_status(
            self,
            payment_id: int,
            status: PaymentStatus,
            transaction_hash: Optional[str] = None
    ) -> Optional[Payment]:
        return await self.payment_repo.update_status(payment_id, status, transaction_hash)

    async def get_payment_by_invoice(self, invoice_id: str) -> Optional[Payment]:
        return await self.payment_repo.get_by_invoice_id(invoice_id)

    async def update_payment_invoice(
            self,
            payment_id: int,
            invoice_id: str,
            cash_register: Optional[str] = None
    ) -> Optional[Payment]:
        from src.core.domain.entity.payment import PaymentUpdate

        update_data = PaymentUpdate(
            invoice_id=invoice_id,
            cash_register=cash_register
        )
        return await self.payment_repo.update(payment_id, update_data)

    async def process_balance_topup(
            self,
            payment_id: int,
            amount: float
    ) -> bool:
        """
        Обрабатывает успешное пополнение баланса
        """
        try:
            # Получаем платеж
            payment = await self.payment_repo.get_by_id(payment_id)
            if not payment:
                self.logger.error(f"Payment {payment_id} not found")
                return False

            # Обновляем статус платежа на завершенный
            await self.payment_repo.update_status(
                payment_id, 
                PaymentStatus.COMPLETED
            )

            # Пополняем баланс пользователя (Heleket уже конвертировал в USD)
            updated_user = await self.user_repo.update_balance(
                payment.user_id, 
                amount  # amount уже в USD благодаря to_currency в Heleket
            )

            if updated_user:
                self.logger.info(f"Successfully topped up balance for user {payment.user_id}: +{amount} USD")
                return True
            else:
                self.logger.error(f"Failed to update balance for user {payment.user_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error processing balance topup for payment {payment_id}: {e}")
            return False

