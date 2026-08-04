# Testing and Validation

## Overview

This document describes the tests performed to validate the networking, application, security, storage, load balancing, Auto Scaling, DNS, and monitoring components.

## 1. Application Load Balancer Test

The load balancer DNS endpoint was tested using HTTP.

```text
http://Project1-NLB-593815959.ap-south-2.elb.amazonaws.com
```

Expected result:

```text
Project1 application page loads successfully
HTTP response code: 200
```

Result:

```text
Passed
```

## 2. Route 53 Domain Test

The Route 53 Alias A record was tested using:

```text
http://www.blacktunes.in
```

Expected result:

```text
Domain resolves to the Application Load Balancer
Application page opens successfully
```

Result:

```text
Passed
```

## 3. Target Group Health Test

The target group was checked under:

```text
EC2
→ Target Groups
→ Project1-App-TG
→ Targets
```

Expected result:

```text
Registered targets: 2
Healthy targets: 2
Unhealthy targets: 0
```

Result:

```text
Passed
```

## 4. Multi-AZ Test

The Auto Scaling instances were checked under:

```text
EC2
→ Auto Scaling Groups
→ Project1-App-ASG
→ Instance management
```

Expected distribution:

```text
Instance 1 → ap-south-2a
Instance 2 → ap-south-2b
```

Result:

```text
Passed
```

## 5. Auto Scaling Capacity Test

The Auto Scaling Group configuration was verified.

```text
Minimum capacity: 2
Desired capacity: 2
Maximum capacity: 4
```

Expected result:

```text
Two instances remain InService during normal operation
The group can scale out to a maximum of four instances
```

Result:

```text
Passed
```

> A sustained high-load scale-out test was not performed. The configuration and target-tracking policy were validated through the AWS Console.

## 6. Bastion Port Test

The Bastion Host’s SSH port was tested from Windows PowerShell:

```powershell
Test-NetConnection BASTION_PUBLIC_IP -Port 22
```

Expected result:

```text
TcpTestSucceeded : True
```

Initial result:

```text
Failed
```

After updating the Bastion Security Group to the current administrator public IP:

```text
Passed
```

## 7. Bastion Login Test

PuTTY was configured with:

```text
Username: ubuntu
Port: 22
Private key: Project1-key.ppk
Agent forwarding: Enabled
```

Expected result:

```text
Successful login to Project1-Bastion
```

Result:

```text
Passed
```

## 8. Private EC2 Connectivity Test

From the Bastion Host:

```bash
ssh ubuntu@10.0.11.98
```

Initial result:

```text
Permission denied (publickey)
```

After loading the PPK key into Pageant and enabling agent forwarding:

```text
Passed
```

This validated:

```text
Management VPC
→ Transit Gateway
→ Application VPC
→ Private EC2
```

## 9. Nginx Service Test

On the private application instance:

```bash
sudo systemctl is-active nginx
```

Expected output:

```text
active
```

Application response test:

```bash
curl http://localhost
```

Expected result:

```text
HTML application page returned
```

Result:

```text
Passed
```

## 10. EC2 IAM Role Test

The assumed IAM identity was checked using:

```bash
aws sts get-caller-identity
```

Expected ARN format:

```text
arn:aws:sts::ACCOUNT_ID:assumed-role/Project1-app-ec2-role/INSTANCE_ID
```

Result:

```text
Passed
```

This confirmed that the EC2 instance received temporary credentials through its IAM role.

## 11. S3 Listing Test

The private EC2 instance attempted to list the project log prefix:

```bash
aws s3 ls \
s3://project1-app-storage-arulkumar-20260804/logs/
```

Initial result:

```text
AccessDenied
```

Root cause:

```text
The bucket name in the IAM policy did not exactly match
the actual bucket name.
```

After correcting the bucket ARN:

```text
Passed
```

## 12. S3 Upload Test

A test object was uploaded from the private EC2 instance:

```bash
echo "Project1 S3 access test from $(hostname)" \
| aws s3 cp - \
s3://project1-app-storage-arulkumar-20260804/logs/connectivity-test.txt
```

Expected result:

```text
upload successful
```

Verification:

```bash
aws s3 ls \
s3://project1-app-storage-arulkumar-20260804/logs/
```

Expected object:

```text
connectivity-test.txt
```

Result:

```text
Passed
```

## 13. CloudWatch CPU Alarm Test

The alarm was checked under:

```text
CloudWatch
→ Alarms
→ Project1-ASG-High-CPU
```

Expected normal state:

```text
OK
```

Observed state:

```text
OK
```

Result:

```text
Passed
```

## 14. Unhealthy Target Alarm Test

The alarm was checked under:

```text
CloudWatch
→ Alarms
→ Project1-ALB-Unhealthy-Host
```

Expected normal state:

```text
OK
```

Observed state:

```text
OK
```

Result:

```text
Passed
```

> An actual target failure was not deliberately triggered. The alarm configuration and normal OK state were validated.

## 15. SNS Subscription Test

The SNS subscription was checked under:

```text
SNS
→ Subscriptions
```

Expected status:

```text
Confirmed
```

Result:

```text
Passed
```

## 16. Security Validation

The following controls were verified:

```text
Application EC2 public IPv4: Not assigned
Application HTTP source: Load Balancer Security Group
Application SSH source: 10.1.0.0/16
Bastion SSH source: Administrator IP/32
S3 Block Public Access: Enabled
S3 ACLs: Disabled
IAM role used instead of static credentials
```

Result:

```text
Passed
```

## 17. Resource Cleanup Validation

After completing the project, the following chargeable resources were removed:

* Auto Scaling Group
* Application Load Balancer
* EC2 instances
* Target Group
* Launch Template
* NAT Gateway
* Unused Elastic IP
* Transit Gateway attachments
* Transit Gateway
* Project VPCs
* S3 bucket
* IAM role
* CloudWatch alarms
* SNS topic and subscription
* Route 53 project record
* EC2 key pair

Result:

```text
Completed
```

## Final Validation Summary

| Test                              | Result    |
| --------------------------------- | --------- |
| Load balancer application access  | Passed    |
| Route 53 domain routing           | Passed    |
| Target-group health               | Passed    |
| Multi-AZ instance distribution    | Passed    |
| Bastion SSH connectivity          | Passed    |
| Transit Gateway connectivity      | Passed    |
| Private Nginx service             | Passed    |
| IAM role authentication           | Passed    |
| S3 listing and upload             | Passed    |
| CloudWatch CPU alarm              | Passed    |
| CloudWatch unhealthy-target alarm | Passed    |
| SNS email subscription            | Passed    |
| Security controls                 | Passed    |
| Resource cleanup                  | Completed |

## Final Outcome

The project successfully demonstrated a secure, Multi-AZ web application architecture with private compute resources, controlled administrative access, load balancing, Auto Scaling, IAM-based S3 access, DNS routing, monitoring, alerting, and cost-aware cleanup.
