# Troubleshooting Runbook

## GitHub OIDC: `Not authorized to perform sts:AssumeRoleWithWebIdentity`

Check:

1. `AWS_ROLE_ARN` points to the intended role and AWS account.
2. The IAM OIDC provider URL is exactly `token.actions.githubusercontent.com`.
3. Audience is `sts.amazonaws.com`.
4. Trust-policy `sub` matches the repository, branch or environment used by the workflow.
5. Workflow permissions include `id-token: write`.

Resource tags do not fix an OIDC trust-policy mismatch.

## SSM deployment remains `Pending`

- Confirm every desired instance shows Ping status `Online` in Systems Manager.
- Confirm SSM Agent is running and the EC2 instance profile is attached.
- Confirm private instances have outbound connectivity to SSM endpoints, either through NAT or VPC endpoints.
- Confirm the two target tags exist on every ASG instance and propagate at launch.
- Inspect Run Command → Command history for invocation-level output.

## SSM deployment remains `InProgress`

`InProgress` for a short time is normal. If it exceeds the workflow timeout, inspect the command output and application logs. A service configured with `Restart=always` can repeatedly fail while the command waits for `/health`.

## `Unit ecommerce.service could not be found`

The deployment stopped before installing `/etc/systemd/system/ecommerce.service`, or the wrong instance was inspected. Verify the release archive and script, then run:

```bash
sudo ls -l /etc/systemd/system/ecommerce.service
sudo systemctl daemon-reload
```

## `connect ECONNREFUSED 127.0.0.1:3306`

The application did not receive the RDS hostname and fell back to localhost. Check:

```bash
sudo grep '^DB_HOST=' /etc/ecommerce/environment
aws ssm get-parameter --name /ecommerce/prod/db-host --query Parameter.Value --output text
```

The parameter value must be the RDS hostname without `https://` and normally without `:3306`.

## `self-signed certificate in certificate chain`

Install the AWS RDS global CA bundle, set `DB_CA_PATH`, and ensure the MySQL client uses that CA with certificate verification enabled. Do not disable TLS verification to make the error disappear.

## Nginx warning: `conflicting server name "_" on 0.0.0.0:80`

Two default server blocks are active. Keep one project configuration and remove/disable the packaged default file. Validate before restarting:

```bash
sudo nginx -T
sudo nginx -t
sudo systemctl restart nginx
```

## One healthy, one unhealthy and one draining target

- `draining` is normal during deregistration until the deregistration delay expires.
- For an unhealthy target, inspect target-health reason codes, then test locally on that instance:

```bash
curl -i http://127.0.0.1/health
sudo systemctl status ecommerce.service --no-pager -l
sudo journalctl -u ecommerce.service --no-pager -n 100
```

Also check the ALB-to-app security-group rule, Nginx state, port 80 listener and health-check path.

## Useful commands

```bash
sudo systemctl status ecommerce.service --no-pager -l
sudo journalctl -u ecommerce.service --no-pager -n 100
sudo nginx -t
curl -i http://127.0.0.1/health
curl -i http://127.0.0.1/api/products
```

## CloudFront Returns 502 or 504

Check:

- ALB targets are healthy.
- CloudFront origin is the correct ALB DNS name.
- CloudFront origin protocol matches the ALB listener.
- The ALB security group allows CloudFront origin traffic.
- The application responds before the CloudFront timeout.
- The ALB certificate matches the origin hostname when HTTPS is used.

Test the ALB directly:

```bash
curl -i http://<ALB-DNS-NAME>/health
curl -i http://<ALB-DNS-NAME>/ready
```

## CloudFront Returns Stale API Data

Disable caching for:

```text
/api/*
/health
/ready
```

Review the CloudFront cache policy, origin request policy, query strings, cookies and forwarded headers.

## AWS WAF Blocks Legitimate Requests

1. Open the WAF Web ACL.
2. Review sampled requests.
3. Identify the exact blocking rule.
4. Change the affected rule to `Count` during investigation.
5. Exclude only the confirmed false-positive subrule.
6. Test again before returning the rule to `Block`.

Do not disable the complete WAF Web ACL without investigation.

## Route 53 Hostname Does Not Work

Confirm:

- The record exists in the correct public hosted zone.
- The A alias points to CloudFront.
- CloudFront status is `Deployed`.
- The application hostname is configured as a CloudFront alternate domain name.
- The ACM certificate matches the hostname.
- The CloudFront ACM certificate was created in `us-east-1`.

Test DNS:

```bash
nslookup <APPLICATION-HOSTNAME>
```

## ACM Certificate Remains Pending Validation

Check:

- The ACM validation CNAME exists in Route 53.
- The CNAME name and value exactly match ACM.
- The certificate was requested in `us-east-1` for CloudFront.
- Duplicate hosted zones are not causing the record to be added to the wrong zone.

Keep the validation CNAME record after the certificate is issued so ACM can renew it.

## Application Is Healthy but Products Do Not Load

The `/health` endpoint checks only the Node.js process.

Check database readiness:

```bash
curl -i http://127.0.0.1/ready
```

Then inspect:

```bash
sudo journalctl -u ecommerce.service --no-pager -n 100
sudo grep '^DB_HOST=' /etc/ecommerce/environment
```

Confirm:

- The RDS endpoint is correct.
- The RDS security group allows port 3306 from the application security group.
- The database secret contains the correct username and password.
- The RDS CA bundle exists.
- The database is available.

## GitHub Workflow Does Not Appear

The workflow must be stored at the repository root:

```text
.github/workflows/project-02-ecommerce-deploy.yml
```

GitHub does not detect workflows stored inside:

```text
Project-02-Highly-Available-Ecommerce/.github/workflows/
```

The workflow trigger must include:

```yaml
paths:
  - "Project-02-Highly-Available-Ecommerce/**"
  - ".github/workflows/project-02-ecommerce-deploy.yml"
```

