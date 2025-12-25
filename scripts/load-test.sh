#!/bin/bash
set -e

API_URL=${1:-http://localhost:8000}
CONCURRENT_USERS=${2:-10}
DURATION=${3:-60}

echo "🔥 Running load test..."
echo "API: $API_URL"
echo "Users: $CONCURRENT_USERS"
echo "Duration: ${DURATION}s"

# Install k6 if not present
if ! command -v k6 &> /dev/null; then
    echo "Installing k6..."
    curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1
    sudo mv k6 /usr/local/bin/
fi

# Create load test script
cat > /tmp/load-test.js << 'LOADTEST'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: __ENV.USERS },
    { duration: __ENV.DURATION + 's', target: __ENV.USERS },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function() {
  let response = http.get(__ENV.API_URL + '/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
LOADTEST

# Run load test
k6 run \
  -e API_URL=$API_URL \
  -e USERS=$CONCURRENT_USERS \
  -e DURATION=$DURATION \
  /tmp/load-test.js

echo "✅ Load test completed!"
