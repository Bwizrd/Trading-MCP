#!/bin/bash

export INFLUXDB_TOKEN="VNC3xnPXodbpC3yJ_riWrBpN0lCA0k-mPiFsocR-Wu9K8kFHQ3JUp32bOCQaNOdjVI6zfGuxoZpgGZl-ZiXP-Q=="
export INFLUXDB_URL="http://localhost:8086"
export INFLUXDB_ORG="PansHouse"
export INFLUXDB_DATABASE="market_data"

echo "Testing influxdb-mcp-server connection..."
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | npx influxdb-mcp-server
