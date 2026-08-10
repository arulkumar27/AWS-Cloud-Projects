'use strict';

const path = require('node:path');
const express = require('express');
const helmet = require('helmet');
const compression = require('compression');
const pinoHttp = require('pino-http');

function createApp({ pool = null, config = {} } = {}) {
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', 1);
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(compression());
  app.use(express.json({ limit: '32kb' }));
  app.use(pinoHttp());

  app.get('/health', (_req, res) => {
    res.status(200).json({ status: 'healthy', service: 'ecommerce-api' });
  });

  app.get('/ready', async (_req, res) => {
    if (!pool) return res.status(503).json({ status: 'not-ready', database: 'unavailable' });
    try {
      await pool.query('SELECT 1');
      return res.status(200).json({ status: 'ready', database: 'connected' });
    } catch (error) {
      return res.status(503).json({ status: 'not-ready', database: 'disconnected' });
    }
  });

  app.get('/api/products', async (_req, res, next) => {
    try {
      if (!pool) throw new Error('Database is unavailable');
      const [products] = await pool.query(
        'SELECT id, name, description, price, image_key AS imageKey FROM products ORDER BY id'
      );
      res.json({ products, assetsBucket: config.assetsBucket || null });
    } catch (error) {
      next(error);
    }
  });

  app.use(express.static(path.join(__dirname, '..', 'public'), { maxAge: '1h', etag: true }));
  app.get('/{*splat}', (_req, res) => res.sendFile(path.join(__dirname, '..', 'public', 'index.html')));

  app.use((error, req, res, _next) => {
    req.log?.error({ err: error }, 'request failed');
    res.status(500).json({ error: 'Internal server error' });
  });

  return app;
}

module.exports = { createApp };
