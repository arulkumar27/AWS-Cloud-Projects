'use strict';

const mysql = require('mysql2/promise');
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

async function readDatabaseSecret(config) {
  if (!config.secretId) throw new Error('DB_SECRET_ARN is not configured');
  const client = new SecretsManagerClient({ region: config.region });
  const response = await client.send(new GetSecretValueCommand({ SecretId: config.secretId }));
  return JSON.parse(response.SecretString);
}

async function createPool(config) {
  const secret = await readDatabaseSecret(config);
  const pool = mysql.createPool({
    host: config.dbHost || secret.host,
    port: Number(secret.port || 3306),
    user: secret.username,
    password: secret.password,
    database: config.database,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
    enableKeepAlive: true,
    ssl: { rejectUnauthorized: true }
  });

  await pool.query(`CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )`);

  const [rows] = await pool.query('SELECT COUNT(*) AS count FROM products');
  if (Number(rows[0].count) === 0) {
    await pool.query(
      'INSERT INTO products (name, description, price, image_key) VALUES ?',
      [[
        ['Cloud Backpack', 'Weather-resistant everyday backpack', 2499.00, null],
        ['DevOps Hoodie', 'Premium cotton engineering hoodie', 1799.00, null],
        ['Mechanical Keyboard', 'Compact hot-swappable keyboard', 5999.00, null]
      ]]
    );
  }
  return pool;
}

module.exports = { createPool, readDatabaseSecret };
