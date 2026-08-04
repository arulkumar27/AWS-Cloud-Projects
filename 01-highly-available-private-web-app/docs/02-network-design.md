# Network Design

## Overview

The project uses two separate Virtual Private Clouds:

1. Application VPC
2. Management VPC

The Application VPC hosts the web application infrastructure, while the Management VPC provides controlled administrative access.

AWS Transit Gateway connects the two VPCs.

## Network Architecture

```text
Internet
   │
   ├── Application Load Balancer
   │       ↓
   │   Private App EC2 Instances
   │
   └── Bastion Host
           ↓
      Transit Gateway
           ↓
      Private App EC2 Instances
```

## Application VPC

```text
Name: Project1-vpc
CIDR: 10.0.0.0/16
Region: ap-south-2
```

The Application VPC contains two public subnets and two private subnets across two Availability Zones.

### Public subnets

| Subnet          | CIDR          | Availability Zone | Resources                     |
| --------------- | ------------- | ----------------- | ----------------------------- |
| Public Subnet 1 | `10.0.1.0/24` | `ap-south-2a`     | Load Balancer and NAT Gateway |
| Public Subnet 2 | `10.0.2.0/24` | `ap-south-2b`     | Load Balancer                 |

The public subnets have routes to an Internet Gateway.

### Private subnets

| Subnet               | CIDR           | Availability Zone | Resources                  |
| -------------------- | -------------- | ----------------- | -------------------------- |
| Private App Subnet 1 | `10.0.11.0/24` | `ap-south-2a`     | Auto Scaling EC2 instances |
| Private App Subnet 2 | `10.0.12.0/24` | `ap-south-2b`     | Auto Scaling EC2 instances |

The private subnets do not assign public IPv4 addresses to EC2 instances.

## Management VPC

```text
Name: management-vpc
CIDR: 10.1.0.0/16
Region: ap-south-2
```

The Management VPC contains one public subnet.

| Subnet                   | CIDR          | Availability Zone | Resources    |
| ------------------------ | ------------- | ----------------- | ------------ |
| Management Public Subnet | `10.1.1.0/24` | `ap-south-2a`     | Bastion Host |

The Bastion Host receives a public IPv4 address and accepts SSH traffic only from the administrator’s approved public IP.

## Internet Gateway

Each VPC has its own Internet Gateway.

### Application Internet Gateway

Provides internet connectivity to:

* Application Load Balancer
* NAT Gateway

### Management Internet Gateway

Provides internet connectivity to:

* Bastion Host

An Internet Gateway does not automatically make a subnet public. The subnet’s route table must contain:

```text
0.0.0.0/0 → Internet Gateway
```

## NAT Gateway

A public NAT Gateway was deployed in Application Public Subnet 1.

```text
Name: Project1-nat-1a
Subnet: 10.0.1.0/24
Connectivity type: Public
Elastic IP: Assigned
```

The NAT Gateway allowed private EC2 instances to:

* Download operating-system updates
* Install Nginx and AWS CLI
* Access external repositories
* Reach public AWS service endpoints

Traffic flow:

```text
Private EC2
    ↓
Private Route Table
    ↓
NAT Gateway
    ↓
Internet Gateway
    ↓
Internet
```

Internet users cannot initiate connections to private instances through the NAT Gateway.

For a production environment, one NAT Gateway should be deployed in each Availability Zone.

## Route Tables

### Application public route table

Associated with:

```text
10.0.1.0/24
10.0.2.0/24
```

Routes:

```text
Destination       Target
10.0.0.0/16       Local
0.0.0.0/0         Internet Gateway
```

### Private route table for AZ 2a

Associated with:

```text
10.0.11.0/24
```

Routes:

```text
Destination       Target
10.0.0.0/16       Local
10.1.0.0/16       Transit Gateway
0.0.0.0/0         NAT Gateway
```

### Private route table for AZ 2b

Associated with:

```text
10.0.12.0/24
```

Routes:

```text
Destination       Target
10.0.0.0/16       Local
10.1.0.0/16       Transit Gateway
0.0.0.0/0         NAT Gateway
```

### Management public route table

Associated with:

```text
10.1.1.0/24
```

Routes:

```text
Destination       Target
10.1.0.0/16       Local
10.0.0.0/16       Transit Gateway
0.0.0.0/0         Internet Gateway
```

## Transit Gateway

AWS Transit Gateway connects the Management VPC and Application VPC.

```text
Name: Project1-TGW
Amazon-side ASN: 64512
DNS support: Enabled
Default route-table association: Enabled
Default route-table propagation: Enabled
```

Two VPC attachments were created:

```text
Project1-TGW-Management-Attachment
Project1-TGW-App-Attachment
```

Traffic flow:

```text
Bastion Host: 10.1.1.x
        ↓
Management Route Table
        ↓
Transit Gateway
        ↓
Application Private Route Table
        ↓
Private App EC2: 10.0.11.x or 10.0.12.x
```

Both forward and return routes are required. Without the return route to `10.1.0.0/16`, the private instance cannot respond to the Bastion Host.

## Application Load Balancer

The internet-facing Application Load Balancer was deployed across both Application VPC public subnets.

```text
Scheme: Internet-facing
IP address type: IPv4
Listener: HTTP 80
```

Traffic flow:

```text
Internet User
    ↓
Route 53
    ↓
Application Load Balancer
    ↓
Target Group
    ↓
Healthy Private EC2 Instance
```

Although the deployed resource was named `Project1-NLB`, its actual AWS resource type was an Application Load Balancer.

## Target Group

The target group used EC2 instance targets.

```text
Target port: 80
Health-check protocol: HTTP
Health-check path: /
Success code: 200
```

The Auto Scaling Group automatically registered and deregistered application instances.

## DNS Routing

Route 53 used an Alias A record:

```text
Record: www.blacktunes.in
Target: Application Load Balancer
Routing policy: Simple
Evaluate target health: Enabled
```

DNS flow:

```text
www.blacktunes.in
    ↓
Route 53
    ↓
Application Load Balancer DNS
```

## Security Group Traffic

### Load Balancer Security Group

```text
Inbound:
TCP 80 from 0.0.0.0/0
```

### Application Security Group

```text
Inbound:
TCP 80 from Load Balancer Security Group
TCP 22 from 10.1.0.0/16
```

### Bastion Security Group

```text
Inbound:
TCP 22 from administrator-public-ip/32
```

## Network Validation

The following network tests were completed:

* Load balancer DNS resolved successfully
* `www.blacktunes.in` opened successfully
* Both target-group instances became healthy
* Bastion SSH port validated using `Test-NetConnection`
* Bastion Host connected to a private EC2 instance
* Transit Gateway routing worked in both directions
* Private EC2 accessed the internet through the NAT Gateway
* Private EC2 accessed Amazon S3 using its IAM role

## Production Recommendations

For production use:

* Deploy a NAT Gateway in each Availability Zone
* Use dedicated Transit Gateway attachment subnets
* Enable VPC Flow Logs
* Use Systems Manager Session Manager instead of public SSH
* Add HTTPS using ACM
* Redirect HTTP to HTTPS
* Add AWS WAF
* Use an S3 Gateway VPC Endpoint
* Restrict outbound Security Group rules
* Monitor NAT Gateway and Transit Gateway traffic
* Automate the network using Terraform or CloudFormation
