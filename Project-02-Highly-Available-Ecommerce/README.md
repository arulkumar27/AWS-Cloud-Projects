# Highly Available E-Commerce Platform on AWS

Production-style Node.js e-commerce application deployed to private EC2 Auto Scaling instances through GitHub, CodePipeline, CodeBuild, and CodeDeploy. The application reads database credentials from AWS Secrets Manager and runtime configuration from Systems Manager Parameter Store.

## Runtime flow

`CloudFront → WAF → ALB → Nginx → Node.js → RDS MySQL`

## CI/CD flow

`GitHub → CodePipeline → CodeBuild → CodeDeploy → EC2 Auto Scaling`

## Required Parameter Store values

- `/ecommerce/prod/db-secret-arn`
- `/ecommerce/prod/assets-bucket`

No passwords, access keys, database endpoints, or account-specific secret values belong in this repository.
