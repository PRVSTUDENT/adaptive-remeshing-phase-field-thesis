# F15 Telegram compatibility repair

- Curl: 7.61.1; portable options verified
- `getMe`: pass
- `getChat`: pass; configured chat matched
- Visible Telegram send: fail after three bounded attempts
- Redacted Telegram result: HTTP 400, message text empty
- Direct email: not resent; prior human receipt remains false
- PBS qsub attempts: 0
- Authorization activation: none
- Raw Telegram response files: deleted by trap
- Secrets exposed or committed: none
- Result: `telegram_send_message_text_empty`
