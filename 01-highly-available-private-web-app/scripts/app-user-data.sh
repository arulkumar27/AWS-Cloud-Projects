#!/bin/bash
set -e

apt-get update -y
apt-get install -y nginx awscli

HOST_NAME=$(hostname)
PRIVATE_IP=$(hostname -I | awk '{print $1}')

cat > /var/www/html/index.html <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project1 AWS Application</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            color: #ffffff;
            text-align: center;
            background: linear-gradient(135deg, #182848, #4b6cb7);
        }

        .card {
            width: 90%;
            max-width: 650px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.12);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
        }

        h1 {
            margin-top: 0;
            color: #ff9900;
        }

        .status {
            color: #73e673;
            font-weight: bold;
        }

        .details {
            margin-top: 25px;
            padding: 20px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.2);
        }

        .footer {
            margin-top: 25px;
            color: #d7e3ff;
            font-size: 14px;
        }
    </style>
</head>

<body>
    <main class="card">
        <h1>Project1 AWS Application</h1>

        <p class="status">
            Application is running successfully
        </p>

        <section class="details">
            <p><strong>Server:</strong> $HOST_NAME</p>
            <p><strong>Private IP:</strong> $PRIVATE_IP</p>
        </section>

        <p>
            This application is hosted securely on an EC2 instance
            inside an AWS private subnet.
        </p>

        <p class="footer">
            Application Load Balancer | Auto Scaling | Multi-AZ
        </p>
    </main>
</body>
</html>
EOF

systemctl enable nginx
systemctl restart nginx
