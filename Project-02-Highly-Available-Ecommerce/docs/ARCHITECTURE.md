# Architecture and Design Decisions

## Overview

This project demonstrates a highly available, three-tier e-commerce application on AWS.

The core ALB-to-application architecture was deployed and tested. Route 53, CloudFront, ACM and AWS WAF represent the complete target edge architecture.

## Complete Request Flow

```text
Users
  ->
Route 53
  ->
CloudFront with ACM
  ->
AWS WAF
  ->
Application Load Balancer
  ->
Nginx on EC2
  ->
Node.js application
  ->
Amazon RDS for MySQL
```

## Network Design

```text
VPC: 10.0.0.0/16
Region: ap-south-1
Availability Zones: ap-south-1a and ap-south-1b
```

| Tier | AZ A | AZ B |
|---|---|---|
| Public | `10.0.1.0/24` | `10.0.2.0/24` |
| Private application | `10.0.11.0/24` | `10.0.12.0/24` |
| Isolated database | `10.0.21.0/24` | `10.0.22.0/24` |

## Route Tables

Public route table:

```text
VPC local route
0.0.0.0/0 -> Internet Gateway
```

Private application route tables:

```text
AZ A: 0.0.0.0/0 -> NAT Gateway A
AZ B: 0.0.0.0/0 -> NAT Gateway B
```

Database route table:

```text
VPC local route only
No internet default route
```

The AWS-created main route table is not associated with workload subnets.

## Security Boundaries

| Source | Destination | Port |
|---|---|---:|
| Internet or CloudFront | ALB security group | 80/443 |
| ALB security group | Application security group | 80 |
| Application security group | RDS security group | 3306 |
| Private EC2 instances | AWS APIs through NAT or endpoints | 443 |

Application and database security groups do not allow unrestricted public inbound access.

## Compute Layer

The Application Load Balancer distributes requests across EC2 instances in two private subnets.

Each instance runs:

```text
Nginx -> Node.js
```

Nginx listens on port 80 and forwards requests to:

```text
127.0.0.1:3000
```

The Node.js process is managed by systemd.

Auto Scaling maintains application capacity and replaces unhealthy instances.

## Database Layer

Amazon RDS for MySQL is deployed using a DB subnet group containing both isolated database subnets.

The application:

- Retrieves credentials from Secrets Manager.
- Reads the RDS hostname from Parameter Store.
- Connects through the RDS security group.
- Uses the AWS RDS CA bundle.
- Verifies the TLS certificate.

The lab used Single-AZ RDS because of account restrictions. Production should use Multi-AZ RDS.

## Edge Layer

The complete target edge architecture uses:

- Route 53 for DNS.
- CloudFront as the public HTTPS entry point.
- ACM for TLS certificates.
- AWS WAF for managed and rate-based rules.
- The ALB as the CloudFront origin.

The CloudFront viewer certificate must be created in `us-east-1`.

The public Route 53 alias points to CloudFront.

See [EDGE-SECURITY.md](EDGE-SECURITY.md) for the complete edge configuration.

## CI/CD Architecture

```text
GitHub push
  ->
GitHub Actions
  ->
AWS OIDC and STS
  ->
S3 release artifact
  ->
Systems Manager Run Command
  ->
Tagged EC2 Auto Scaling instances
```

The project does not use CodeBuild, CodePipeline or CodeDeploy.

GitHub Actions uses temporary AWS credentials instead of permanent access keys.

## Runtime Configuration

Parameter Store contains:

```text
/ecommerce/prod/db-secret-arn
/ecommerce/prod/db-host
/ecommerce/prod/assets-bucket
```

Secrets Manager contains the database username and password.

The deployment script creates:

```text
/etc/ecommerce/environment
```

## Monitoring

CloudWatch monitors:

- ALB health and errors
- EC2 CPU utilization
- Auto Scaling capacity
- RDS CPU, connections and storage
- CloudFront errors
- WAF requests

SNS sends operational email notifications.

## Production Improvements

- Use Multi-AZ RDS.
- Add database migration tooling.
- Add automated readiness, API and database tests.
- Configure Content Security Policy.
- Use rolling or blue/green deployments.
- Add VPC endpoints to reduce NAT dependency.
- Send application and Nginx logs to CloudWatch Logs.
- Implement the infrastructure using Terraform, CDK or CloudFormation.
- Test backup restoration and disaster recovery.
