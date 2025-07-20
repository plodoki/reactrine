#!/usr/bin/env node

import http from 'http';
import https from 'https';
import { URL } from 'url';

const OPENAPI_URL = process.env.OPENAPI_URL || 'http://127.0.0.1:8000';
const FULL_URL = `${OPENAPI_URL}/api/v1/openapi.json`;

console.log(`Checking OpenAPI endpoint: ${FULL_URL}`);

const url = new URL(FULL_URL);
const client = url.protocol === 'https:' ? https : http;

const options = {
  hostname: url.hostname,
  port: url.port,
  path: url.pathname + url.search,
  method: 'GET',
  timeout: 5000,
};

const req = client.request(options, res => {
  if (res.statusCode === 200) {
    console.log('✅ OpenAPI endpoint is reachable');
    process.exit(0);
  } else {
    console.error(`❌ OpenAPI endpoint returned status ${res.statusCode}`);
    process.exit(1);
  }
});

req.on('error', err => {
  console.error(`❌ Failed to reach OpenAPI endpoint: ${err.message}`);
  process.exit(1);
});

req.on('timeout', () => {
  console.error('❌ Request to OpenAPI endpoint timed out');
  req.destroy();
  process.exit(1);
});

req.end();
