import json
import re


EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def lambda_handler(event, context):
    required_fields = [
        "orderId",
        "customerId",
        "customerEmail",
        "productId",
        "quantity",
        "amount"
    ]

    missing_fields = [
        field for field in required_fields
        if event.get(field) in (None, "")
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    if not re.match(EMAIL_PATTERN, event["customerEmail"]):
        raise ValueError("Invalid customer email address")

    quantity = int(event["quantity"])
    amount = float(event["amount"])

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    validated_order = {
        **event,
        "validationStatus": "VALIDATED",
        "status": "ORDER_VALIDATED"
    }

    print(
        json.dumps(
            {
                "level": "INFO",
                "message": "Order validation completed",
                "orderId": event["orderId"]
            }
        )
    )

    return validated_order