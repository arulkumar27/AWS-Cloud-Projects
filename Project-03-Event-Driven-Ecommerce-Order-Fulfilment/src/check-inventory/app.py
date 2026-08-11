import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")

INVENTORY_TABLE = os.environ["INVENTORY_TABLE"]
inventory_table = dynamodb.Table(INVENTORY_TABLE)


def lambda_handler(event, context):
    product_id = event["productId"]
    requested_quantity = int(event["quantity"])
    updated_at = datetime.now(timezone.utc).isoformat()

    try:
        result = inventory_table.update_item(
            Key={
                "productId": product_id
            },
            UpdateExpression=(
                "SET availableQuantity = availableQuantity - :quantity, "
                "reservedQuantity = if_not_exists(reservedQuantity, :zero) + :quantity, "
                "updatedAt = :updated_at"
            ),
            ConditionExpression=(
                "attribute_exists(productId) AND "
                "availableQuantity >= :quantity"
            ),
            ExpressionAttributeValues={
                ":quantity": requested_quantity,
                ":zero": 0,
                ":updated_at": updated_at
            },
            ReturnValues="ALL_NEW"
        )

        updated_inventory = result["Attributes"]

        print(
            json.dumps(
                {
                    "level": "INFO",
                    "message": "Inventory reserved",
                    "orderId": event["orderId"],
                    "productId": product_id,
                    "quantity": requested_quantity
                }
            )
        )

        return {
            **event,
            "inventoryStatus": "RESERVED",
            "status": "INVENTORY_RESERVED",
            "remainingQuantity": int(
                updated_inventory["availableQuantity"]
            )
        }

    except ClientError as error:
        error_code = error.response["Error"]["Code"]

        if error_code == "ConditionalCheckFailedException":
            print(
                json.dumps(
                    {
                        "level": "WARNING",
                        "message": "Product unavailable or stock insufficient",
                        "orderId": event["orderId"],
                        "productId": product_id
                    }
                )
            )

            raise RuntimeError("INVENTORY_UNAVAILABLE")

        raise