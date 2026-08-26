#!/bin/sh
set -e

echo "[MONITORING] Starting Prometheus on port 9090..."
if [ -f /usr/local/bin/prometheus ]; then
  /usr/local/bin/prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/data/prometheus --web.listen-address="0.0.0.0:9090" &
fi

echo "[MONITORING] Starting Grafana on port 3000..."
exec /run.sh
