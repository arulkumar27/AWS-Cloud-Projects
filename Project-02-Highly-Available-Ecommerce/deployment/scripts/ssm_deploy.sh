#!/usr/bin/env bash
set -euo pipefail

RELEASE_DIR="${1:-/tmp/ecommerce-release}"
APP_DIR="/opt/ecommerce-app"
REGION="ap-south-1"

echo "Stopping the current application"
systemctl stop ecommerce.service 2>/dev/null || true

echo "Preparing the application directory"
install -d -m 0755 -o ec2-user -g ec2-user "$APP_DIR"
find "$APP_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

echo "Installing the new release"
cp -R "$RELEASE_DIR/src" "$APP_DIR/src"
cp -R "$RELEASE_DIR/public" "$APP_DIR/public"
cp -R "$RELEASE_DIR/node_modules" "$APP_DIR/node_modules"
cp "$RELEASE_DIR/package.json" "$APP_DIR/package.json"
cp "$RELEASE_DIR/package-lock.json" "$APP_DIR/package-lock.json"

install -d -m 0755 "$APP_DIR/config"
cp "$RELEASE_DIR/config/ecommerce.service" "$APP_DIR/config/ecommerce.service"
cp "$RELEASE_DIR/config/nginx.conf" "$APP_DIR/config/nginx.conf"

chown -R ec2-user:ec2-user "$APP_DIR"

echo "Loading runtime configuration from Parameter Store"
SECRET_ARN=$(aws ssm get-parameter \
  --region "$REGION" \
  --name "/ecommerce/prod/db-secret-arn" \
  --query "Parameter.Value" \
  --output text)

ASSETS_BUCKET=$(aws ssm get-parameter \
  --region "$REGION" \
  --name "/ecommerce/prod/assets-bucket" \
  --query "Parameter.Value" \
  --output text)

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

echo "Installing systemd and Nginx configuration"
install -m 0644 \
  "$APP_DIR/config/ecommerce.service" \
  /etc/systemd/system/ecommerce.service

install -m 0644 \
  "$APP_DIR/config/nginx.conf" \
  /etc/nginx/conf.d/ecommerce.conf

rm -f /etc/nginx/conf.d/default.conf

systemctl daemon-reload
nginx -t

echo "Starting the new application"
systemctl enable ecommerce.service
systemctl restart ecommerce.service
systemctl enable nginx
systemctl restart nginx

echo "Validating the deployment"
for attempt in {1..30}; do
  if curl --fail --silent http://127.0.0.1/health >/dev/null; then
    echo "Deployment completed successfully"
    exit 0
  fi

  sleep 3
done

echo "Application health check failed"
journalctl -u ecommerce.service --no-pager -n 100
exit 1
