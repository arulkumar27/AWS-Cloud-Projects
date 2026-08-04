# Implementation Guide

## Prerequisites

Before starting, ensure that you have:

* An active AWS account
* Access to the AWS Management Console
* A registered domain in Route 53
* PuTTY, PuTTYgen, and Pageant installed
* Basic knowledge of VPC, EC2, IAM, and Linux
* Selected the `ap-south-2` Hyderabad region

> NAT Gateway, Transit Gateway, Load Balancer, EC2, and public IPv4 resources can generate charges.

## 1. Create the Application VPC

Create a VPC using the **VPC and more** option.

```text
Name: Project1
CIDR: 10.0.0.0/16
Availability Zones: 2
Public subnets: 2
Private subnets: 2
NAT Gateway: None
DNS resolution: Enabled
DNS hostnames: Enabled
```

Configure the subnets:

```text
Public Subnet 1:  10.0.1.0/24  — ap-south-2a
Public Subnet 2:  10.0.2.0/24  — ap-south-2b
Private Subnet 1: 10.0.11.0/24 — ap-south-2a
Private Subnet 2: 10.0.12.0/24 — ap-south-2b
```

Enable automatic public IPv4 assignment only for the two public subnets.

## 2. Create the Management VPC

Create another VPC:

```text
Name: management
CIDR: 10.1.0.0/16
Availability Zones: 1
Public subnets: 1
Private subnets: 0
NAT Gateway: None
DNS resolution: Enabled
DNS hostnames: Enabled
```

Configure its public subnet:

```text
Management Public Subnet: 10.1.1.0/24 — ap-south-2a
```

Enable automatic public IPv4 assignment for this subnet.

## 3. Create the NAT Gateway

Create a Zonal public NAT Gateway:

```text
Name: Project1-nat-1a
VPC: Project1-vpc
Subnet: 10.0.1.0/24
Connectivity type: Public
Elastic IP: Allocate a new Elastic IP
```

Wait until its state becomes `Available`.

Add this route to both private route tables:

```text
0.0.0.0/0 → Project1-nat-1a
```

## 4. Create Security Groups

### Load Balancer Security Group

```text
Name: Project1-nlb-sg
VPC: Project1-vpc

Inbound:
HTTP 80 from 0.0.0.0/0
```

### Bastion Security Group

```text
Name: Project1-bastion-sg
VPC: management-vpc

Inbound:
SSH 22 from administrator-public-ip/32
```

### Application Security Group

```text
Name: Project1-app-sg
VPC: Project1-vpc

Inbound:
HTTP 80 from Project1-nlb-sg
SSH 22 from 10.1.0.0/16
```

## 5. Create the EC2 IAM Role

Create an IAM role with EC2 as its trusted service.

```text
Role name: Project1-app-ec2-role
```

Attach:

```text
AmazonSSMManagedInstanceCore
CloudWatchAgentServerPolicy
```

S3 access is added after creating the project bucket.

## 6. Create the S3 Bucket

Create a private, globally unique bucket:

```text
Bucket name: project1-app-storage-arulkumar-20260804
Region: ap-south-2
ACLs: Disabled
Block Public Access: Enabled
Versioning: Enabled
Encryption: SSE-S3
```

Create these prefixes:

```text
uploads/
logs/
backups/
```

Add a restricted inline policy to the EC2 IAM role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListProject1Bucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::project1-app-storage-arulkumar-20260804"
    },
    {
      "Sid": "ManageProject1Objects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::project1-app-storage-arulkumar-20260804/*"
    }
  ]
}
```

## 7. Create the Bastion Host

Launch an EC2 instance:

```text
Name: Project1-Bastion
AMI: Ubuntu Server 24.04 LTS
Instance type: t3.micro
VPC: management-vpc
Subnet: 10.1.1.0/24
Public IPv4: Enabled
Security Group: Project1-bastion-sg
Storage: 8 GiB gp3
```

Create and download:

```text
Project1-key.pem
```

Convert it to `Project1-key.ppk` using PuTTYgen.

## 8. Create the Transit Gateway

Create a Transit Gateway:

```text
Name: Project1-TGW
Amazon-side ASN: 64512
Default route-table association: Enabled
Default route-table propagation: Enabled
DNS support: Enabled
```

Create two attachments:

```text
Project1-TGW-Management-Attachment
Project1-TGW-App-Attachment
```

Attach the Management VPC using its public subnet.

Attach the Application VPC using its two private subnets.

## 9. Configure Transit Gateway Routes

Add to the Management public route table:

```text
10.0.0.0/16 → Project1-TGW
```

Add to both Application private route tables:

```text
10.1.0.0/16 → Project1-TGW
```

Do not remove the existing Internet Gateway or NAT Gateway routes.

## 10. Create the Launch Template

Create:

```text
Name: Project1-App-Template
AMI: Ubuntu Server 24.04 LTS
Instance type: t3.micro
Key pair: Project1-key
Security Group: Project1-app-sg
IAM role: Project1-app-ec2-role
Storage: 8 GiB gp3
Metadata version: IMDSv2 only
Subnet: Not included
```

Paste the contents of the following file into EC2 user data:

```text
scripts/app-user-data.sh
```

## 11. Create the Target Group

Create an instance-based target group:

```text
Name: Project1-App-TG
Protocol: HTTP
Port: 80
VPC: Project1-vpc
Health-check protocol: HTTP
Health-check path: /
Healthy threshold: 3
Unhealthy threshold: 3
Interval: 10 seconds
Success code: 200
```

Do not manually register instances. Auto Scaling performs registration.

## 12. Create the Auto Scaling Group

Create:

```text
Name: Project1-App-ASG
Launch Template: Project1-App-Template
VPC: Project1-vpc
Subnets: 10.0.11.0/24 and 10.0.12.0/24
Target Group: Project1-App-TG
ELB health checks: Enabled
Health-check grace period: 180 seconds
```

Capacity:

```text
Minimum: 2
Desired: 2
Maximum: 4
```

Scaling policy:

```text
Policy type: Target tracking
Metric: Average CPU utilization
Target value: 60%
Instance warm-up: 180 seconds
```

## 13. Create the Application Load Balancer

Create an internet-facing Application Load Balancer:

```text
Name: Project1-NLB
Scheme: Internet-facing
IP type: IPv4
VPC: Project1-vpc
Subnets: 10.0.1.0/24 and 10.0.2.0/24
Security Group: Project1-nlb-sg
Listener: HTTP 80
Default action: Forward to Project1-App-TG
```

> The resource was named `Project1-NLB`, but its actual AWS type was Application Load Balancer.

Wait until:

```text
Load Balancer state: Active
Targets: Healthy
```

## 14. Configure Route 53

Create an Alias A record:

```text
Record name: www.blacktunes.in
Record type: A
Alias: Enabled
Target: Project1-NLB
Region: ap-south-2
Routing policy: Simple
Evaluate target health: Enabled
```

Test:

```text
http://www.blacktunes.in
```

## 15. Create SNS Notifications

Create an SNS topic:

```text
Name: Project1-Alerts
Type: Standard
```

Create an email subscription and confirm it using the link sent by AWS.

## 16. Create CloudWatch Alarms

### High CPU alarm

```text
Name: Project1-ASG-High-CPU
Metric: CPUUtilization
Dimension: Project1-App-ASG
Statistic: Average
Period: 5 minutes
Threshold: Greater than or equal to 80%
Datapoints: 2 out of 2
Notification: Project1-Alerts
```

### Unhealthy target alarm

```text
Name: Project1-ALB-Unhealthy-Host
Namespace: ApplicationELB
Metric: UnHealthyHostCount
Statistic: Maximum
Period: 1 minute
Threshold: Greater than or equal to 1
Datapoints: 2 out of 2
Notification: Project1-Alerts
```

## 17. Validate Bastion Access

Convert the PEM key to PPK using PuTTYgen, load it into Pageant, and enable agent forwarding in PuTTY.

Connect to the Bastion:

```text
Username: ubuntu
Host: Bastion public IPv4 address
Port: 22
```

From the Bastion, connect to a private instance:

```bash
ssh ubuntu@PRIVATE_APP_IP
```

Verify:

```bash
hostname
hostname -I
curl http://localhost
sudo systemctl is-active nginx
```

## 18. Validate IAM and S3

Confirm the IAM role:

```bash
aws sts get-caller-identity
```

Upload a test object:

```bash
echo "Project1 S3 access test from $(hostname)" \
| aws s3 cp - \
s3://project1-app-storage-arulkumar-20260804/logs/connectivity-test.txt
```

List the objects:

```bash
aws s3 ls \
s3://project1-app-storage-arulkumar-20260804/logs/
```

## 19. Validate Monitoring

Open:

```text
CloudWatch → Metrics → ApplicationELB
```

Review:

```text
RequestCount
TargetResponseTime
HealthyHostCount
UnHealthyHostCount
HTTPCode_Target_2XX_Count
HTTPCode_Target_5XX_Count
```

Confirm both alarms show:

```text
OK
```

## Final Result

The completed architecture provided:

* Multi-AZ application availability
* Automatic instance recovery and scaling
* Private application hosting
* Controlled administrative access
* IAM-based S3 access
* Domain-based application access
* Health monitoring and email notifications
