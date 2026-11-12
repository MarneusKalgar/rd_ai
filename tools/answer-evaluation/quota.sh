#!/bin/bash
# Supported account metadata only: no thread/start, turn/start or model generation.
set -euo pipefail
{
  printf '%s\n' '{"id":0,"method":"initialize","params":{"clientInfo":{"name":"rd_ai_s08_metadata","version":"1"}}}'
  sleep 1
  printf '%s\n' '{"method":"initialized","params":{}}' '{"id":1,"method":"account/rateLimits/read"}'
  sleep 5
} | codex app-server --stdio -c 'features.apps=false' -c 'features.plugins=false' -c 'web_search="disabled"'
