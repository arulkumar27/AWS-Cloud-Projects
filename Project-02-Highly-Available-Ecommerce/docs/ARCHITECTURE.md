# Architecture and Design Decisions

## Design goals

The design prioritizes tier isolation, multi-AZ application availability, replaceable compute, managed secrets and auditable deployments. It is a production-style learning architecture, not a claim of full production readiness.

## Traffic boundaries

| Source | Destination | Port | Reason |
|---|---|---:|---|
| Internet | ALB security group | 80/443 | Public application entry point |
| ALB security group | App security group | 80 | ALB to Nginx |
| App security group | RDS security group | 3306 | MySQL only |
| App instances | AWS APIs/internet | 443 | SSM, S3, secrets, packages and RDS CA bundle |

Do not add `0.0.0.0/0` inbound rules to the application or database tiers.

## Route tables

- Public route table: local route plus `0.0.0.0/0 → Internet Gateway`; associated with both public subnets.
- Private app route table AZ-a: local route plus `0.0.0.0/0 → NAT Gateway AZ-a`.
- Private app route table AZ-b: local route plus `0.0.0.0/0 → NAT Gateway AZ-b`.
- Isolated DB route table: local route only; associated with both DB subnets.
- VPC main route table: intentionally left without workload subnet associations. AWS always creates a main route table; it is not an extra workload route table.

## Compute path

Nginx listens on port 80 and proxies to Node.js on `127.0.0.1:3000`. Binding Node.js to loopback prevents it from being exposed directly on the instance network interface. systemd starts the service, restarts failures and sends logs to journald.

## Data path

The app retrieves the secret value from Secrets Manager at runtime and connects to the RDS endpoint supplied through Parameter Store. MySQL TLS uses `/etc/ecommerce/global-bundle.pem` downloaded from the official AWS RDS trust store during deployment.

## Deployment path

GitHub Actions tests and packages the application, assumes an AWS IAM role through OIDC, uploads the versioned archive to S3 and sends an SSM command to instances selected by both tags:

- `Project=ecommerce-prod`
- `Environment=production`

The deployment script stops the service, replaces the application directory, writes runtime configuration, installs systemd/Nginx files, restarts services and polls `/health`.

## Production improvements

- Multi-AZ RDS with automated backups and tested restore procedures.
- HTTPS listener with ACM certificate; redirect HTTP to HTTPS.
- CloudFront and WAF managed rules where edge protection is required.
- VPC endpoints for S3, SSM, EC2 Messages, SSM Messages, Secrets Manager and CloudWatch Logs to reduce NAT dependency.
- Rolling or blue/green deployments with explicit capacity and rollback controls.
- Infrastructure as Code, policy-as-code and drift detection.
- Centralized structured application logs, dashboards, alarms and SNS notifications.
- AWS Backup, RDS Performance Insights and GuardDuty/Security Hub as appropriate.

