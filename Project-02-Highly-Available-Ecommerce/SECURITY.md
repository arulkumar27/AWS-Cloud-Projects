# Security Policy

## Project Scope

This repository contains a production-style AWS learning project. It demonstrates security practices for a highly available e-commerce application.

The project must be reviewed and hardened further before processing real customer or payment information.

## Security Architecture

The application uses multiple security layers:

- AWS WAF filters malicious requests at the edge.
- CloudFront provides the public HTTPS entry point.
- The Application Load Balancer distributes traffic to private EC2 instances.
- EC2 application instances do not require inbound SSH.
- Amazon RDS is deployed inside isolated database subnets.
- IAM roles provide temporary AWS permissions.
- Secrets Manager stores database credentials.
- Parameter Store stores non-secret application configuration.
- GitHub Actions uses OIDC instead of permanent AWS access keys.
- RDS connections use TLS certificate verification.
- CloudWatch and SNS provide monitoring and notifications.

## Never Commit Sensitive Information

Never commit the following information:

- AWS access key ID
- AWS secret access key
- AWS session token
- GitHub personal access token
- Database username or password
- Secrets Manager secret value
- Private SSH keys
- `.pem` or `.ppk` files
- Private TLS certificates
- Real `.env` files
- Application production secrets
- Payment or customer information

Only safe placeholders should be stored in `.env.example`.

## GitHub Actions Authentication

GitHub Actions must authenticate to AWS through OpenID Connect.

The workflow requires:

```yaml
permissions:
  contents: read
  id-token: write
```

The AWS IAM role trust policy must restrict access to:

- The GitHub OIDC provider
- The expected AWS audience
- This GitHub repository
- The intended branch or GitHub environment

Static AWS access keys must not be stored in GitHub Actions secrets.

## IAM Security

The EC2 application role should have only the permissions required to:

- Communicate with AWS Systems Manager
- Download deployment artifacts from the project S3 bucket
- Read the project Parameter Store parameters
- Retrieve the project database secret
- Send logs and metrics to CloudWatch when configured

The GitHub deployment role should have only the permissions required to:

- Upload release artifacts to the project S3 bucket
- Send deployment commands through Systems Manager
- Read Systems Manager command status

Administrator policies must not be attached to application or deployment roles.

## Network Security

Recommended security-group flow:

```text
Internet
   |
   v
CloudFront and AWS WAF
   |
   v
Application Load Balancer security group
   |
   v
Application security group
   |
   v
RDS security group
```

Rules:

- The ALB accepts only the required HTTP/HTTPS traffic.
- Application instances accept port 80 only from the ALB security group.
- RDS accepts port 3306 only from the application security group.
- Database subnets have no default internet route.
- SSH port 22 is not publicly exposed.
- Systems Manager Session Manager is used for administrative access.

## S3 Security

The deployment bucket must use:

- Block Public Access
- Object versioning
- Default encryption
- Least-privilege bucket permissions
- Lifecycle rules for old deployment artifacts when appropriate

Application instances should have read access only to the required deployment prefix.

GitHub Actions should have write access only to the required deployment prefix.

## Database Security

Database credentials must remain in AWS Secrets Manager.

The application must:

- Retrieve credentials at runtime
- Use the private RDS endpoint
- Verify the RDS TLS certificate
- Avoid logging database credentials
- Avoid exposing RDS publicly

Production environments should use Multi-AZ RDS, automated backups and tested recovery procedures.

## Logging Security

Application logs must not contain:

- Passwords
- Access keys
- Session tokens
- Secret JSON values
- Customer payment information
- Complete sensitive request bodies

CloudWatch log groups should use appropriate retention periods to control cost and meet operational requirements.

## Secret Exposure Response

If a secret is accidentally committed:

1. Revoke or rotate the exposed credential immediately.
2. Update the affected AWS or GitHub configuration.
3. Review CloudTrail and application logs for unauthorized activity.
4. Remove the secret from Git history.
5. Verify that forks, caches or build artifacts do not retain the secret.
6. Document the incident and corrective actions.

Deleting only the latest Git commit is not sufficient because the credential may remain in Git history.

## Dependency Security

Before deployment:

```bash
cd application
npm ci
npm audit
npm test
```

Review high and critical vulnerabilities before using the application in a production environment.

## Reporting a Security Issue

Do not open a public GitHub issue containing:

- Credentials
- Exploit details
- Private infrastructure information
- Customer or application data

Report security concerns privately to the repository owner.

## Disclaimer

This project is intended for learning, portfolio demonstration and controlled AWS lab environments. It should not be used unchanged for a real production e-commerce platform.
