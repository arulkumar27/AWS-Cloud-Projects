# AWS Resource Cleanup Checklist

Delete resources in dependency order to prevent errors and continued AWS charges.

## 1. Stop Deployments

- Disable the Project 02 GitHub Actions workflow.
- Remove unused Project 02 GitHub repository variables.

## 2. Auto Scaling and EC2

1. Set Auto Scaling minimum capacity to `0`.
2. Set desired capacity to `0`.
3. Set maximum capacity to `0`.
4. Wait for Auto Scaling instances to terminate.
5. Delete the Auto Scaling group.
6. Terminate any remaining project EC2 instances.
7. Delete the launch template and its versions.

## 3. Load Balancing

1. Delete the Application Load Balancer.
2. Wait for the ALB to finish deleting.
3. Delete the target group.

## 4. Database

1. Disable RDS deletion protection if enabled.
2. Delete the RDS instance.
3. Create a final snapshot only when the data must be retained.
4. Delete unused manual RDS snapshots.
5. Delete the RDS subnet group.
6. Schedule deletion of the database secret.
7. Delete these Parameter Store values:

```text
/ecommerce/prod/db-secret-arn
/ecommerce/prod/db-host
/ecommerce/prod/assets-bucket
```

## 5. S3 Storage

1. Delete all current S3 objects.
2. Delete previous object versions.
3. Delete all delete markers.
4. Delete the project S3 bucket.

A versioned bucket cannot be deleted until all versions and delete markers are removed.

## 6. Route 53, CloudFront, WAF and ACM

1. Delete Project 02 Route 53 application records.
2. Disable the CloudFront distribution.
3. Wait until CloudFront finishes deploying the disabled configuration.
4. Delete the CloudFront distribution.
5. Disassociate and delete the project WAF Web ACL.
6. Delete unused WAF rules, IP sets and rule groups.
7. Delete the CloudFront ACM certificate from `us-east-1`.
8. Delete the regional ALB ACM certificate if one was created.

Do not delete a shared Route 53 hosted zone or registered domain.

## 7. Monitoring

Delete project-specific:

- CloudWatch alarms
- CloudWatch dashboard
- CloudWatch log groups that are no longer required
- SNS topic
- SNS subscriptions

## 8. NAT Gateways and Elastic IPs

1. Delete both NAT gateways.
2. Wait until their status becomes `Deleted`.
3. Release both Elastic IP addresses.

NAT gateways and unused Elastic IP addresses can continue generating charges.

## 9. AMI, Snapshots and Volumes

1. Deregister the project golden AMI.
2. Delete its associated EBS snapshot.
3. Delete unused project EBS snapshots.
4. Delete unattached project EBS volumes.

## 10. IAM

Delete project-specific:

- EC2 application role
- EC2 instance profile
- GitHub Actions deployment role
- Inline policies
- Customer-managed policies used only by this project

Keep the GitHub OIDC identity provider if another project uses it.

This project does not use CodeBuild, CodePipeline or CodeDeploy roles.

## 11. Security Groups and Subnets

1. Delete the RDS security group.
2. Delete the application security group.
3. Delete the ALB security group.
4. Delete both database subnets.
5. Delete both private application subnets.
6. Delete both public subnets.

If a security group or subnet cannot be deleted, check for remaining network interfaces.

## 12. Route Tables and VPC

1. Delete custom route-table associations.
2. Delete custom route tables.
3. Detach the Internet Gateway.
4. Delete the Internet Gateway.
5. Delete the VPC.

The AWS-created main route table is deleted automatically with the VPC.

## 13. Final Billing Audit

Check for remaining resources in every Region used by the project:

- EC2 instances
- EBS volumes
- EBS snapshots
- AMIs
- Elastic IP addresses
- Load balancers
- Target groups
- Auto Scaling groups
- Launch templates
- NAT gateways
- Network interfaces
- RDS instances and snapshots
- S3 buckets and object versions
- Secrets Manager secrets
- Parameter Store values
- CloudFront distributions
- WAF Web ACLs
- ACM certificates
- Route 53 records
- CloudWatch alarms and log groups
- SNS topics
- IAM roles and policies

Review:

```text
AWS Billing
Cost Explorer
Free Tier usage
AWS Credits
AWS Budgets
```

AWS billing information can take time to update after resources are deleted.
