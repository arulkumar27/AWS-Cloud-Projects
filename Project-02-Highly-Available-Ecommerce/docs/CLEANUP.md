# Dependency-Aware Cleanup Checklist

Use the same Region in which the project was created. Resolve exact resource names before deletion and preserve shared domain/DNS resources.

## 1. Stop deployments

- Disable the GitHub Actions workflow.
- Remove or archive project repository variables after the environment is gone.

## 2. Compute and load balancing

- Set Auto Scaling min, desired and max capacity to `0`.
- Wait for instances to terminate, then delete the Auto Scaling group.
- Delete remaining project EC2 instances.
- Delete the ALB and wait for deletion.
- Delete the target group.
- Delete the launch template and its versions.

## 3. Database and configuration

- Delete RDS; take a final snapshot only if data must be retained.
- For a disposable lab, disable deletion protection and skip the final snapshot intentionally.
- Delete the DB subnet group after RDS is gone.
- Schedule deletion of the project database secret.
- Delete the three `/ecommerce/prod/...` parameters.

## 4. Storage

- Delete every object version and delete marker from the versioned S3 bucket.
- Delete the bucket.
- Deregister the project AMI.
- Delete its associated EBS snapshot.
- Delete orphaned EBS volumes.

## 5. Network cost resources

- Delete both NAT gateways and wait until they are fully deleted.
- Release their Elastic IP addresses.
- Delete any project-created Route 53 record and ACM certificate.
- Keep a shared Route 53 hosted zone and registered domain.

## 6. IAM

- Delete project EC2 and GitHub Actions roles after detaching/deleting their inline policies.
- Delete an optional CodeDeploy role if one was created but unused.
- Keep the GitHub OIDC provider only if another project uses it; otherwise delete it.

## 7. VPC

- Delete project security groups after all ENIs/dependencies disappear.
- Delete all six subnets.
- Delete custom route tables.
- Detach and delete the Internet Gateway.
- Delete the VPC.

If deletion is blocked, inspect remaining network interfaces; they usually identify the dependent ALB, NAT Gateway, RDS instance or EC2 resource.

## 8. Final audit

Check for project resources and unattached billable resources:

- EC2 instances, volumes, snapshots, AMIs and Elastic IPs.
- Load balancers, target groups, Auto Scaling groups and launch templates.
- NAT gateways and network interfaces.
- RDS instances and snapshots.
- S3 buckets and object versions.
- Secrets Manager secrets and Parameter Store parameters.
- Route 53 records and ACM certificates.
- CloudWatch log groups/alarms and SNS topics created only for this project.

Review Billing, Cost Explorer, Free Tier and Credits again after provider billing data updates.

