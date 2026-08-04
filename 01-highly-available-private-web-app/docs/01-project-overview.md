# Project Overview

## Introduction

This project demonstrates how to deploy a secure, highly available, and scalable web application using AWS services.

The application runs on EC2 instances located inside private subnets. An internet-facing Application Load Balancer receives user requests and distributes them across healthy instances managed by an Auto Scaling Group.

Administrative access is separated into a dedicated Management VPC. A Bastion Host and AWS Transit Gateway provide controlled access to the private application instances.

## Project Objectives

The primary objectives were to:

* Deploy application instances without public IPv4 addresses
* Distribute the application across two Availability Zones
* Provide high availability using Auto Scaling
* Distribute traffic using an Application Load Balancer
* Separate management and application resources into different VPCs
* Connect both VPCs using AWS Transit Gateway
* Provide secure administrative access through a Bastion Host
* Provide outbound internet access through a NAT Gateway
* Access a private S3 bucket using an EC2 IAM role
* Configure domain routing using Route 53
* Monitor application health using CloudWatch
* Send email notifications using Amazon SNS
* Validate the complete architecture and remove chargeable resources afterward

## Region

The project was deployed in:

```text
AWS Region: Asia Pacific (Hyderabad)
Region code: ap-south-2
```

The application resources were distributed across:

```text
ap-south-2a
ap-south-2b
```

## Application VPC

The Application VPC hosted the load balancer, NAT Gateway, Auto Scaling Group, and private application instances.

```text
VPC CIDR: 10.0.0.0/16
```

Resources included:

* Two public subnets
* Two private application subnets
* Internet Gateway
* NAT Gateway
* Public and private route tables
* Application Load Balancer
* Auto Scaling Group
* EC2 application instances
* Transit Gateway attachment

## Management VPC

The Management VPC provided controlled administrative access.

```text
VPC CIDR: 10.1.0.0/16
```

Resources included:

* One public subnet
* Internet Gateway
* Public route table
* Bastion Host
* Transit Gateway attachment

## Application Traffic Flow

```text
User
  ↓
Route 53
  ↓
Application Load Balancer
  ↓
Target Group
  ↓
Healthy EC2 application instance
  ↓
Nginx web application
```

The domain used during testing was:

```text
www.blacktunes.in
```

## Administrative Traffic Flow

```text
Administrator
  ↓
SSH from approved public IP
  ↓
Bastion Host
  ↓
Transit Gateway
  ↓
Private application EC2 instance
```

The private instances did not have public IPv4 addresses.

## High Availability

High availability was implemented by:

* Creating private subnets in two Availability Zones
* Maintaining two EC2 instances through an Auto Scaling Group
* Registering instances automatically with a target group
* Performing HTTP health checks through the load balancer
* Replacing unhealthy instances through Auto Scaling
* Scaling between two and four instances based on CPU utilization

Auto Scaling capacity:

```text
Minimum: 2
Desired: 2
Maximum: 4
```

## Security

The architecture used multiple security layers:

* Application instances deployed only in private subnets
* No direct public access to application instances
* SSH access restricted to the Management VPC
* Bastion SSH access restricted to the administrator’s public IP
* Web traffic accepted only from the load balancer
* S3 Block Public Access enabled
* IAM role used instead of static access keys
* IMDSv2 enforced through the Launch Template

## Storage

A private S3 bucket was used for:

* Application uploads
* Logs
* Backups
* Connectivity testing

Access was provided using an EC2 IAM role with permissions restricted to the project bucket.

## Monitoring

CloudWatch monitored:

* EC2 CPU utilization
* Healthy targets
* Unhealthy targets
* Application Load Balancer requests
* Target response time
* HTTP response codes

CloudWatch alarms were connected to an SNS topic for email notifications.

## Validation Results

The following validations were completed successfully:

* Domain resolved to the load balancer
* Application opened through `www.blacktunes.in`
* Both application targets became healthy
* Application traffic was distributed through the load balancer
* Bastion Host accepted SSH from the approved IP
* Private EC2 instance was accessed through the Bastion Host
* Transit Gateway routing worked between both VPCs
* Nginx responded successfully on the private instance
* IAM role credentials were available through AWS STS
* S3 upload and object listing succeeded
* CloudWatch alarms reported an OK state
* SNS email subscription was confirmed

## Cleanup

After validation, all project-specific chargeable resources were deleted, including:

* Auto Scaling Group
* Application Load Balancer
* EC2 instances
* NAT Gateway
* Elastic IP
* Transit Gateway and attachments
* Target Group
* Launch Template
* S3 bucket
* IAM role
* CloudWatch alarms
* SNS topic and subscription
* Route 53 application record
* Project VPCs

This prevented unnecessary AWS charges after the learning exercise.

## Outcome

This project provided practical experience in designing, deploying, securing, monitoring, troubleshooting, and cleaning up a multi-VPC AWS application architecture.

It demonstrates knowledge of real-world Cloud and DevOps concepts including networking, high availability, load balancing, Auto Scaling, IAM authorization, private storage, DNS, monitoring, alerting, and cost management.
