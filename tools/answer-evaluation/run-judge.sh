#!/bin/bash
# Host exception: simple orchestration only; all JSON and evaluation logic runs in Docker.
set -euo pipefail
if [ "${1:-}" != "--provisional" ]; then
  echo 'Requires --provisional; human calibration has not passed.' >&2
  exit 2
fi
task_root="$(cd "$(dirname "$0")/../.." && pwd)"
task_jobs="$task_root/results/submission/P03-S08-v1/judge-v1"
test "$(codex --version)" = 'codex-cli 0.167.1'
codex login status 2>&1 | rg -q '^Logged in using ChatGPT$'
task_started=$(date +%s)
for task_directory in "$task_jobs"/[0-9][0-9][0-9]; do
  task_job=$(basename "$task_directory")
  if [ -e "$task_directory/started.txt" ]; then
    echo "Existing attempt $task_job; stop without automatic retry or resume." >&2
    exit 3
  fi
  if [ $(( $(date +%s) - task_started )) -ge 7200 ]; then
    echo 'Phase deadline reached.' >&2
    exit 3
  fi
  /bin/bash "$task_root/tools/answer-evaluation/quota.sh" > "$task_directory/quota.jsonl" 2> "$task_directory/quota.stderr"
  make -C "$task_root" answer-judge-admit JOB="$task_job"
  task_work=$(mktemp -d /private/tmp/rd-ai-s08-judge.XXXXXX)
  cp "$task_directory/instructions.txt" "$task_directory/schema.json" "$task_work/"
  date -u +%FT%TZ > "$task_directory/started.txt"
  env -u OPENAI_API_KEY -u CODEX_API_KEY -u OPENAI_BASE_URL \
    codex exec --ignore-user-config --ignore-rules --strict-config \
    --skip-git-repo-check --ephemeral --sandbox read-only --model gpt-6.1-sol \
    -C "$task_work" --json --output-schema "$task_work/schema.json" \
    -o "$task_directory/verdict.json" \
    -c 'forced_login_method="chatgpt"' -c 'model_reasoning_effort="medium"' \
    -c "model_instructions_file=\"$task_work/instructions.txt\"" \
    -c 'project_doc_max_bytes=0' -c 'web_search="disabled"' \
    -c 'skills.bundled.enabled=false' -c 'skills.include_instructions=false' \
    --disable shell_tool --disable unified_exec --disable apps --disable plugins \
    --disable browser_use --disable browser_use_external --disable in_app_browser \
    --disable computer_use --disable multi_agent --disable multi_agent_v2 \
    --disable hooks --disable view_image --disable skill_search \
    --disable sleep_tool --disable workspace_dependencies --disable remote_plugin \
    --disable plugin_discovery_prefetch --disable unbounded_connection_retries \
    --enable skip_host_skill_discovery \
    - < "$task_directory/bundle.json" > "$task_directory/events.jsonl" 2> "$task_directory/stderr.txt" &
  task_pid=$!
  (sleep 180; kill -TERM "$task_pid" 2>/dev/null || true; sleep 3; kill -KILL "$task_pid" 2>/dev/null || true) &
  task_watchdog=$!
  task_code=0
  wait "$task_pid" || task_code=$?
  kill "$task_watchdog" 2>/dev/null || true
  printf '%s\n' "$task_code" > "$task_directory/exit-code.txt"
  date -u +%FT%TZ > "$task_directory/finished.txt"
  make -C "$task_root" answer-judge-check JOB="$task_job"
done
make -C "$task_root" answer-judge-summary
