#!/usr/bin/env bash
set -euo pipefail

REGION="ap-south-1"
SECRET_ARN=$(aws ssm get-parameter --region "$REGION" --name /ecommerce/prod/db-secret-arn --query 'Parameter.Value' --output text)
ASSETS_BUCKET=$(aws ssm get-parameter --region "$REGION" --name /ecommerce/prod/assets-bucket --query 'Parameter.Value' --output text)

install -d -m 0750 -o root -g ec2-user /etc/ecommerce
cat > /etc/ecommerce/environment <<EOF
NODE_ENV=production
PORT=3000
AWS_REGION=$REGION
DB_NAME=ecommerce
DB_SECRET_ARN=$SECRET_ARN
ASSETS_BUCKET=$ASSETS_BUCKET
EOF
chmod 0640 /etc/ecommerce/environment
chown root:ec2-user /etc/ecommerce/environment

install -m 0644 /opt/ecommerce-app/config/ecommerce.service /etc/systemd/system/ecommerce.service
install -m 0644 /opt/ecommerce-app/config/nginx.conf /etc/nginx/conf.d/ecommerce.conf
rm -f /etc/nginx/conf.d/default.conf
systemctl daemon-reload
nginx -t
