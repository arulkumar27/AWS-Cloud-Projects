from datetime import datetime, timezone
from decimal import Decimal

import boto3


TABLE_NAME = "project03-ecommerce-inventory"
REGION = "ap-south-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

products = [
    {
        "productId": "LAPTOP-001",
        "productName": "DevOps Professional Laptop",
        "availableQuantity": 10,
        "reservedQuantity": 0,
        "price": Decimal("55000"),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    },
    {
        "productId": "HEADPHONE-001",
        "productName": "Wireless Headphones",
        "availableQuantity": 20,
        "reservedQuantity": 0,
        "price": Decimal("3500"),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
]

for product in products:
    table.put_item(Item=product)
    print(f"Added product: {product['productId']}")

print("Inventory seeding completed successfully.")