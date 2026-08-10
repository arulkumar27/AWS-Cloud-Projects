# Deployment Guide — AWS Console

This guide recreates the tested project in `ap-south-1`. Replace all placeholder values; never copy another account's IDs or ARNs.

## 0. Before provisioning

1. Sign in with an administrative identity, not the root user for routine work.
2. Select one AWS Region and keep every regional resource there.
3. Create a monthly AWS Budget with actual-cost alerts.
4. Record every resource in a cleanup checklist.

## 1. VPC and subnets

Create `ecommerce-prod-vpc` with IPv4 CIDR `10.0.0.0/16`, DNS resolution enabled and DNS hostnames enabled.

Create six subnets:

| Name | Example CIDR | AZ | Public IPv4 assignment |
|---|---|---|---|
| `ecommerce-public-subnet-1a` | `10.0.1.0/24` | `ap-south-1a` | Enabled |
| `ecommerce-public-subnet-1b` | `10.0.2.0/24` | `ap-south-1b` | Enabled |
| `ecommerce-app-subnet-1a` | `10.0.11.0/24` | `ap-south-1a` | Disabled |
| `ecommerce-app-subnet-1b` | `10.0.12.0/24` | `ap-south-1b` | Disabled |
| `ecommerce-db-subnet-1a` | `10.0.21.0/24` | `ap-south-1a` | Disabled |
| `ecommerce-db-subnet-1b` | `10.0.22.0/24` | `ap-south-1b` | Disabled |

Create and attach `ecommerce-prod-igw`. Create one NAT Gateway in each public subnet with an Elastic IP.

Create the public, two private-app and isolated-DB route tables described in [ARCHITECTURE.md](ARCHITECTURE.md). Confirm subnet associations before proceeding.

## 2. Security groups

Create all security groups in the project VPC:

1. `ecommerce-alb-sg`: inbound HTTP 80 from `0.0.0.0/0`; add HTTPS 443 only when ACM is configured.
2. `ecommerce-app-sg`: inbound HTTP 80 with source `ecommerce-alb-sg`.
3. `ecommerce-rds-sg`: inbound MySQL 3306 with source `ecommerce-app-sg`.

Keep outbound defaults for the lab. Do not create an SSH ingress rule when Session Manager is available.

## 3. RDS and secret

1. RDS → Subnet groups → create `ecommerce-db-subnet-group` using both DB subnets.
2. Create a MySQL database using Full configuration.
3. Select the smallest account-eligible template and Single-AZ for this lab; production requires Multi-AZ.
4. Identifier: `ecommerce-prod-db`; initial database: `ecommerce`.
5. Choose the custom VPC, DB subnet group and `ecommerce-rds-sg`.
6. Set Public access to **No**.
7. Enable storage autoscaling only with a controlled maximum.
8. Set backup retention and deletion protection according to whether the environment is a disposable lab.
9. Store the generated/master credentials in Secrets Manager and note only the secret ARN.

Never place the password in source code, `.env.example`, Parameter Store String parameters or GitHub variables.

## 4. S3 and Parameter Store

Create a globally unique private bucket such as `ecommerce-prod-assets-<suffix>`:

- Block all public access.
- Enable versioning.
- Enable default encryption.
- Optionally add a lifecycle rule for old `deployments/` objects.

Create String parameters:

```text
/ecommerce/prod/db-secret-arn = <SECRET_ARN>
/ecommerce/prod/db-host       = <RDS_ENDPOINT_WITHOUT_PORT>
/ecommerce/prod/assets-bucket = <BUCKET_NAME>
```

Leading slashes are valid and recommended for hierarchical Parameter Store names.

## 5. EC2 role and golden image

Create `ecommerce-ec2-role` with an EC2 trust relationship and an instance profile. Grant only:

- SSM managed-instance core functionality.
- Read access to this project's release prefix in S3.
- `ssm:GetParameter` for the three project parameters.
- `secretsmanager:GetSecretValue` for the project DB secret.

Launch one temporary Amazon Linux instance in a private app subnet with `ecommerce-app-sg` and the instance profile. Use Session Manager to install Node.js 20, Nginx, AWS CLI and required OS updates. Confirm the SSM Ping status is `Online`, then create `ecommerce-nodejs-golden-ami-v1`. Terminate the temporary builder after the AMI is available.

## 6. Target group, ALB and Auto Scaling

1. Create an instance target group on HTTP port 80.
2. Health check path: `/health`; success code: `200`.
3. Create an internet-facing ALB in both public subnets with `ecommerce-alb-sg`.
4. Add HTTP listener 80 forwarding to the target group.
5. Create a launch template using the golden AMI, private app settings, app SG and instance profile.
6. Add tags and enable **Tag new instances**/propagation:
   - `Project=ecommerce-prod`
   - `Environment=production`
7. Create an Auto Scaling group spanning both private app subnets and attach the target group.
8. For the lab, use a controlled small capacity. A production design should normally keep at least two healthy instances.
9. Enable ELB health checks and choose a grace period long enough for service startup.

## 7. GitHub OIDC

In IAM, create the OIDC provider:

```text
Provider URL: https://token.actions.githubusercontent.com
Audience:     sts.amazonaws.com
```

Create `ecommerce-github-actions-role`. Its trust policy must allow `sts:AssumeRoleWithWebIdentity` only for the provider, audience and intended repository/branch. Use the exact `sub` emitted for your repository policy model; GitHub repository renames or identity-policy changes may require an update.

Grant the role only permission to:

- Upload objects under the deployment bucket's `deployments/` prefix.
- Run and inspect SSM commands against tagged project instances.

In GitHub → Settings → Secrets and variables → Actions → Variables, add `AWS_REGION`, `AWS_ROLE_ARN` and `DEPLOYMENT_BUCKET`.

## 8. Run deployment

Push a change within the project path or manually dispatch **Deploy Project 02 Ecommerce**. The workflow will:

1. Check out the repository.
2. Install dependencies with `npm ci`.
3. Run automated tests.
4. Prune development dependencies and build a tar archive.
5. Assume the AWS role through OIDC.
6. Upload the archive to S3.
7. Send SSM Run Command to matching instances.
8. Wait for every invocation to reach a terminal state.

## 9. Validate

Confirm all target-group instances are healthy. Open the ALB DNS name, then test `/health` and `/api/products`. Review application logs through Session Manager if products do not load.

## 10. Complete Edge Architecture

The validated core application used the Application Load Balancer DNS name.

The complete target edge architecture is:

```text
Route 53
  ->
CloudFront with ACM
  ->
AWS WAF
  ->
Application Load Balancer
```

### ACM Certificate

1. Switch to the `us-east-1` Region.
2. Request an ACM public certificate for the application hostname.
3. Select DNS validation.
4. Create the ACM validation CNAME record in Route 53.
5. Wait until the certificate status becomes `Issued`.

CloudFront requires its viewer certificate in `us-east-1`.

### CloudFront

1. Create a CloudFront distribution.
2. Select the Application Load Balancer as the origin.
3. Set Viewer protocol policy to `Redirect HTTP to HTTPS`.
4. Attach the ACM certificate from `us-east-1`.
5. Add the public application hostname as an alternate domain name.
6. Disable caching for `/api/*`, `/health` and `/ready`.
7. Wait until the distribution status becomes `Deployed`.

### AWS WAF

1. Open AWS WAF using Global or CloudFront scope.
2. Create `ecommerce-cloudfront-web-acl`.
3. Associate it with the CloudFront distribution.
4. Add AWS managed rule groups.
5. Add a rate-based rule.
6. Start rules in `Count` mode.
7. Review sampled requests before changing rules to `Block`.

### Route 53

Create an A alias record:

```text
Record name: <APPLICATION-HOSTNAME>
Record type: A
Alias target: CloudFront distribution
Routing policy: Simple
```

The final public hostname should point to CloudFront, not directly to the ALB.

See [EDGE-SECURITY.md](EDGE-SECURITY.md) for the complete configuration.

## 11. Monitoring

1. Create an SNS topic named `ecommerce-ops-alerts`.
2. Add and confirm an email subscription.
3. Create CloudWatch alarms for:
   - Unhealthy ALB targets
   - ALB 5XX responses
   - EC2 CPU utilization
   - Auto Scaling capacity
   - RDS CPU, connections and free storage
   - CloudFront errors
   - WAF blocked requests
4. Send alarm notifications to the SNS topic.
5. Create the `Ecommerce-Production` CloudWatch dashboard.

See [MONITORING.md](MONITORING.md) for monitoring details.

## 12. Final Validation

Validate each layer:

```bash
curl -i http://<ALB-DNS-NAME>/health
curl -i http://<ALB-DNS-NAME>/ready
curl -i http://<ALB-DNS-NAME>/api/products
```

For the complete edge design:

```bash
curl -I https://<APPLICATION-HOSTNAME>/
curl -i https://<APPLICATION-HOSTNAME>/health
curl -i https://<APPLICATION-HOSTNAME>/api/products
```

Confirm:

- GitHub Actions completed successfully.
- EC2 instances are Online in Systems Manager.
- ALB targets are healthy.
- The application connects to RDS.
- CloudFront status is Deployed.
- The Route 53 hostname resolves correctly.
- The ACM certificate is valid.
- WAF metrics are visible.
- SNS notifications are received.
