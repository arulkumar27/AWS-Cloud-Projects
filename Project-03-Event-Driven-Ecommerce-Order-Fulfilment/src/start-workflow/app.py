import json
import os

import boto3
from botocore.exceptions import ClientError


stepfunctions = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def lambda_handler(event, context):
    batch_item_failures = []

    for record in event.get("Records", []):
        message_id = record["messageId"]

        try:
            message_body = json.loads(record["body"])

            order = message_body.get("detail", message_body)

            if isinstance(order, str):
                order = json.loads(order)

            order_id = order["orderId"]

            try:
                stepfunctions.start_execution(
                    stateMachineArn=STATE_MACHINE_ARN,
                    name=order_id,
                    input=json.dumps(order)
                )

                print(
                    json.dumps(
                        {
                            "level": "INFO",
                            "message": "Order workflow started",
                            "orderId": order_id
                        }
                    )
                )

            except ClientError as error:
                error_code = error.response["Error"]["Code"]

                if error_code == "ExecutionAlreadyExists":
                    print(
                        json.dumps(
                            {
                                "level": "INFO",
                                "message": "Duplicate order ignored",
                                "orderId": order_id
                            }
                        )
                    )
                else:
                    raise

        except Exception as error:
            print(
                json.dumps(
                    {
                        "level": "ERROR",
                        "message": "Unable to start workflow",
                        "messageId": message_id,
                        "error": str(error)
                    }
                )
            )

            batch_item_failures.append(
                {
                    "itemIdentifier": message_id
                }
            )

    return {
        "batchItemFailures": batch_item_failures
    }