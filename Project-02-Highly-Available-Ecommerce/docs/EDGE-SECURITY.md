# Route 53, ACM, CloudFront and AWS WAF

## Overview

The edge layer provides DNS resolution, HTTPS encryption, content delivery and protection against common web attacks.

```text
Users
  |
  v
Route 53
  |
  v
CloudFront + ACM
  |
  v
AWS WAF
  |
  v
Application Load Balancer
  |
  v
EC2 Auto Scaling instances
```

## Final Public Request Flow

```text
shop.example.com
      |
      v
Route 53 alias record
      |
      v
CloudFront distribution
      |
      v
AWS WAF Web ACL
      |
      v
Application Load Balancer
      |
      v
Nginx and Node.js application
```

The public Route 53 application record should point to CloudFront.

Pointing the public application hostname directly to the ALB would bypass CloudFront caching and the CloudFront AWS WAF Web ACL.

## ACM Certificate Placement

Two ACM certificates may be required when HTTPS is used for both connections.

| Connection | Certificate Region | Example hostname |
|---|---|---|
| Browser to CloudFront | `us-east-1` | `shop.example.com` |
| CloudFront to ALB | ALB Region, such as `ap-south-1` | `origin.example.com` |

CloudFront requires its viewer certificate to be created in the `us-east-1` Region.

The optional ALB certificate must be created in the Region where the ALB is deployed.

Use DNS validation and keep the ACM validation CNAME records in Route 53 so that ACM can renew the certificates automatically.

## Route 53 Configuration

Open the existing Route 53 public hosted zone.

Create an A alias record:

```text
Record name: shop.example.com
Record type: A
Alias: Yes
Route traffic to: CloudFront distribution
Routing policy: Simple
Evaluate target health: No
```

Create an AAAA alias record only when IPv6 is enabled for the CloudFront distribution.

Keep the ACM validation CNAME records.

Do not create multiple public hosted zones for the same domain unless DNS delegation is intentionally configured.

## CloudFront Distribution

Create a CloudFront distribution using the Application Load Balancer as the origin.

### Origin settings

```text
Origin domain: Application Load Balancer DNS name
Origin type: Custom origin
Origin protocol policy: HTTP only or HTTPS only
HTTP port: 80
HTTPS port: 443
```

Use `HTTPS only` between CloudFront and the ALB only when:

- The ALB has an HTTPS listener.
- The ALB uses a valid regional ACM certificate.
- The certificate matches the CloudFront origin hostname.

For a temporary lab, CloudFront can connect to the ALB using HTTP while viewers connect to CloudFront using HTTPS.

### Viewer settings

```text
Viewer protocol policy: Redirect HTTP to HTTPS
Allowed HTTP methods: GET, HEAD and OPTIONS
Compress objects automatically: Yes
```

Include POST, PUT, PATCH and DELETE methods only when the application API requires them.

### Alternate domain name

Add the public application hostname:

```text
shop.example.com
```

Select the ACM certificate created in `us-east-1`.

Wait until the CloudFront distribution status becomes:

```text
Deployed
```

## CloudFront Cache Behaviors

Recommended cache behaviors:

| Path pattern | Methods | Caching |
|---|---|---|
| `/styles.css` | GET and HEAD | Enabled |
| `/app.js` | GET and HEAD | Enabled |
| `/images/*` | GET and HEAD | Enabled |
| `/health` | GET and HEAD | Disabled or very short |
| `/ready` | GET and HEAD | Disabled |
| `/api/*` | Required API methods | Disabled initially |
| Default `/*` | GET and HEAD | Conservative caching |

Do not cache dynamic API responses until their data, query strings, headers and cookies are fully understood.

For `/api/*`, use a disabled caching policy initially.

Forward only the headers, cookies and query strings required by the application.

## AWS WAF Web ACL

Open AWS WAF in:

```text
Global resources / CloudFront / us-east-1
```

Create:

```text
Web ACL name: ecommerce-cloudfront-web-acl
Resource type: CloudFront distributions
Default action: Allow
```

Associate it with the e-commerce CloudFront distribution.

## Recommended WAF Rules

| Priority | Rule | Initial action | Purpose |
|---:|---|---|---|
| 10 | Amazon IP reputation list | Count | Detect suspicious IP addresses |
| 20 | AWS Core rule set | Count | Protect against common attacks |
| 30 | Known bad inputs | Count | Detect known malicious input |
| 40 | Rate-based rule | Count | Limit abusive request volume |
| 50 | Optional IP/geographic rules | Count | Apply business restrictions |

Start managed and custom rules in `Count` mode.

Review WAF sampled requests before changing rules to `Block`.

This reduces the risk of blocking legitimate users.

## Rate-Based Rule

Create a rate-based rule according to expected application traffic.

Example configuration:

```text
Rule name: ecommerce-rate-limit
Rule type: Rate-based rule
Evaluation window: 5 minutes
Action: Count initially
Aggregate by: Source IP address
```

Do not select an extremely low request limit without observing normal application traffic.

After validation, change the action from `Count` to `Block`.

## SQL Injection and Cross-Site Scripting Protection

AWS managed rule groups can detect common patterns associated with:

- SQL injection
- Cross-site scripting
- Path traversal
- Invalid request bodies
- Known malicious payloads
- Scanner and bot activity

Managed rules reduce risk but do not replace secure application coding, input validation, prepared SQL statements or dependency updates.

## Prevent Direct ALB Access

If users can access the ALB DNS name directly, they may bypass CloudFront and the CloudFront WAF Web ACL.

For stronger production protection:

1. Restrict the ALB security group to the AWS-managed CloudFront origin-facing prefix list.
2. Configure CloudFront to send a secret custom origin header.
3. Configure an ALB listener rule or regional WAF rule to reject requests without the expected header.
4. Store and rotate the origin-header value securely.
5. Do not expose the secret header in client-side code or public documentation.

Do not rely only on hiding the ALB DNS name.

## Edge Monitoring

Enable CloudWatch metrics for:

- CloudFront requests
- CloudFront 4XX error rate
- CloudFront 5XX error rate
- CloudFront cache-hit rate
- WAF allowed requests
- WAF blocked requests
- WAF counted requests

Use WAF sampled requests to investigate blocked and counted traffic.

Full WAF logging is optional and may create additional charges.

## Validation

Test the public hostname:

```bash
curl -I https://shop.example.com/
curl -i https://shop.example.com/health
curl -i https://shop.example.com/api/products
```

Confirm:

- The HTTPS certificate is valid.
- HTTP redirects to HTTPS.
- The hostname resolves through Route 53.
- CloudFront serves the application.
- The ALB has healthy targets.
- Static assets use the expected cache behavior.
- API responses are not incorrectly cached.
- WAF metrics and sampled requests are visible.
- Direct ALB access is restricted when origin protection is enabled.

## Common Problems

### CloudFront returns 502 or 504

Check:

- ALB target health
- CloudFront origin protocol
- ALB listener ports
- ALB certificate hostname
- Application response time
- Security-group rules

### CloudFront returns stale API data

Disable caching for `/api/*` and review the cache policy.

### WAF blocks legitimate traffic

Inspect sampled requests and identify the exact terminating rule.

Temporarily use `Count` mode or exclude only the specific false-positive rule.

Do not disable the entire Web ACL without investigating.

### Route 53 hostname does not open

Confirm:

- The record exists in the correct hosted zone.
- The record points to CloudFront.
- CloudFront status is `Deployed`.
- The alternate domain name is configured.
- The `us-east-1` ACM certificate is attached and issued.
