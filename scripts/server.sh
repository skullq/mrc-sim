#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SCRIPT="$ROOT_DIR/scripts/web_dashboard.py"
PID_FILE="/tmp/mrc_dashboard.pid"
LOG_FILE="/tmp/mrc_dashboard.log"
PORT="${2:-${MRC_PORT:-8787}}"
HOST="${MRC_HOST:-0.0.0.0}"

get_pids() {
  pgrep -f "python3 .*web_dashboard\.py" || true
}

is_running() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "$pid"
      return 0
    fi
  fi
  local found
  found="$(get_pids | head -n 1 || true)"
  if [[ -n "$found" ]]; then
    echo "$found"
    return 0
  fi
  return 1
}

cmd_start() {
  local pid
  if pid="$(is_running)"; then
    echo "[MRC-SIM] 이미 실행 중입니다 (PID=$pid, PORT=$PORT)"
    cmd_status
    return 0
  fi

  nohup python3 "$APP_SCRIPT" --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 </dev/null &
  local new_pid=$!
  echo "$new_pid" >"$PID_FILE"

  for _ in $(seq 1 20); do
    if curl -s -o /dev/null "http://127.0.0.1:${PORT}/" 2>/dev/null; then
      echo "[MRC-SIM] 서버 시작 완료 (PID=$new_pid)"
      cmd_status
      return 0
    fi
    sleep 0.25
  done

  echo "[MRC-SIM] 서버 시작 확인 실패. 로그: $LOG_FILE"
  tail -n 20 "$LOG_FILE" || true
  return 1
}

cmd_stop() {
  local pids
  pids="$(get_pids)"
  if [[ -z "$pids" ]] && [[ ! -f "$PID_FILE" ]]; then
    echo "[MRC-SIM] 실행 중인 서버가 없습니다."
    return 0
  fi

  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi

  for p in $pids; do
    kill "$p" 2>/dev/null || true
  done
  sleep 0.5
  for p in $(get_pids); do
    kill -9 "$p" 2>/dev/null || true
  done

  echo "[MRC-SIM] 서버가 중지되었습니다."
}

cmd_status() {
  local pid
  if pid="$(is_running)"; then
    local code ip
    code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/" 2>/dev/null || echo "000")"
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    echo "[MRC-SIM] 상태: RUNNING (PID=$pid)"
    echo "  • 로컬 URL : http://127.0.0.1:${PORT}/ (HTTP $code)"
    if [[ -n "$ip" ]]; then
      echo "  • 서버 IP  : http://${ip}:${PORT}/"
    fi
    echo "  • 로그 파일: $LOG_FILE"
  else
    echo "[MRC-SIM] 상태: STOPPED"
  fi
}

cmd_logs() {
  if [[ -f "$LOG_FILE" ]]; then
    tail -n "${1:-40}" "$LOG_FILE"
  else
    echo "[MRC-SIM] 로그 파일이 없습니다: $LOG_FILE"
  fi
}

case "${1:-status}" in
  start)
    cmd_start
    ;;
  stop)
    cmd_stop
    ;;
  restart)
    cmd_stop
    cmd_start
    ;;
  status)
    cmd_status
    ;;
  logs)
    cmd_logs "${2:-40}"
    ;;
  *)
    echo "사용법: $0 {start|stop|restart|status|logs} [port]"
    exit 1
    ;;
esac
