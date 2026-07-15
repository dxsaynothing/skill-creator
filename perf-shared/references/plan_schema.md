# performance-plan.yaml Schema (v1, JMeter runner)

## Purpose

`performance-plan.yaml` is the contract between:

- `jmeter-perf-plan-from-doc` (producer)
- `jmeter-scaffold-from-plan` (consumer: JMX + CLI)
- `jmeter-perf-result-analyzer` (context reader, optional)

This pack targets **`meta.runner: jmeter`**. Field names align with the Locust-oriented schema where possible; JMeter-specific execution lives under `run.jmeter`.

## Minimal Required Fields

```yaml
version: "1.0"
meta:
  plan_id: "jmeter-plan-20260511-order-service"
  runner: "jmeter"
  system: "order-service"
  owner: "qa-team"
  generated_at: "2026-05-11T10:00:00+08:00"
  env: "staging"
  base_url: "https://staging-api.example.com"

global:
  test_types: ["baseline", "stress", "soak"]
  default_headers:
    Content-Type: "application/json"
  auth:
    type: "bearer"
    token_env: "PERF_TOKEN"
  acceptance:
    default_error_rate_pct: 1.0
    default_p95_ms: 500

run:
  report_dir: "./reports"
  jmeter:
    non_gui: true
    jmx_path: "./plan.jmx"
    jtl_file: "./reports/results.jtl"
    html_report_dir: "./reports/html"
    properties_file: ""
    remote_hosts: ""
    log_file: "./reports/jmeter.log"
    jvm_heap: "2g"
    thread_group_defaults:
      ramp_time_sec: 60
      duration_sec: 600
      same_user_on_iteration: true

scenarios:
  - id: "create-order"
    name: "Create order"
    enabled: true
    priority: "P0"
    endpoint:
      method: "POST"
      path: "/api/orders"
    workload:
      model: "ramp"
      users: 100
      spawn_rate: 10
      duration: "10m"
    jmeter:
      sampler_name: "POST /api/orders"
      thread_group:
        num_threads: 100
        ramp_time_sec: 60
        duration_sec: 600
        scheduler: true
    sla:
      p95_ms: 300
      error_rate_pct: 0.5
      min_rps: 20
    checks:
      status_codes: [200, 201]
    data:
      source: "csv"
      file: "data.csv"
      variable_names: "username,password"
      recycle: true
      sharing_mode: "all"
    tags: ["order", "core"]
```

## Field Rules

- `version`: required string; current value is `1.0`.
- `meta.runner`: for this skill pack, must be `jmeter`.
- `meta.system`, `meta.env`, `meta.base_url`: required.
- `global.test_types`: at least one of `baseline|stress|soak|capacity`.
- `scenarios`: non-empty list.
- each scenario requires: `id`, `endpoint.method`, `endpoint.path`, `workload`.
- `run.jmeter`: optional; scaffold merges by priority **`CLI > run.jmeter > scenario.jmeter > derived from workload`**.
- `enabled=false` means scaffold should skip generation for that scenario.

## Workload → JMeter mapping (default)

| Plan field | JMeter mapping |
|------------|----------------|
| `workload.users` | `ThreadGroup.num_threads` (or `scenario.jmeter.thread_group.num_threads` if set) |
| `workload.spawn_rate` | approximate ramp: `ramp_time_sec = max(1, ceil(users / spawn_rate))` |
| `workload.duration` | `duration_sec` from suffix `s|m|h`; enable scheduler on thread group |
| `workload.model=constant` | ramp 0 or small fixed ramp per policy |
| `workload.model=step` | document use of Ultimate Thread Group / stepping thread group plugin (not in minimal JMX) |

If `scenario.jmeter.thread_group` is omitted, scaffold derives it from `workload` and `run.jmeter.thread_group_defaults`.

## Default/Fallback Strategy

When input docs are incomplete, use defaults and append risk notes in generated markdown:

- missing `auth`: set `type=none`.
- missing scenario SLA: inherit from `global.acceptance`.
- missing `spawn_rate`: use `max(1, users/10)` for ramp derivation.
- missing `duration`: baseline `5m`, stress `10m`, soak `60m`.
- missing status codes: default `[200]`.
- missing data source: use `inline` with placeholder.
- missing `run.jmeter.jmx_path`: default `./plan.jmx` under `runs/<plan_id>/` execution cwd.

## Validation Checklist

- no duplicated `scenarios[].id`.
- `endpoint.path` starts with `/`.
- `users > 0`, `spawn_rate > 0` when present.
- `p95_ms > 0`, `error_rate_pct >= 0`.
- `duration` uses suffix `s|m|h`.
- CSV scenarios: `data.file` non-empty when `source=csv`; `variable_names` aligns with CSV columns.
