#!/bin/bash
set -e

HAPROXY_STATIC_TOP='
global
	log /dev/log local0
	log /dev/log local1 notice
	chroot /var/lib/haproxy
	stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
	stats timeout 30s
	user haproxy
	group haproxy

	# SSL Configuration (TLS 1.2 and 1.3)
	ca-base /etc/ssl/certs
	crt-base /etc/ssl/private
	ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
	ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
	ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
	option dontlognull
	timeout connect 5s
	timeout client 10m
	timeout server 10m
	errorfile 400 /usr/local/etc/haproxy/errors/400.http
	errorfile 403 /usr/local/etc/haproxy/errors/403.http
	errorfile 408 /usr/local/etc/haproxy/errors/408.http
	errorfile 500 /usr/local/etc/haproxy/errors/500.http
	errorfile 502 /usr/local/etc/haproxy/errors/502.http
	errorfile 503 /usr/local/etc/haproxy/errors/503.http
	errorfile 504 /usr/local/etc/haproxy/errors/504.http
'

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 '<json_config_obj>'" >&2
  exit 1
fi

if ! echo "$1" | jq -e . >/dev/null 2>&1; then
  echo "ERROR: argument must be a valid JSON object" >&2
  exit 1
fi

# Generate initial haproxy.cfg with static top only
HAPROXY_CFG="/usr/local/etc/haproxy/haproxy.cfg"
HAPROXY_CFG_TMP="haproxy.cfg.tmp"
printf "%s
" "$HAPROXY_STATIC_TOP" > "$HAPROXY_CFG_TMP"

# --- listen console (HTTP admin) ---
cat >> "$HAPROXY_CFG_TMP" <<'EOF'

listen console
	bind :8080
	mode tcp
	balance roundrobin
EOF

# primary region (console)
jq -r '
  .primary as $p |
  $p.nodes[] |
  "	server roach-\($p.region)-\(.) tasks.roach-\($p.region)-\(.):8080 check inter 3s fall 3 rise 2"
' <<< "$1" >> "$HAPROXY_CFG_TMP"

# backup regions (console)
jq -r '
  .backup[] as $b |
  $b.nodes[] |
  "	server roach-\($b.region)-\(.) tasks.roach-\($b.region)-\(.):8080 check inter 3s fall 3 rise 2 backup"
' <<< "$1" >> "$HAPROXY_CFG_TMP"

# --- listen roachcluster (CockroachDB SQL) ---
cat >> "$HAPROXY_CFG_TMP" <<'EOF'

listen roachcluster
	bind :26257
	mode tcp
	option redispatch
	balance roundrobin
EOF

# primary region (roachcluster)
jq -r '
  .primary as $p |
  $p.nodes[] |
  "	server roach-\($p.region)-\(.) tasks.roach-\($p.region)-\(.):26257 check inter 3s fall 3 rise 2"
' <<< "$1" >> "$HAPROXY_CFG_TMP"

# backup regions (roachcluster)
jq -r '
  .backup[] as $b |
  $b.nodes[] |
  "	server roach-\($b.region)-\(.) tasks.roach-\($b.region)-\(.):26257 check inter 3s fall 3 rise 2 backup"
' <<< "$1" >> "$HAPROXY_CFG_TMP"

exit 0

mv "$HAPROXY_CFG_TMP" "$HAPROXY_CFG"

echo "🕓 Waiting for CockroachDB node DNS entries..."

for name in "$@"; do
  fqdn="tasks.$name"
  until getent hosts "$fqdn" > /dev/null 2>&1; do
    echo "  ⏳ $fqdn not ready..."
    sleep 1
  done

done

echo "✅ All node hostnames resolved. Launching HAProxy..."
exec haproxy -f "$HAPROXY_CFG"
