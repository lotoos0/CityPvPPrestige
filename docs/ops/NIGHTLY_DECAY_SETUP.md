# Nightly Decay Setup (systemd)

This document explains how to install and run the nightly prestige soft-decay job.

## Prerequisites
- Backend deployed on the server
- Python venv available
- DB connection configured (same config as backend runtime)
- Server timezone set correctly (recommended: Europe/Warsaw)

## 1) Copy systemd units
From the repository:

- ops/systemd/prestige-decay.service
- ops/systemd/prestige-decay.timer

Copy them to:

/etc/systemd/system/prestige-decay.service
/etc/systemd/system/prestige-decay.timer

## 2) Edit paths
Update:
- WorkingDirectory
- ExecStart

to match your deployment paths.

## 3) Reload and enable
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now prestige-decay.timer
```

## 4) Verify

Check timer status:

```bash
systemctl list-timers --all | grep prestige-decay
systemctl status prestige-decay.timer
```

Run job manually once (safe due to idempotency):

```bash
sudo systemctl start prestige-decay.service
sudo systemctl status prestige-decay.service
journalctl -u prestige-decay.service --no-pager -n 200
```

## 5) Timezone sanity check

Verify server timezone:

```bash
timedatectl
```

Recommended:

Time zone: Europe/Warsaw

## Notes

- The job is idempotent via system_ticks (safe against double runs).
- Soft-decay constants are defined in docs/BALANCE_CONSTANTS.md and backend pvp_constants.py.
- If the service fails due to sandboxing, adjust unit settings instead of disabling hardening.
