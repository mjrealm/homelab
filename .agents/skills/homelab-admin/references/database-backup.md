# Databases and backups

Read this when an app needs a PostgreSQL database, when you add or change a database backup, or when you remove an app that has one. The R2 budget and the default schedule are in `AGENTS.md` ("R2 storage budget"); this file is the procedure.

## Which database setup to use

1. **CloudNativePG (CNPG) with the Barman plugin.** The default for new databases. It gives base backups plus continuous WAL archiving to R2, so you can restore to a point in time. The operator is `k8s/platform/cnpg`. Copy `k8s/apps/sure/templates/postgres.yaml` as the pattern for a plain database. `k8s/apps/immich/templates/postgres.yaml` adds Postgres extensions and a `Database` resource on top of it.
2. **A plain `postgres` StatefulSet in the app chart.** The older pattern. Its only protection is the Velero volume snapshot, which is crash-consistent and has no point-in-time restore. Don't use it for a new app. When you touch an app that still has one, tell the user it's a migration candidate.
3. **Databasus** (`k8s/apps/databasus`) can take scheduled logical dumps (`pg_dump`) of a plain Postgres, to a NAS or S3. It's configured in its web UI, not in the repo. Mention it as a second safety net, not a replacement for CNPG.

Redis and other caches are not backed up.

## Add a CNPG database with a backup

1. Create `templates/postgres.yaml` with three resources, named after the app:
   - `Cluster` `<app>-database`, with `plugins: [{name: barman-cloud.cloudnative-pg.io, isWALArchiver: true, parameters: {barmanObjectName: <app>-r2, serverName: <app>-database}}]`.
   - `ObjectStore` `<app>-r2`, with `destinationPath: s3://{{ .Values.backup.r2.bucket }}/<app>`, the R2 `endpointURL`, credentials from the `<app>-secrets` Secret (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`), gzip compression, and the three R2 environment variables (`AWS_DEFAULT_REGION=auto`, and the two checksum settings set to `when_required`) under `instanceSidecarConfiguration`. R2 has no regions and rejects the newer default S3 checksums.
   - `ScheduledBackup` `<app>-daily` with `method: plugin` and `backupOwnerReference: self`.
2. Add the `backup.r2` block to `values.yaml` at the top level (outside the dependency key):

   ```yaml
   backup:
     r2:
       bucket: homelab-db-backups
       endpointURL: <copy from k8s/apps/sure/values.yaml>
       retention: 3d
       schedule: "0 0 <hour> * * 0"  # UTC, Sundays. Run: make check-backups
   ```

3. Add `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` to the app's `InfisicalSecret` folder, and list them in the PR (project, path, key names). The keys must exist before the merge.
4. Point the app at `<app>-database-rw`, and take the credentials from the `<app>-database-app` Secret that CNPG creates.

## Choose the schedule and retention

- Default: a weekly base backup (Sunday) with `retention: 3d`. Use daily or a longer retention only for a small database whose data matters, and say why in the PR.
- Base backups are full copies. Barman keeps the newest base backup older than the retention window, so a database holds about `base size × (retention ÷ interval + 2)` copies at worst, plus WAL.
- Schedule rules, checked by `make check-backups`: every database base backup starts at least 60 minutes from every Velero run and 60 minutes from every other database backup, between 01:00 and 05:00 UTC. The six-field cron is `seconds minutes hours day month weekday` in UTC. Pick a free hour from the output of `make check-backups`.
- Run `make check-backups` through the project's `.venv` (`.venv/bin/python scripts/check-backup-windows.py`) if `make` picks the wrong Python. It must end with `ok:`.

## R2 budget check (every PR that adds or changes R2 usage)

1. Read the current bucket and folder sizes from the R2 dashboard. Don't estimate from memory. If you can't, say so in the PR and don't raise usage.
2. Estimate the new database's size with the formula above and add it to the total.
3. Put the old total, the new total and the 10 GB limit in the PR description. Above 8 GB, lower the frequency or retention first and ask the user.

## Keep the docs and diagrams in step

A change to a schedule, a retention, or the set of databases with a backup also changes:

- `docs/recover/03-backup-schedule.md`: the schedule table and, if you moved the window, the rule text.
- `docs/recover/02-what-is-backed-up.md`: the copies table.
- `docs/recover/img/backup-schedule.svg` (one row per database, the window label, the description) and `docs/recover/img/backups.svg` (the Barman and R2 boxes).

After you edit an SVG, check it with `xmllint --noout`, render it (for example with `qlmanage -t -s 1400 -o <dir> <file>` on macOS) and look for clipped labels. Don't state counts or versions that change as the cluster changes.

## Verify after the merge

Read-only, with context `k3s-ansible`:

```bash
kubectl get cluster.postgresql.cnpg.io -n <app>
kubectl get backups.postgresql.cnpg.io -n <app>
kubectl get cluster <app>-database -n <app> -o jsonpath='{.status.firstRecoverabilityPoint}'
```

Expect the cluster `Ready`, and a timestamp from the last command once the first base backup has finished. An empty value means no base backup has completed yet.

To take one now, apply a `Backup` resource (`method: plugin`, `pluginConfiguration.name: barman-cloud.cloudnative-pg.io`) in the app's namespace. This changes the cluster outside Git, so do it only when the user asks. It's a one-off object that Argo CD doesn't manage. Don't commit it. A base backup runs while Postgres stays up.

## Migrate a plain Postgres to CNPG

Two PRs, one app at a time:

1. Add the CNPG cluster and backup, import the data with `bootstrap.initdb.import` (or dump and restore), and point the app at the new service. The app must be stopped during the import.
2. After the user has checked the new database, remove the old `postgres` controller and its PVC. Removing the PVC deletes the old data, so wait for the user's go-ahead.

Pick the Postgres major version on purpose. The import allows an upgrade.

## Remove an app that has a CNPG backup

Removing the directory deletes the cluster and its PVCs. The backup data stays in R2 and keeps counting against the budget. Tell the user to delete the app's folder in `homelab-db-backups` (R2 dashboard) once they no longer need the backup, and update the docs and diagrams above.
