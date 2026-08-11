$ErrorActionPreference = "Stop"

$stackName = "project03-event-driven-ecommerce"
$region = "ap-south-1"

$dlqUrl = aws cloudformation describe-stacks `
    --stack-name $stackName `
    --region $region `
    --query "Stacks[0].Outputs[?OutputKey=='DeadLetterQueueUrl'].OutputValue | [0]" `
    --output text

if (-not $dlqUrl) {
    throw "Unable to retrieve the DLQ URL."
}

$attributes = aws sqs get-queue-attributes `
    --queue-url $dlqUrl `
    --attribute-names `
        ApproximateNumberOfMessages `
        ApproximateNumberOfMessagesNotVisible `
    --region $region |
    ConvertFrom-Json

Write-Host "Dead-letter queue status"
Write-Host "Queue URL: $dlqUrl"
Write-Host "Visible messages: $($attributes.Attributes.ApproximateNumberOfMessages)"
Write-Host "In-flight messages: $($attributes.Attributes.ApproximateNumberOfMessagesNotVisible)"