from fastapi import APIRouter, Request, Depends, HTTPException, status
from src.services.payment_service import PaymentService
from src.core.domain.entity.payment import PaymentStatus
from src.core.di import get_payment_service
from src.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhooks/heleket")
async def handle_heleket_webhook(
        request: Request,
        payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        webhook_data = await request.json()
        logger.info(f"Received Heleket webhook: {webhook_data}")

        # Валидация подписи
        # signature = request.headers.get("X-Signature")
        # if not _verify_signature(webhook_data, signature):
        #     return {"status": "invalid signature"}

        invoice_id = webhook_data.get("uuid")
        payment_status = webhook_data.get("payment_status")
        transaction_hash = webhook_data.get("txid")

        if not invoice_id:
            return {"status": "error", "message": "No invoice id"}

        payment = await payment_service.get_payment_by_invoice(invoice_id)
        if not payment:
            return {"status": "error", "message": "Payment not found"}

        status_mapping = {
            "check": PaymentStatus.PENDING,
            "paid": PaymentStatus.COMPLETED,
            "expired": PaymentStatus.CANCELLED,
            "failed": PaymentStatus.FAILED
        }

        new_status = status_mapping.get(payment_status, PaymentStatus.PENDING)

        await payment_service.update_payment_status(
            payment.id,
            new_status,
            transaction_hash
        )

        logger.info(f"Updated payment {payment.id} to status {new_status}")
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
