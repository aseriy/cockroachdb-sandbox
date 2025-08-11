#!/bin/bash
set -e

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 roach0 roach1 roach2 ..."
  exit 1
fi

echo "🕓 Waiting for CockroachDB node DNS entries..."

for name in "$@"; do
  fqdn="tasks.$name"
  until getent hosts "$fqdn" > /dev/null 2>&1; do
    echo "  ⏳ $fqdn not ready..."
    sleep 1
  done

done

echo "✅ All node hostnames resolved. Launching HAProxy..."
exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg
