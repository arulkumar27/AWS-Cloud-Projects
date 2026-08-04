# AWS Resource Cleanup Guide

## Overview

This document explains how the project resources were deleted after testing to prevent unnecessary AWS charges.

> Resource deletion is permanent. Confirm that no important data is required before deleting S3 objects, EC2 instances, or other resources.

## AWS Region

The project was deployed in:

```text
Asia Pacific (Hyderabad)
ap-south-2
```

Always confirm the correct AWS region before checking for remaining resources.

## Deletion Order

Resources must be deleted in dependency order:

```text
Auto Scaling Group
    ↓
Application Load Balancer
    ↓
Target Group
    ↓
Launch Template
    ↓
Bastion Host
    ↓
Transit Gateway Attachments
    ↓
Transit Gateway
    ↓
NAT Gateway
    ↓
Elastic IP
    ↓
VPCs
```

## 1. Delete the Auto Scaling Group

Navigate to:

```text
EC2
→ Auto Scaling Groups
→ Project1-App-ASG
```

Delete the Auto Scaling Group.

This automatically terminates the two application EC2 instances managed by the group.

Wait until:

```text
Project1-App-ASG no longer exists
Project1-App-Server instances are terminated
```

## 2. Delete the Application Load Balancer

Navigate to:

```text
EC2
→ Load Balancers
→ Project1-NLB
→ Actions
→ Delete
```

Although the resource was named `Project1-NLB`, its actual AWS resource type was Application Load Balancer.

Wait until the load balancer disappears.

## 3. Delete the Target Group

Navigate to:

```text
EC2
→ Target Groups
→ Project1-App-TG
→ Actions
→ Delete
```

If deletion fails, confirm that the load balancer has already been deleted.

## 4. Delete the Launch Template

Navigate to:

```text
EC2
→ Launch Templates
→ Project1-App-Template
→ Actions
→ Delete template
```

Confirm that all template versions should be deleted.

## 5. Terminate the Bastion Host

Navigate to:

```text
EC2
→ Instances
→ Project1-Bastion
→ Instance state
→ Terminate instance
```

Wait until its state becomes:

```text
Terminated
```

## 6. Delete Transit Gateway Attachments

Navigate to:

```text
VPC
→ Transit Gateway attachments
```

Delete:

```text
Project1-TGW-Management-Attachment
Project1-TGW-App-Attachment
```

Wait until both attachments are completely deleted.

Transit Gateway attachments can continue generating charges until they are removed.

## 7. Delete the Transit Gateway

Navigate to:

```text
VPC
→ Transit gateways
→ Project1-TGW
→ Actions
→ Delete
```

The Transit Gateway cannot be deleted while active attachments remain.

## 8. Delete the NAT Gateway

Navigate to:

```text
VPC
→ NAT Gateways
→ Project1-nat-1a
→ Actions
→ Delete
```

Wait until the state becomes:

```text
Deleted
```

NAT Gateway hourly charges continue until deletion is completed.

## 9. Release the Elastic IP

After deleting the NAT Gateway, navigate to:

```text
VPC
→ Elastic IP addresses
```

Select the unused Elastic IP previously associated with the NAT Gateway.

Choose:

```text
Actions
→ Release Elastic IP addresses
```

Unused public IPv4 addresses can generate charges.

## 10. Delete the Application VPC

Navigate to:

```text
VPC
→ Your VPCs
→ Project1-vpc
→ Actions
→ Delete VPC
```

Deleting the VPC also removes its:

- Subnets
- Route tables
- Internet Gateway
- Network ACLs
- Security Groups created for the project

If deletion fails, check for remaining:

- Network interfaces
- NAT Gateways
- Load balancers
- EC2 instances
- Transit Gateway attachments
- VPC endpoints
- Elastic IP associations

## 11. Delete the Management VPC

Navigate to:

```text
VPC
→ Your VPCs
→ management-vpc
→ Actions
→ Delete VPC
```

Confirm that the Bastion Host and Transit Gateway attachment were already removed.

## 12. Empty the S3 Bucket

Navigate to:

```text
S3
→ project1-app-storage-arulkumar-20260804
→ Empty
```

Enter:

```text
permanently delete
```

Because bucket versioning was enabled, ensure that the operation removes:

- Current objects
- Previous object versions
- Delete markers

S3 objects and versions cannot be recovered after permanent deletion.

## 13. Delete the S3 Bucket

After the bucket is empty:

```text
S3
→ project1-app-storage-arulkumar-20260804
→ Delete
```

Enter the complete bucket name to confirm deletion.

## 14. Delete the IAM Role

Navigate to:

```text
IAM
→ Roles
→ Project1-app-ec2-role
→ Delete
```

The deletion removes the attached project inline policy along with the role.

Do not delete unrelated IAM roles.

## 15. Delete CloudWatch Alarms

Navigate to:

```text
CloudWatch
→ Alarms
→ All alarms
```

Delete:

```text
Project1-ASG-High-CPU
Project1-ALB-Unhealthy-Host
```

## 16. Delete the SNS Subscription

Navigate to:

```text
SNS
→ Subscriptions
```

Delete the email subscription connected to:

```text
Project1-Alerts
```

If its ID displays `Deleted`, no further subscription action is required.

## 17. Delete the SNS Topic

Navigate to:

```text
SNS
→ Topics
→ Project1-Alerts
→ Delete
```

Deleting the topic also removes its remaining subscription references.

## 18. Delete the Route 53 Record

Navigate to:

```text
Route 53
→ Hosted zones
→ blacktunes.in
```

Delete only:

```text
www.blacktunes.in
```

Do not delete:

```text
NS record
SOA record
blacktunes.in hosted zone
```

unless the complete domain configuration is no longer required.

## 19. Delete the ACM Certificate

If an ACM certificate was created only for this project, navigate to:

```text
AWS Certificate Manager
→ Certificates
```

Delete the certificate for:

```text
www.blacktunes.in
```

Do not delete a certificate still used by another application.

## 20. Delete the EC2 Key Pair

Navigate to:

```text
EC2
→ Key pairs
→ Project1-key
→ Delete
```

Delete the local files only if they are no longer required:

```text
Project1-key.pem
Project1-key.ppk
```

## 21. Final Cost Verification

Check the following services in `ap-south-2`:

```text
EC2 instances
Load balancers
NAT Gateways
Elastic IP addresses
Transit Gateways
Transit Gateway attachments
S3 buckets
VPC endpoints
RDS databases
```

Then navigate to:

```text
Billing and Cost Management
→ Bills
```

Review charges for:

- EC2
- Elastic Load Balancing
- NAT Gateway
- Transit Gateway
- Public IPv4
- Route 53
- S3
- Data transfer

Billing data may take several hours to update after deletion.

## Cleanup Validation Checklist

```text
[ ] Auto Scaling Group deleted
[ ] Application EC2 instances terminated
[ ] Application Load Balancer deleted
[ ] Target Group deleted
[ ] Launch Template deleted
[ ] Bastion Host terminated
[ ] Transit Gateway attachments deleted
[ ] Transit Gateway deleted
[ ] NAT Gateway deleted
[ ] Elastic IP released
[ ] Application VPC deleted
[ ] Management VPC deleted
[ ] S3 bucket emptied and deleted
[ ] IAM role deleted
[ ] CloudWatch alarms deleted
[ ] SNS subscription deleted
[ ] SNS topic deleted
[ ] Route 53 project record deleted
[ ] ACM certificate deleted if applicable
[ ] EC2 key pair deleted
[ ] Billing dashboard reviewed
```

## Final Outcome

All project-specific resources were removed after successful testing and validation. This prevented ongoing charges from NAT Gateway, Transit Gateway, Load Balancer, EC2, and public IPv4 resources.
