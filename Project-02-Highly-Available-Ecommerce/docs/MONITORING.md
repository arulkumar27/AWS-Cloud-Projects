# CloudWatch and SNS Monitoring

## Overview

CloudWatch monitors the application infrastructure. SNS sends email notifications when an alarm changes state.

## SNS Topic

Create:

```text
Topic name: ecommerce-ops-alerts
Topic type: Standard
Subscription: Email
```

Confirm the subscription from your email inbox.

## Recommended CloudWatch Alarms

| Service | Metric | Purpose |
|---|---|---|
| ALB | `UnHealthyHostCount > 0` | Detect unhealthy EC2 targets |
| ALB | `HTTPCode_Target_5XX_Count` | Detect application errors |
| ALB | `TargetResponseTime` | Detect application latency |
| EC2 | `CPUUtilization` | Detect high CPU usage |
| Auto Scaling | In-service instances | Detect capacity problems |
| RDS | `CPUUtilization` | Detect database load |
| RDS | `DatabaseConnections` | Monitor DB connections |
| RDS | `FreeStorageSpace` | Detect low storage |
| CloudFront | 4XX and 5XX error rates | Detect edge/origin errors |
| WAF | Blocked requests | Monitor malicious traffic |

Send alarm notifications to:

```text
ecommerce-ops-alerts
```

## CloudWatch Dashboard

Create:

```text
Dashboard name: Ecommerce-Production
```

Add widgets for:

- ALB request count and response time
- Healthy and unhealthy targets
- EC2 CPU utilization
- Auto Scaling capacity
- RDS CPU, connections and storage
- CloudFront requests and errors
- WAF allowed and blocked requests

## Application Logs

The Node.js application writes logs to systemd journal.

View them using:

```bash
sudo journalctl -u ecommerce.service --no-pager -n 100
```

View Nginx logs:

```bash
sudo tail -n 100 /var/log/nginx/ecommerce-access.log
sudo tail -n 100 /var/log/nginx/ecommerce-error.log
```

A production environment should send these logs to CloudWatch Logs using the CloudWatch Agent.

Never log passwords, access keys or database secret values.

## Validate Notifications

1. Publish a test message to the SNS topic.
2. Confirm that the email arrives.
3. Trigger a safe test alarm.
4. Confirm the alarm notification.
5. Restore the correct alarm threshold.
