# Security Design

## Overview

This project uses layered security controls across networking, compute, identity, storage, and monitoring.

The primary security objective is to prevent direct internet access to application instances while still allowing users to access the application through the load balancer.

## Security Architecture

```text
Internet User
    ↓
Application Load Balancer Security Group
    ↓
Application Security Group
    ↓
Private EC2 Instances
```

Administrative access:

```text
Administrator Public IP
    ↓
Bastion Security Group
    ↓
Bastion Host
    ↓
Transit Gateway
    ↓
Application Security Group
    ↓
Private EC2 Instance
```

## Network Isolation

Two separate VPCs were used:

```text
Application VPC: 10.0.0.0/16
Management VPC:  10.1.0.0/16
```

This separation prevents public management resources from being deployed inside the same network segment as the application instances.

## Public and Private Subnets

### Public resources

The following resources were deployed in public subnets:

* Application Load Balancer
* NAT Gateway
* Bastion Host

### Private resources

The application EC2 instances were deployed in private subnets.

They had:

```text
Public IPv4 address: Disabled
Direct internet ingress: Not allowed
Outbound internet access: NAT Gateway only
```

## Security Groups

### Load Balancer Security Group

```text
Name: Project1-nlb-sg
```

Inbound rule:

```text
Protocol: TCP
Port: 80
Source: 0.0.0.0/0
Purpose: Allow public HTTP application traffic
```

SSH was not allowed on the load balancer.

### Application Security Group

```text
Name: Project1-app-sg
```

Inbound rules:

```text
HTTP 80 from Project1-nlb-sg
SSH 22 from 10.1.0.0/16
```

HTTP traffic was accepted only from the load balancer Security Group.

SSH traffic was accepted only from the Management VPC network.

The application instances did not accept direct HTTP or SSH connections from the internet.

### Bastion Security Group

```text
Name: Project1-bastion-sg
```

Inbound rule:

```text
Protocol: TCP
Port: 22
Source: Administrator public IPv4 address/32
```

Using `/32` restricts SSH access to one approved public IPv4 address.

The SSH source was updated when the administrator’s public IP changed.

## Bastion Host Security

The Bastion Host acted as the controlled entry point for private EC2 administration.

Security controls included:

* Public SSH allowed only from an approved IP
* Key-based authentication
* No password-based login
* PuTTY Pageant agent forwarding
* Private key not copied to the Bastion Host
* Private instances accessed using their private IPv4 addresses

Connection flow:

```text
PuTTY
  ↓
Project1-Bastion
  ↓
Transit Gateway
  ↓
Private App EC2
```

## SSH Key Management

The EC2 key pair was created as:

```text
Project1-key.pem
```

For PuTTY, it was converted to:

```text
Project1-key.ppk
```

Security practices followed:

* Private keys were stored only on the administrator’s laptop
* Private keys were not uploaded to EC2 instances
* Pageant was used for agent forwarding
* Public-key authentication was used instead of passwords
* The key pair was deleted after project cleanup

## IAM Role Security

The application EC2 instances used:

```text
Project1-app-ec2-role
```

The role provided temporary AWS credentials through the EC2 metadata service.

No static access key or secret access key was stored on the server.

Attached permissions included:

```text
AmazonSSMManagedInstanceCore
CloudWatchAgentServerPolicy
Project-specific S3 inline policy
```

## Least-Privilege S3 Access

The inline S3 policy was restricted to one project bucket.

Bucket-level actions:

```text
s3:ListBucket
s3:GetBucketLocation
```

Object-level actions:

```text
s3:GetObject
s3:PutObject
s3:DeleteObject
```

The policy did not provide access to every S3 bucket in the account.

Correct ARN formats:

```text
Bucket ARN:
arn:aws:s3:::project1-app-storage-arulkumar-20260804

Object ARN:
arn:aws:s3:::project1-app-storage-arulkumar-20260804/*
```

## EC2 Metadata Security

The Launch Template enforced:

```text
Metadata endpoint: Enabled
Metadata version: IMDSv2 only
```

IMDSv2 requires session-oriented metadata requests and provides stronger protection against unauthorized metadata access.

## S3 Bucket Security

The project bucket used:

```text
ACLs: Disabled
Block Public Access: Enabled
Versioning: Enabled
Server-side encryption: SSE-S3
```

The bucket was not used as a public website.

Application access occurred through the EC2 IAM role.

## NAT Gateway Security

Private application instances used the NAT Gateway for outbound connectivity.

This allowed them to:

* Install operating-system packages
* Download application dependencies
* Access public AWS endpoints

The NAT Gateway did not allow unsolicited inbound connections from the internet to the private instances.

## Transit Gateway Security

Transit Gateway connected only the required VPC CIDR ranges:

```text
Management to Application:
10.0.0.0/16

Application to Management:
10.1.0.0/16
```

Routes were added only to the route tables that required inter-VPC communication.

## Load Balancer Health Checks

The load balancer continuously checked:

```text
Protocol: HTTP
Port: 80
Path: /
Expected status: 200
```

Unhealthy instances were removed from traffic distribution.

Auto Scaling could replace failed instances, helping maintain application availability.

## Monitoring and Alerting

CloudWatch alarms monitored:

```text
High EC2 CPU utilization
Unhealthy load balancer targets
```

Alarm notifications were delivered through a confirmed SNS email subscription.

This allowed operational issues to be detected without continuously checking the AWS Console.

## Security Limitations

The learning implementation had the following limitations:

* HTTP was used instead of HTTPS
* Bastion Host had a public IPv4 address
* SSH was allowed from the full Management VPC CIDR
* A single NAT Gateway created an Availability Zone dependency
* VPC Flow Logs were not enabled
* AWS WAF was not configured
* CloudTrail analysis was not included
* Outbound Security Group rules remained open

## Production Security Improvements

For production use:

* Add an ACM certificate
* Configure an HTTPS listener on port 443
* Redirect HTTP traffic to HTTPS
* Add AWS WAF managed rules
* Replace Bastion access with Systems Manager Session Manager
* Enable VPC Flow Logs
* Enable centralized CloudTrail logging
* Use an S3 Gateway VPC Endpoint
* Restrict outbound Security Group rules
* Use KMS customer-managed keys where required
* Add GuardDuty threat detection
* Store secrets in AWS Secrets Manager
* Apply S3 lifecycle and retention policies
* Regularly rotate and remove unused SSH keys
* Add AWS Config compliance rules

## Security Outcome

The final architecture ensured that:

* Users could access only the load balancer
* Application instances remained private
* Administrative access was restricted
* AWS credentials were supplied using IAM roles
* S3 remained private and encrypted
* Failed targets were detected automatically
* Security-related operational events generated alerts
