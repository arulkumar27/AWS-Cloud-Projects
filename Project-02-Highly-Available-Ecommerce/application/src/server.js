'use strict';

const { loadConfig } = require('./config');
const { createPool } = require('./db');
const { createApp } = require('./app');

async function start() {
  const config = loadConfig();
  const pool = await createPool(config);
  const app = createApp({ pool, config });
  const server = app.listen(config.port, '127.0.0.1', () => {
    console.log(JSON.stringify({ level: 'info', message: 'server started', port: config.port }));
  });

  const shutdown = () => server.close(async () => {
    await pool.end();
    process.exit(0);
  });
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

start().catch((error) => {
  console.error(JSON.stringify({ level: 'fatal', message: error.message }));
  process.exit(1);
});
