# Troubleshooting Guide

## Overview

This document records the major issues encountered during the project, their root causes, diagnostic methods, and resolutions.

## 1. Load Balancer DNS Not Working

### Symptoms

The load balancer DNS name did not initially open in the browser.

```text
Project1-NLB-593815959.ap-south-2.elb.amazonaws.com
```

### Diagnostic checks

The following components were verified:

```text
Load balancer state: Active
Scheme: Internet-facing
Listener: HTTP 80
Target group: Project1-App-TG
Healthy targets: 2
Unhealthy targets: 0
```

The Security Group was checked for:

```text
HTTP
TCP
Port 80
Source 0.0.0.0/0
```

The URL was tested using:

```text
http://
```

instead of:

```text
https://
```

### Resolution

After verifying the listener, Security Group, healthy targets, public-subnet mappings, and HTTP protocol, the application became accessible.

### Lesson learned

If targets are healthy but the website is unavailable, check:

1. Load balancer scheme
2. Listener protocol and port
3. Load balancer Security Group
4. Public-subnet route to the Internet Gateway
5. Correct use of HTTP or HTTPS
6. Load balancer status

## 2. ApplicationELB vs NetworkELB Metrics

### Symptoms

`NetworkELB` was not visible under CloudWatch metrics.

Only this namespace appeared:

```text
ApplicationELB
```

### Root cause

The resource was named:

```text
Project1-NLB
```

However, its actual AWS type was:

```text
Application Load Balancer
```

Evidence included:

```text
Load balancer type: Application
Listener: HTTP:80
ARN path: loadbalancer/app/
```

### Resolution

CloudWatch metrics were selected from:

```text
CloudWatch
→ Metrics
→ ApplicationELB
```

### Lesson learned

A resource name does not determine its AWS resource type. Always verify:

* Load balancer type
* ARN
* Listener protocol
* CloudWatch namespace

## 3. Bastion SSH Connection Timeout

### Symptoms

PowerShell returned:

```text
WARNING: TCP connect to BASTION_PUBLIC_IP:22 failed
TcpTestSucceeded: False
```

### Diagnosis

The port was tested using:

```powershell
Test-NetConnection BASTION_PUBLIC_IP -Port 22
```

A timeout indicated a networking or firewall problem rather than an SSH-key problem.

### Root cause

The Bastion Security Group did not contain the administrator’s current public IPv4 address.

Public IP addresses can change when:

* The router reconnects
* The ISP renews the connection
* The user switches between networks
* A VPN is enabled or disabled

### Resolution

The Bastion Security Group SSH rule was updated:

```text
Type: SSH
Port: 22
Source: My IP
CIDR: Current public IP/32
```

The test was repeated:

```powershell
Test-NetConnection BASTION_PUBLIC_IP -Port 22
```

Successful result:

```text
TcpTestSucceeded: True
```

### Lesson learned

A TCP timeout usually indicates:

* Incorrect public IP
* Incorrect Security Group source
* Missing Internet Gateway route
* Wrong subnet
* Network ACL restriction
* Local or corporate firewall restriction

An invalid private key normally produces:

```text
Permission denied (publickey)
```

not a timeout.

## 4. Private EC2 Permission Denied

### Symptoms

The Bastion Host reached the private EC2 instance, but authentication failed:

```text
ubuntu@PRIVATE_IP: Permission denied (publickey)
```

### Root cause

The private key was available to PuTTY for the Bastion connection but was not forwarded to the Bastion SSH session.

### Resolution

The following actions were completed:

1. Converted `Project1-key.pem` to `Project1-key.ppk`.
2. Opened Pageant.
3. Added `Project1-key.ppk` to Pageant.
4. Enabled `Allow agent forwarding` in PuTTY.
5. Reconnected to the Bastion Host.
6. Verified the forwarded key:

```bash
ssh-add -L
```

7. Connected to the private instance:

```bash
ssh ubuntu@PRIVATE_APP_IP
```

### Lesson learned

Do not copy private keys to the Bastion Host.

Use:

* PuTTY agent forwarding
* OpenSSH agent forwarding
* ProxyJump
* AWS Systems Manager Session Manager

## 5. S3 AccessDenied Error

### Symptoms

The application instance returned:

```text
AccessDenied when calling the ListObjectsV2 operation
```

AWS reported that the assumed EC2 role was not authorized to perform:

```text
s3:ListBucket
```

### Root cause

The S3 bucket name in the IAM policy did not exactly match the actual bucket name.

Incorrect policy bucket:

```text
project1-app-storage-arulkumar27-20260804
```

Actual bucket:

```text
project1-app-storage-arulkumar-20260804
```

### Resolution

The IAM policy was corrected to use:

```text
arn:aws:s3:::project1-app-storage-arulkumar-20260804
```

for bucket-level actions and:

```text
arn:aws:s3:::project1-app-storage-arulkumar-20260804/*
```

for object-level actions.

The following tests then succeeded:

```bash
aws s3 ls \
s3://project1-app-storage-arulkumar-20260804/logs/
```

```bash
echo "Project1 S3 access test" \
| aws s3 cp - \
s3://project1-app-storage-arulkumar-20260804/logs/connectivity-test.txt
```

### Lesson learned

S3 permissions require different resource formats:

```text
Bucket actions → arn:aws:s3:::bucket-name
Object actions → arn:aws:s3:::bucket-name/*
```

Bucket names must match exactly.

## 6. CloudWatch Metrics Not Immediately Visible

### Symptoms

Load balancer metrics were not immediately visible after resource creation.

### Causes

Possible reasons included:

* No application traffic had reached the load balancer
* Metrics had not yet been published
* The wrong AWS region was selected
* The wrong CloudWatch namespace was selected
* The incorrect load balancer type was assumed

### Resolution

Traffic was generated by refreshing:

```text
http://www.blacktunes.in
```

The following settings were selected:

```text
Region: ap-south-2
Time range: 1 hour
Period: 1 minute
Namespace: ApplicationELB
```

The CloudWatch page was refreshed after waiting several minutes.

### Lesson learned

CloudWatch metrics are not always instantaneous. Confirm the region, resource type, namespace, and traffic before diagnosing a missing metric.

## 7. Alarm Initially Shows Insufficient Data

### Symptoms

A new CloudWatch alarm showed:

```text
INSUFFICIENT_DATA
```

### Cause

CloudWatch had not collected enough datapoints to evaluate the alarm.

### Resolution

The configured evaluation period was allowed to complete.

The alarm later changed to:

```text
OK
```

### Lesson learned

`INSUFFICIENT_DATA` immediately after alarm creation is often expected and does not necessarily indicate a configuration failure.

## 8. Target Group Shows Initial State

### Symptoms

Newly launched targets temporarily showed:

```text
Initial
```

### Cause

The user-data script was still:

* Updating Ubuntu packages
* Installing Nginx
* Creating the web page
* Starting the Nginx service

### Resolution

The health-check grace period allowed initialization to complete.

The targets later changed to:

```text
Healthy
```

### Diagnostic commands

On the instance:

```bash
sudo systemctl status nginx
```

```bash
curl http://localhost
```

```bash
sudo tail -n 100 /var/log/cloud-init-output.log
```

## 9. Target Group Is Unhealthy

If a target remains unhealthy, verify:

```text
Target port: 80
Health-check protocol: HTTP
Health-check path: /
Success code: 200
Application Security Group source: Load Balancer Security Group
Nginx service: Active
```

Useful commands:

```bash
sudo systemctl is-active nginx
```

```bash
sudo ss -lntp | grep ':80'
```

```bash
curl -I http://localhost
```

```bash
sudo nginx -t
```

## 10. Transit Gateway Connection Timeout

If the Bastion cannot reach a private instance, verify:

### Management route

```text
10.0.0.0/16 → Transit Gateway
```

### Application return route

```text
10.1.0.0/16 → Transit Gateway
```

### Application Security Group

```text
SSH 22 from 10.1.0.0/16
```

### Transit Gateway attachments

```text
Management attachment: Available
Application attachment: Available
```

Both forward and return routes are required.

## 11. NAT Gateway Failure

If private instances cannot install packages, check:

```text
NAT Gateway state: Available
NAT Gateway subnet: Public subnet
NAT Gateway Elastic IP: Assigned
Public subnet route: 0.0.0.0/0 → Internet Gateway
Private subnet route: 0.0.0.0/0 → NAT Gateway
```

Test from the private instance:

```bash
curl -I https://aws.amazon.com
```

```bash
sudo apt-get update
```

## 12. Resource Deletion Dependency Errors

AWS resources must be removed in dependency order.

Recommended order:

1. Auto Scaling Group
2. Load Balancer
3. Target Group
4. Launch Template
5. Bastion Host
6. Transit Gateway attachments
7. Transit Gateway
8. NAT Gateway
9. Elastic IP
10. VPCs
11. S3 bucket
12. IAM role
13. CloudWatch alarms
14. SNS resources
15. Route 53 record
16. Key pair

If a VPC cannot be deleted, check for:

* Running EC2 instances
* Network interfaces
* NAT Gateways
* Load balancers
* Transit Gateway attachments
* VPC endpoints
* Elastic IP associations

## Troubleshooting Method

For each issue:

1. Identify the failing traffic path.
2. Confirm the AWS region.
3. Check resource state.
4. Check source and destination.
5. Verify Security Groups.
6. Verify route tables.
7. Verify target health.
8. Review CloudWatch metrics.
9. Review application and cloud-init logs.
10. Change only one configuration at a time.
11. Retest after every change.
12. Document the root cause and final resolution.
