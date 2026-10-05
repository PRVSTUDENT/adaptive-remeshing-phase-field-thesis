#!/bin/bash
load_notification_config() {
    NOTIF_ENV="$HOME/.config/adaptive-remeshing/notifications.env"
    if [ -f "$NOTIF_ENV" ]; then
        source "$NOTIF_ENV"
    fi
}

notify_start() {
    JOB_ID="$1"
    CANDIDATE="$2"
    HOST="$3"
    QUEUE="$4"
    WALLTIME="$5"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        MSG="🚀 *HPC Job Started*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Host:* $HOST%0A*Queue:* $QUEUE%0A*Walltime:* $WALLTIME"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}

notify_completed() {
    JOB_ID="$1"
    CANDIDATE="$2"
    EXIT_CODE="$3"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        STATUS="✅ COMPLETED"
        if [ "$EXIT_CODE" -ne 0 ]; then
            STATUS="❌ FAILED (RC=$EXIT_CODE)"
        fi
        MSG="🏁 *HPC Job Execution Finished*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Result:* $STATUS"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}

notification_install_terminal_trap() {
    JOB_ID="$1"
    CANDIDATE="$2"
    trap 'notify_completed "$JOB_ID" "$CANDIDATE" "$?"' EXIT SIGINT SIGTERM
}

notify_submitted() {
    JOB_ID="$1"
    CANDIDATE="$2"
    QUEUE="$3"
    CPUS="$4"
    MEM="$5"
    WALLTIME="$6"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        MSG="📥 *HPC Job Submitted*%0A*Job ID:* \`$JOB_ID\`%0A*Candidate:* \`$CANDIDATE\`%0A*Queue:* $QUEUE%0A*Resources:* ${CPUS} CPU, ${MEM}, ${WALLTIME}"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d "chat_id=${TELEGRAM_CHAT_ID}" -d "text=${MSG}" -d "parse_mode=Markdown" >/dev/null || true
    fi
}
