import json
import uuid
from datetime import datetime, timezone


def lambda_handler(event, context):
    order_id = event["orderId"]
    amount = float(event["amount"])

    simulate_failure = event.get("simulatePaymentFailure", False)

    if simulate_failure:
        print(
            json.dumps(
                {
                    "level": "WARNING",
                    "message": "Simulated payment failure",
                    "orderId": order_id
                }
            )
        )

        raise RuntimeError("PAYMENT_FAILED")

    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    processed_at = datetime.now(timezone.utc).isoformat()

    print(
        json.dumps(
            {
                "level": "INFO",
                "message": "Payment processed successfully",
                "orderId": order_id,
                "transactionId": transaction_id,
                "amount": amount
            }
        )
    )

    return {
        **event,
        "paymentStatus": "PAID",
        "status": "PAYMENT_COMPLETED",
        "transactionId": transaction_id,
        "paymentProcessedAt": processed_at
    }