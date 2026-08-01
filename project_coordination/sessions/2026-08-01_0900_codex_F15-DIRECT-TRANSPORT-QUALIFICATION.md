# F15 direct transport qualification session

- Starting commit: `86d54a17c4a71bd2ac07b46e9b36393862df6439`
- Configuration: present, owner matched, mode 600, mandatory values nonempty
- Selected email transport: `sendmail`
- Offline tests: 8 passed under cluster Python 3.6
- Direct email: technical pass, one attempt, no duplicate sent
- Direct Telegram: failed, three bounded attempts, curl return code 2
- Telegram cause: installed curl lacks `--fail-with-body`; no HTTP request
  completed and no Telegram message ID exists
- PBS qsub attempts: 0
- Successful PBS submissions: 0
- Authorization activation: none
- Scientific execution: none
- Secrets exposed or committed: none
- Result: `telegram_direct_transport_client_incompatible`

Redacted evidence is under
`runs/hpc/stage_f/f15_dual_channel_notification_qualification/direct_test_evidence/`.
