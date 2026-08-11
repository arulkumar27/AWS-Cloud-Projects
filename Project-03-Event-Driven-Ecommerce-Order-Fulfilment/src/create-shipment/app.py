import json
import uuid
from datetime import datetime, timedelta, timezone


def lambda_handler(event, context):
    shipment_id = f"SHIP-{uuid.uuid4().hex[:10].upper()}"
    tracking_number = f"TRK-{uuid.uuid4().hex[:12].upper()}"

    current_time = datetime.now(timezone.utc)
    estimated_delivery = current_time + timedelta(days=5)

    print(
        json.dumps(
            {
                "level": "INFO",
                "message": "Shipment created",
                "orderId": event["orderId"],
                "shipmentId": shipment_id,
                "trackingNumber": tracking_number
            }
        )
    )

    return {
        **event,
        "shipmentId": shipment_id,
        "trackingNumber": tracking_number,
        "shipmentStatus": "CREATED",
        "status": "SHIPMENT_CREATED",
        "shipmentCreatedAt": current_time.isoformat(),
        "estimatedDelivery": estimated_delivery.date().isoformat()
    }