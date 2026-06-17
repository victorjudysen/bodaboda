# BodaBoda Digital — CMMI Maturity Assessment
## CS 421 Assignment 4 — Task 5

---

## CMMI Maturity Levels Reference

| Level | Name | Characteristics |
|-------|------|----------------|
| 1 | Initial | Ad hoc, unpredictable builds; success depends on individual heroics |
| 2 | Managed | Repeatable pipeline; planned, tracked deployments |
| 3 | Defined | Standardized, documented automation across the project |
| 4 | Quantitatively Managed | Metrics collected and used to control the process |
| 5 | Optimizing | Continuous improvement; process changes data-driven |

---

## Current Assessment: **Level 3 — Defined**

### Evidence Table

| CMMI Area | Level 1 | Level 2 | Level 3 ✅ | Level 4 | Level 5 |
|-----------|---------|---------|------------|---------|---------|
| **Build process** | ❌ Ad hoc | ✅ Repeatable | ✅ Defined in `ci.yml` | — | — |
| **Testing** | ❌ Manual | ✅ Automated pytest | ✅ Coverage tracked (`pytest-cov`) | ⚠️ Trend not yet tracked over time | — |
| **Deployment** | ❌ Manual | ✅ Triggered on push | ✅ Staging → Approval → Production | — | — |
| **Versioning** | ❌ None | ✅ SHA tags | ✅ Semantic tags `v<run>` + `latest` | — | — |
| **Rollback** | ❌ None | ❌ None | ✅ Rollback workflow (`rollback.yml`) | — | — |
| **Monitoring** | ❌ None | ✅ Prometheus scraping | ✅ Grafana dashboards provisioned | ⚠️ Alerting not configured | — |
| **Notifications** | ❌ None | ⚠️ GitHub default emails | ✅ Slack webhook + GitHub annotations | — | — |
| **External hosting** | ❌ Local only | ✅ Docker Hub | ✅ Render.com live URL | — | — |
| **MQTT integration** | ❌ None | ✅ Local broker | ✅ CI smoke test validates pub/sub | — | — |
| **Documentation** | ❌ None | ⚠️ Partial README | ✅ Process docs + this assessment | — | — |

---

## Detailed Justification for Level 3

### What qualifies us as Level 3 (Defined):

1. **Standardised CI pipeline** — every code push triggers the exact same sequence:
   `checkout → install → test+coverage → build docker → MQTT smoke test`
   This is codified in `.github/workflows/ci.yml` and is not person-dependent.

2. **Defined deployment process** — the CD pipeline enforces:
   - Staging deploy + health verification
   - Manual approval gate before production
   - Semantic version tagging (`v<run_number>`)
   - Rollback procedure documented and automated

3. **Test coverage measurement** — `pytest-cov` generates XML and HTML reports
   on every CI run; coverage threshold (60%) is enforced at the pipeline level.

4. **Process documentation** — CMMI requires that processes are not just practised
   but *written down*. This file, the workflow YAMLs, and the README constitute
   that documentation.

5. **Automated rollback** — a defined, repeatable procedure exists to revert
   production to any prior image tag without manual Docker commands.

### Why we are NOT yet Level 4:

Level 4 requires *quantitative management* — collecting metrics over time and
using statistical techniques to control process performance. Currently:
- We collect Prometheus metrics but have no alert thresholds configured.
- Build duration is logged per run but not trended or compared to baselines.
- Test pass rate (100%) is visible per run but not tracked across weeks.
- No SLO (Service Level Objective) has been formally defined and enforced.

---

## Improvement Plan: Level 3 → Level 4

| Action | Implementation | Expected Impact |
|--------|---------------|-----------------|
| **Configure Grafana alerting** | Set threshold alerts on `up{job="bodaboda-backend"}` and login failure rate | Automated downtime detection |
| **Track build duration over time** | Write duration to a Prometheus pushgateway or parse GitHub API | Baseline + trend analysis |
| **Define SLOs** | Document: test pass rate ≥ 95%, deploy time < 5 min, uptime ≥ 99% | Formal quality targets |
| **Weekly metrics review** | Schedule a Monday review of the Grafana dashboard | Data-driven retrospectives |
| **Coverage trend** | Store `coverage.xml` results in a time-series; alert if coverage drops | Quantified quality gate |

---

## Process Improvement Summary (Assignment 4 — Task 4)

### Improvement #1: Test Coverage Reports
- **Before:** Tests ran but no coverage data was collected or enforced.
- **After:** `pytest-cov` generates XML + HTML coverage reports on every CI run.
  A minimum 60% coverage threshold blocks merges if coverage drops.
- **Impact:** Developers know exactly which backend code paths are untested.
  Coverage report artifact is downloadable from every GitHub Actions run.

### Improvement #2: Failure Notifications
- **Before:** Failures produced only the default GitHub email (often missed).
- **After:** Pipeline failures post a structured message to Slack (configurable
  via `SLACK_WEBHOOK_URL` secret) with commit SHA, branch, and a direct link
  to the failed run. Success in production also sends a confirmation message.
- **Impact:** Team is notified within seconds of a failure; no manual checking
  of the Actions dashboard required.

### Improvement #3: Rollback Mechanism
- **Before:** A broken production deployment required manually running Docker
  commands to pull an older image — error-prone and undocumented.
- **After:** A `workflow_dispatch` workflow (`rollback.yml`) accepts a target
  image tag, verifies the image exists on Docker Hub, re-tags it as `latest`,
  runs a health check, and notifies the team. Requires Release Manager approval.
- **Impact:** Mean Time to Recovery (MTTR) reduced from ~10 minutes (manual)
  to < 2 minutes (automated). Full audit trail in GitHub Actions history.

---

## Root Cause Analysis (5 Whys — Slow Deployments)

**Symptom:** Staging deploy step takes 45–90 seconds per build.

| Why # | Question | Answer |
|-------|----------|--------|
| 1 | Why is deployment slow? | Docker image rebuild from scratch on every CI run |
| 2 | Why does it rebuild from scratch? | No Docker layer caching configured in GitHub Actions |
| 3 | Why is caching not configured? | `docker/build-push-action` caching not set in `ci.yml` |
| 4 | Why was caching not set up initially? | Assignment focused on correctness, not performance |
| 5 | Why does this matter now? | Frequent commits make slow pipelines a bottleneck |

**Corrective action (next sprint):** Add `cache-from` / `cache-to` with `type=gha`
to the `docker/build-push-action` steps to cut build time by ~50%.

---

*Document prepared for CS 421 Assignment 4 — Process Improvement Using Tools*
*Date: June 2026*
