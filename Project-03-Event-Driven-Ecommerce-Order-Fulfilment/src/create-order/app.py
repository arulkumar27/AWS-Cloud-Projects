import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3


dynamodb = boto3.resource("dynamodb")
eventbridge = boto3.client("events")

ORDERS_TABLE = os.environ["ORDERS_TABLE"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
orders_table = dynamodb.Table(ORDERS_TABLE)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        required_fields = [
            "customerId",
            "customerEmail",
            "productId",
            "quantity",
            "amount"
        ]

        missing_fields = [
            field for field in required_fields
            if body.get(field) in (None, "")
        ]

        if missing_fields:
            return response(
                400,
                {
                    "message": "Required fields are missing",
                    "missingFields": missing_fields
                }
            )

        quantity = int(body["quantity"])
        amount = Decimal(str(body["amount"]))

        if quantity <= 0 or amount <= 0:
            return response(
                400,
                {
                    "message": "Quantity and amount must be greater than zero"
                }
            )

        order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        order = {
            "orderId": order_id,
            "customerId": body["customerId"],
            "customerEmail": body["customerEmail"],
            "productId": body["productId"],
            "quantity": quantity,
            "amount": amount,
            "simulatePaymentFailure": bool(
                body.get("simulatePaymentFailure", False)
            ),
            "status": "ORDER_RECEIVED",
            "paymentStatus": "PENDING",
            "inventoryStatus": "PENDING",
            "createdAt": created_at,
            "updatedAt": created_at
        }

        orders_table.put_item(
            Item=order,
            ConditionExpression="attribute_not_exists(orderId)"
        )

        event_result = eventbridge.put_events(
            Entries=[
                {
                    "Source": "ecommerce.orders",
                    "DetailType": "OrderCreated",
                    "Detail": json.dumps(order, default=str),
                    "EventBusName": EVENT_BUS_NAME
                }
            ]
        )

        if event_result["FailedEntryCount"] > 0:
            raise RuntimeError("Order event could not be published")

        return response(
            202,
            {
                "message": "Order accepted for processing",
                "orderId": order_id,
                "status": "ORDER_RECEIVED"
            }
        )

    except (ValueError, TypeError, json.JSONDecodeError):
        return response(
            400,
            {
                "message": "Invalid request body"
            }
        )

    except Exception as error:
        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "message": "Order creation failed",
                    "error": str(error)
                }
            )
        )

        return response(
            500,
            {
                "message": "Internal server error"
            }
        )