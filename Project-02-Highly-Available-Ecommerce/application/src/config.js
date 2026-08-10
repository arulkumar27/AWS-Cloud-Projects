'use strict';

function loadConfig(env = process.env) {
  return {
    port: Number(env.PORT || 3000),
    region: env.AWS_REGION || 'ap-south-1',
    secretId: env.DB_SECRET_ARN || '',
    dbHost: env.DB_HOST || '',
    dbCaPath: env.DB_CA_PATH || '/etc/ecommerce/global-bundle.pem',
    database: env.DB_NAME || 'ecommerce',
    assetsBucket: env.ASSETS_BUCKET || '',
    nodeEnv: env.NODE_ENV || 'production'
  };
}

module.exports = { loadConfig };
