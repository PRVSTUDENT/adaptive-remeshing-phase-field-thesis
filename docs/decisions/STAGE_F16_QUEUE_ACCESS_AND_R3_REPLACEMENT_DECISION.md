# Stage F16 queue-access and R3 replacement decision

Installed PBS 2024.1.3 configuration proves `entry_imfdfkmq` is the required
user-accessible Route queue. It admits the user's general HPC group and routes
to `normal_imfdfkmq` and `short_imfdfkmq`. The normal destination is an
Execution queue with `from_route_only=True`, and its direct ACL excludes the
requesting user. Successful project records confirm submission through entry
and final execution through normal.

The prior classification `wave_b_submission_rejected_queue_access_denied` is
unchanged. Distinct R3 replacement packages correct scheduler-facing job
names, queue directives, paths, manifests, dependency construction, and
attempt accounting only. Scientific artifacts and Telegram implementation are
byte-identical. The R3 batch is `prepared_not_authorized`; a separate explicit
authorization is mandatory before any qsub.
