# IAM Roles and Permissions

## EC2 Application Role

Role name:

```text
ecommerce-ec2-role
```

Trusted service:

```text
EC2
```

Required permissions:

- Connect to Systems Manager.
- Download deployment artifacts from the project S3 bucket.
- Read project Parameter Store values.
- Retrieve the database secret from Secrets Manager.
- Send logs and metrics to CloudWatch when configured.

Do not attach AdministratorAccess.

## GitHub Actions Role

Role name:

```text
ecommerce-github-actions-role
```

Trusted identity:

```text
token.actions.githubusercontent.com
```

Required trust action:

```text
sts:AssumeRoleWithWebIdentity
```

Trust-policy conditions must verify:

```text
Audience: sts.amazonaws.com
Repository: arulkumar27/AWS-Cloud-Projects
Branch: main
```

Required permissions:

- Upload release artifacts to the project S3 bucket.
- Send commands through Systems Manager.
- Check Systems Manager command status.

GitHub Actions must use OIDC and temporary credentials.

Never store permanent AWS access keys in GitHub.

## GitHub Variables

Configure these repository variables:

```text
AWS_REGION=ap-south-1
AWS_ROLE_ARN=<GITHUB-ACTIONS-ROLE-ARN>
DEPLOYMENT_BUCKET=<PROJECT-S3-BUCKET>
```

These values are configuration, not passwords.

## Security Rules

- Grant only required permissions.
- Restrict access to project resources.
- Use IAM roles instead of IAM user access keys.
- Enable MFA for human AWS users.
- Review role activity after deployment.
- Delete unused project roles during cleanup.
