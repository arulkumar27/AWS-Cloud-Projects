import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

ORDERS_TABLE = os.environ["ORDERS_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

orders_table = dynamodb.Table(ORDERS_TABLE)


def lambda_handler(event, context):
    updated_at = datetime.now(timezone.utc).isoformat()

    orders_table.update_item(
        Key={
            "orderId": event["orderId"]
        },
        UpdateExpression=(
            "SET #status = :status, "
            "paymentStatus = :payment_status, "
            "inventoryStatus = :inventory_status, "
            "shipmentStatus = :shipment_status, "
            "transactionId = :transaction_id, "
            "shipmentId = :shipment_id, "
            "trackingNumber = :tracking_number, "
            "estimatedDelivery = :estimated_delivery, "
            "updatedAt = :updated_at"
        ),
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":status": "FULFILLED",
            ":payment_status": event["paymentStatus"],
            ":inventory_status": event["inventoryStatus"],
            ":shipment_status": event["shipmentStatus"],
            ":transaction_id": event["transactionId"],
            ":shipment_id": event["shipmentId"],
            ":tracking_number": event["trackingNumber"],
            ":estimated_delivery": event["estimatedDelivery"],
            ":updated_at": updated_at
        }
    )

    notification_message = {
        "message": "Order fulfilled successfully",
        "orderId": event["orderId"],
        "customerId": event["customerId"],
        "productId": event["productId"],
        "quantity": event["quantity"],
        "amount": event["amount"],
        "status": "FULFILLED",
        "transactionId": event["transactionId"],
        "shipmentId": event["shipmentId"],
        "trackingNumber": event["trackingNumber"],
        "estimatedDelivery": event["estimatedDelivery"]
    }

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Order fulfilled: {event['orderId']}",
        Message=json.dumps(notification_message, indent=2)
    )

    print(
        json.dumps(
            {
                "level": "INFO",
                "message": "Order marked as fulfilled",
                "orderId": event["orderId"]
            }
        )
    )

    return {
        **event,
        "status": "FULFILLED",
        "updatedAt": updated_at
    }