from fastapi import APIRouter, Depends, HTTPException, status
from src.services.heleket_service import HeleketService
from src.services.payment_service import PaymentService
from src.core.domain.entity.payment import PaymentCreate, PaymentStatus, PaymentResponse
from src.core.di import get_heleket_service, get_payment_service
from src.core.di import get_current_user
from src.core.domain.entity.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/topup", response_model=PaymentResponse)
async def create_balance_topup(
        amount: float,
        currency: str = "USD",
        current_user: User = Depends(get_current_user),
        heleket_service: HeleketService = Depends(get_heleket_service),
        payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Создает платеж для пополнения баланса пользователя
    """
    try:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )

        # Создаем запись о платеже
        payment_create = PaymentCreate(
            user_id=current_user.id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING
        )

        db_payment = await payment_service.create_payment(payment_create)

        # Создаем платеж в Heleket
        heleket_response = await heleket_service.create_balance_topup(
            amount=amount,
            currency=currency,
            order_id=f"topup_{db_payment.id}",
            user_id=current_user.id
        )

        if heleket_response.get("state") == 0:
            invoice_data = heleket_response["result"]
            
            # Обновляем платеж с данными инвойса
            updated_payment = await payment_service.update_payment_invoice(
                db_payment.id,
                invoice_data["uuid"],
                invoice_data.get("address")
            )

            return PaymentResponse(
                payment_url=invoice_data["url"],
                invoice_id=invoice_data["uuid"],
                status=PaymentStatus.PENDING
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create balance topup in Heleket"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
        payment_data: dict,
        heleket_service: HeleketService = Depends(get_heleket_service),
        payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Deprecated: Используйте /topup для пополнения баланса
    """
    try:
        payment_create = PaymentCreate(
            user_id=payment_data["user_id"],
            amount=payment_data["amount"],
            status=PaymentStatus.PENDING
        )

        db_payment = await payment_service.create_payment(payment_create)

        heleket_response = await heleket_service.create_payment(
            amount=payment_data["amount"],
            currency=payment_data.get("currency", "USD"),
            order_id=str(db_payment.id),
            user_id=payment_data["user_id"],
            **payment_data.get("additional_params", {})
        )

        if heleket_response.get("state") == 0:
            invoice_data = heleket_response["result"]
            updated_payment = await payment_service.update_payment_invoice(
                db_payment.id,
                invoice_data["uuid"],
                invoice_data.get("address")
            )

            return PaymentResponse(
                payment_url=invoice_data["url"],
                invoice_id=invoice_data["uuid"],
                status=PaymentStatus.PENDING
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create payment in Heleket"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get('/{payment_id}')
async def get_payment(
        payment_id: int,
        payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = await payment_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )