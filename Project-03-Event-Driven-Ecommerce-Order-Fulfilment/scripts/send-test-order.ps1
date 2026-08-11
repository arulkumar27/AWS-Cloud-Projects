param(
    [ValidateSet("success", "payment-failure", "inventory-failure")]
    [string]$Scenario = "success"
)

$ErrorActionPreference = "Stop"

$stackName = "project03-event-driven-ecommerce"
$region = "ap-south-1"

$eventFiles = @{
    "success" = "events\create-order.json"
    "payment-failure" = "events\payment-failure.json"
    "inventory-failure" = "events\inventory-failure.json"
}

$apiUrl = aws cloudformation describe-stacks `
    --stack-name $stackName `
    --region $region `
    --query "Stacks[0].Outputs[?OutputKey=='OrderApiUrl'].OutputValue | [0]" `
    --output text

if (-not $apiUrl) {
    throw "Unable to retrieve the API URL."
}

$eventFile = $eventFiles[$Scenario]

if (-not (Test-Path $eventFile)) {
    throw "Event file not found: $eventFile"
}

$requestBody = Get-Content $eventFile -Raw

Write-Host "Testing scenario: $Scenario"
Write-Host "Endpoint: $apiUrl"

$response = Invoke-RestMethod `
    -Uri $apiUrl `
    -Method Post `
    -ContentType "application/json" `
    -Body $requestBody

$response | Format-List