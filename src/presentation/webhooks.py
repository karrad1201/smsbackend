from fastapi import APIRouter, Request, Depends, HTTPException, status
from src.services.payment_service import PaymentService
from src.services.heleket_service import HeleketService
from src.core.domain.entity.payment import PaymentStatus
from src.core.di import get_payment_service, get_heleket_service
from src.core.logging_config import get_logger
import json

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhook/heleket")
async def handle_heleket_webhook(
        request: Request,
        payment_service: PaymentService = Depends(get_payment_service),
        heleket_service: HeleketService = Depends(get_heleket_service)
):
    try:
        body = await request.body()
        webhook_data = json.loads(body.decode('utf-8'))

        logger.info(f"Received Heleket webhook: {webhook_data}")
        logger.info(f"Webhook headers: {dict(request.headers)}")

        signature_header = request.headers.get("sign") or request.headers.get("X-Signature")
        signature_body = webhook_data.pop("sign", None)

        signature = signature_header or signature_body

        if signature:
            is_valid = heleket_service.verify_webhook_signature(webhook_data, signature)
            if not is_valid:
                logger.warning(f"Invalid webhook signature: {signature}")
                return {"status": "error", "message": "Invalid signature"}
            logger.info("Webhook signature verified successfully")
        else:
            logger.warning("No signature found in webhook request")
            return {"status": "error", "message": "No signature"}

        invoice_id = webhook_data.get("uuid")
        payment_status = webhook_data.get("status")
        transaction_hash = webhook_data.get("txid")
        amount = webhook_data.get("amount")
        currency = webhook_data.get("currency")

        if not invoice_id:
            logger.error("No invoice ID in webhook data")
            return {"status": "error", "message": "No invoice id"}

        if not payment_status:
            logger.error("No payment status in webhook data")
            return {"status": "error", "message": "No payment status"}

        payment = await payment_service.get_payment_by_invoice(invoice_id)
        if not payment:
            logger.error(f"Payment not found for invoice: {invoice_id}")
            return {"status": "error", "message": "Payment not found"}

        status_mapping = {
            "check": PaymentStatus.PENDING,
            "paid": PaymentStatus.COMPLETED,
            "expired": PaymentStatus.CANCELLED,
            "failed": PaymentStatus.FAILED
        }

        new_status = status_mapping.get(payment_status, PaymentStatus.PENDING)
        
        logger.info(f"Processing payment {payment.id}: {payment_status} -> {new_status}")

        if payment.status == PaymentStatus.COMPLETED and new_status == PaymentStatus.COMPLETED:
            logger.info(f"Payment {payment.id} already processed, skipping")
            return {"status": "ok", "message": "Already processed"}

        updated_payment = await payment_service.update_payment_status(
            payment.id,
            new_status,
            transaction_hash
        )

        if not updated_payment:
            logger.error(f"Failed to update payment {payment.id} status")
            return {"status": "error", "message": "Failed to update payment status"}

        if new_status == PaymentStatus.COMPLETED:
            logger.info(f"Processing balance topup for payment {payment.id}, amount: {payment.amount}")
            
            success = await payment_service.process_balance_topup(
                payment.id,
                payment.amount
            )
            
            if success:
                logger.info(f"Successfully processed balance topup for payment {payment.id}")
            else:
                logger.error(f"Failed to process balance topup for payment {payment.id}")
                return {"status": "error", "message": "Failed to process balance topup"}

        logger.info(f"Webhook processed successfully for payment {payment.id}")
        return {"status": "ok"}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook body: {e}")
        return {"status": "error", "message": "Invalid JSON"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
