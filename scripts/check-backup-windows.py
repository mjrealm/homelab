#!/usr/bin/env python3
"""Fail when a database base backup could overlap Velero's Longhorn CSI snapshots.

Velero (k8s/system/velero/values.yaml) takes the Longhorn CSI snapshots, in the
timezone Velero runs in (daylight saving moves it by an hour in UTC). CloudNativePG
base backups (`backup.schedule` or `backup.r2.schedule` in any values.yaml) run in UTC.
A database backup must stay at least GAP_MIN minutes away from every Velero run, in
winter and in summer, and database backups must not overlap each other.

Only the time of day is compared (the day of the week is ignored), which is the safe
side. Longhorn recurring jobs are set in the Longhorn UI, not in Git, so they are not
checked here.

Usage: scripts/check-backup-windows.py [--extra "<six-field cron>"]...
"""
import argparse
import datetime as dt
import glob
import sys
from zoneinfo import ZoneInfo

import yaml

VELERO_VALUES = "k8s/system/velero/values.yaml"
VELERO_RUN_MIN = 30  # the longest observed Velero run is about 15 minutes
DB_RUN_MIN = 30  # base backups of these databases take seconds to minutes
GAP_MIN = 60  # between a database backup and a Velero run
DB_GAP_MIN = 30  # between two database backups
DAY = 1440


def hm(expr, six):
    f = expr.split()
    minute, hour = f[1 if six else 0], f[2 if six else 1]
    if not (minute.isdigit() and hour.isdigit()):
        sys.exit(f"cannot check '{expr}': use a fixed minute and hour")
    return int(hour) * 60 + int(minute)


def gap(a, da, b, db):
    """Minutes between two runs [a, a+da] and [b, b+db] on a 24 hour circle."""
    if (b - a) % DAY < da or (a - b) % DAY < db:
        return 0
    return min((b - (a + da)) % DAY, (a - (b + db)) % DAY)


def utc_minutes(local_minutes, tz, month):
    day = dt.datetime(2026, month, 15, local_minutes // 60, local_minutes % 60, tzinfo=ZoneInfo(tz))
    u = day.astimezone(dt.timezone.utc)
    return u.hour * 60 + u.minute


def fmt(m):
    return f"{m % DAY // 60:02d}:{m % DAY % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", action="append", default=[], help="extra six-field UTC cron to check")
    args = ap.parse_args()

    v = yaml.safe_load(open(VELERO_VALUES))["velero"]
    tz = next((e["value"] for e in v["configuration"].get("extraEnvVars", []) if e["name"] == "TZ"), "UTC")
    velero = []  # (name, winter utc minute, summer utc minute)
    for name, s in v["schedules"].items():
        local = hm(s["schedule"], False)
        velero.append((name, utc_minutes(local, tz, 1), utc_minutes(local, tz, 7)))

    dbs = []  # (name, utc minute)
    for path in sorted(glob.glob("k8s/**/values.yaml", recursive=True)):
        data = yaml.safe_load(open(path)) or {}
        b = data.get("backup")
        if not isinstance(b, dict):
            continue
        sched = b.get("schedule") or (b.get("r2") or {}).get("schedule")
        if sched:
            dbs.append((path.split("/")[-2], hm(sched, True)))
    dbs += [(f"extra{i}", hm(e, True)) for i, e in enumerate(args.extra)]

    bad = []
    print(f"Velero runs in {tz}; times below are UTC (winter / summer):")
    for name, w, s in velero:
        print(f"  {name:28s} {fmt(w)} / {fmt(s)}  (each run up to {VELERO_RUN_MIN} min)")
    print("Database base backups (UTC):")
    for name, m in dbs:
        print(f"  {name:28s} {fmt(m)}")
        for vname, w, s in velero:
            for label, vm in (("winter", w), ("summer", s)):
                g = gap(m, DB_RUN_MIN, vm, VELERO_RUN_MIN)
                if g < GAP_MIN:
                    bad.append(f"{name} ({fmt(m)} UTC) is {g} min from {vname} in {label} ({fmt(vm)} UTC); need {GAP_MIN}")
    for i, (n1, m1) in enumerate(dbs):
        for n2, m2 in dbs[i + 1:]:
            g = gap(m1, DB_RUN_MIN, m2, DB_RUN_MIN)
            if g < DB_GAP_MIN:
                bad.append(f"{n1} ({fmt(m1)} UTC) and {n2} ({fmt(m2)} UTC) are {g} min apart; need {DB_GAP_MIN}")
    if bad:
        print("\nFAIL:")
        for b in bad:
            print("  " + b)
        sys.exit(1)
    print(f"\nok: every database backup is at least {GAP_MIN} min from Velero's snapshots, and {DB_GAP_MIN} min from each other")


if __name__ == "__main__":
    main()
