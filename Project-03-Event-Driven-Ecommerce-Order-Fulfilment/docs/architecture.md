# Architecture

```mermaid
flowchart TD
    Client["Client / Postman / PowerShell"]
    API["API Gateway HTTP API"]
    Create["Create Order Lambda"]
    Orders[("DynamoDB Orders")]
    Bus["EventBridge Custom Bus"]
    Rule["OrderCreated Rule"]
    Queue["SQS Order Queue"]
    Starter["Start Workflow Lambda"]
    DLQ["SQS Dead-Letter Queue"]

    subgraph Workflow["Step Functions Order Fulfilment"]
        Validate["Validate Order"]
        Inventory["Check Inventory"]
        Payment["Process Payment"]
        Shipment["Create Shipment"]
        Update["Update Order"]
        Failure["Handle Failure"]
    end

    Stock[("DynamoDB Inventory")]
    SNS["SNS Notifications"]
    Email["Admin Email"]
    Monitor["CloudWatch Logs and Alarm"]

    Client -->|"POST /orders"| API
    API --> Create
    Create --> Orders
    Create -->|"OrderCreated"| Bus
    Bus --> Rule
    Rule --> Queue
    Queue --> Starter
    Queue -.->|"Retries exhausted"| DLQ
    Starter --> Workflow

    Validate --> Inventory
    Inventory --> Payment
    Payment --> Shipment
    Shipment --> Update

    Validate -.-> Failure
    Inventory -.-> Failure
    Payment -.-> Failure
    Shipment -.-> Failure
    Update -.-> Failure

    Inventory <--> Stock
    Update --> Orders
    Failure --> Orders
    Update --> SNS
    Failure --> SNS
    SNS --> Email
    DLQ --> Monitor
    Monitor --> SNS
```

## Successful order flow

1. Client submits an order through API Gateway.
2. Create Order Lambda validates the request and stores the initial order.
3. An `OrderCreated` event is published to EventBridge.
4. EventBridge routes the event to the SQS order queue.
5. Start Workflow Lambda consumes the message and starts Step Functions.
6. Step Functions validates the order, reserves inventory, processes payment and creates a shipment.
7. Final details are stored in DynamoDB.
8. SNS sends a fulfilment notification.

## Failure handling

- Invalid orders are routed to the failure handler.
- Insufficient inventory cancels processing before payment.
- Payment failure releases previously reserved inventory.
- SQS retries technical failures.
- Messages exceeding the retry limit move to the DLQ.
- CloudWatch detects DLQ messages and triggers an SNS alert.