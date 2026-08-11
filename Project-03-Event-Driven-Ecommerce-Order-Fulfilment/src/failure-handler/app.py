import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

ORDERS_TABLE = os.environ["ORDERS_TABLE"]
INVENTORY_TABLE = os.environ["INVENTORY_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

orders_table = dynamodb.Table(ORDERS_TABLE)
inventory_table = dynamodb.Table(INVENTORY_TABLE)


def lambda_handler(event, context):
    updated_at = datetime.now(timezone.utc).isoformat()

    failure = event.get("failure", {})
    error_name = failure.get("Error", "PROCESSING_ERROR")
    error_cause = failure.get("Cause", "Unknown processing failure")

    if "INVENTORY_UNAVAILABLE" in error_cause:
        final_status = "CANCELLED"
        failure_reason = "INVENTORY_UNAVAILABLE"
        inventory_status = "UNAVAILABLE"
        payment_status = "NOT_PROCESSED"

    elif "PAYMENT_FAILED" in error_cause:
        final_status = "CANCELLED"
        failure_reason = "PAYMENT_FAILED"
        inventory_status = "RELEASED"
        payment_status = "FAILED"

        if event.get("inventoryStatus") == "RESERVED":
            quantity = int(event["quantity"])

            inventory_table.update_item(
                Key={
                    "productId": event["productId"]
                },
                UpdateExpression=(
                    "SET availableQuantity = availableQuantity + :quantity, "
                    "reservedQuantity = reservedQuantity - :quantity, "
                    "updatedAt = :updated_at"
                ),
                ExpressionAttributeValues={
                    ":quantity": quantity,
                    ":updated_at": updated_at
                }
            )

    else:
        final_status = "FAILED"
        failure_reason = error_name
        inventory_status = event.get("inventoryStatus", "UNKNOWN")
        payment_status = event.get("paymentStatus", "UNKNOWN")

    orders_table.update_item(
        Key={
            "orderId": event["orderId"]
        },
        UpdateExpression=(
            "SET #status = :status, "
            "failureReason = :failure_reason, "
            "inventoryStatus = :inventory_status, "
            "paymentStatus = :payment_status, "
            "updatedAt = :updated_at"
        ),
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":status": final_status,
            ":failure_reason": failure_reason,
            ":inventory_status": inventory_status,
            ":payment_status": payment_status,
            ":updated_at": updated_at
        }
    )

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Order processing failed: {event['orderId']}",
        Message=json.dumps(
            {
                "message": "Order processing failed",
                "orderId": event["orderId"],
                "status": final_status,
                "failureReason": failure_reason
            },
            indent=2
        )
    )

    print(
        json.dumps(
            {
                "level": "ERROR",
                "message": "Order failure handled",
                "orderId": event["orderId"],
                "status": final_status,
                "failureReason": failure_reason
            }
        )
    )

    return {
        **event,
        "status": final_status,
        "failureReason": failure_reason,
        "updatedAt": updated_at
    }