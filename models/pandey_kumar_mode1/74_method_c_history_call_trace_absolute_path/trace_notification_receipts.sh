# Record only transport return codes and event names; never tokens or API bodies.
unset NOTIFICATION_MOCK_TELEGRAM NOTIFICATION_MOCK_FAIL
_definition="$(declare -f notification_send_telegram_once)"
eval "${_definition/notification_send_telegram_once/trace_original_telegram_once}"
_definition="$(declare -f notification_send_email_once)"
eval "${_definition/notification_send_email_once/trace_original_email_once}"
notification_send_telegram_once() {
 local event=UNKNOWN rc=0
 case "$1" in *STARTED*) event=STARTED;; *COMPLETED*) event=COMPLETED;; *FAILED*) event=FAILED;; *TERMINATED*) event=TERMINATED;; esac
 trace_original_telegram_once "$@" || rc=$?
 printf '%s TELEGRAM %s %s\n' "$PBS_JOBID" "$event" "$rc" >> "$RUN_DIR/notification_delivery.tsv"
 return "$rc"
}
notification_send_email_once() {
 local event=UNKNOWN rc=0
 case "$2" in *STARTED*) event=STARTED;; *COMPLETED*) event=COMPLETED;; *FAILED*) event=FAILED;; *TERMINATED*) event=TERMINATED;; esac
 if command -v sendmail >/dev/null 2>&1; then trace_original_email_once "$@" || rc=$?; else rc=127; fi
 printf '%s EMAIL %s %s\n' "$PBS_JOBID" "$event" "$rc" >> "$RUN_DIR/notification_delivery.tsv"
 return "$rc"
}
