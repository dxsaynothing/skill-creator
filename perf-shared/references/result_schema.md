# perf-results.json Schema (v1, JMeter)

## Purpose

`perf-results.json` is the normalized result contract consumed by `jmeter-perf-result-analyzer`. It may be produced from:

- JMeter **JTL** (XML or CSV) aggregated by label / transaction
- JMeter **HTML dashboard** summary (if JTL lacks percentiles)
- Third-party exporters (InfluxDB / Prometheus) if mapped into the same shape

## Minimal Required Fields

```json
{
  "version": "1.0",
  "meta": {
    "plan_id": "jmeter-plan-20260511-order-service",
    "system": "order-service",
    "env": "staging",
    "tool": "jmeter",
    "jtl_path": "./reports/results.jtl",
    "generated_at": "2026-05-11T11:00:00+08:00",
    "duration_sec": 600
  },
  "overall": {
    "requests": 120000,
    "failures": 300,
    "error_rate_pct": 0.25,
    "rps": 200.0,
    "latency_ms": {
      "p50": 80,
      "p90": 180,
      "p95": 240,
      "p99": 520
    }
  },
  "endpoints": [
    {
      "id": "create-order",
      "name": "POST /api/orders",
      "label": "POST /api/orders",
      "requests": 50000,
      "failures": 200,
      "error_rate_pct": 0.4,
      "rps": 90.0,
      "latency_ms": {
        "p50": 100,
        "p90": 220,
        "p95": 320,
        "p99": 680
      },
      "sla": {
        "p95_ms": 300,
        "error_rate_pct": 0.5,
        "min_rps": 80
      },
      "pass": false,
      "top_errors": [
        { "type": "HTTP_500", "count": 120 },
        { "type": "TIMEOUT", "count": 80 }
      ]
    }
  ],
  "summary": {
    "pass": false,
    "failed_endpoint_count": 1,
    "risk_level": "medium"
  }
}
```

## Field Rules

- `overall.error_rate_pct = failures / requests * 100` (when requests > 0).
- `endpoints[].pass` is true only when all configured SLA checks pass.
- `summary.risk_level` enum: `low|medium|high`.
- `meta.plan_id` should match `performance-plan.yaml.meta.plan_id`.
- `meta.tool` should be `jmeter` for this pack.
- `endpoints[].label`: optional; JMeter sampler **Label** used when aggregating JTL (fallback to `name`).

## JTL → normalized mapping (guidance)

- Aggregate samples by **label** (or transaction controller name) and map to `endpoints[]`:
  - match `endpoints[].id` to plan `scenarios[].id` via `scenario.jmeter.sampler_name` or label naming convention.
- Latency percentiles: prefer JTL with `elapsed` and use configured percentile calculation, or read from HTML report `statistics.json` if present.
- If `p99` missing in source, keep as `null`, do not fabricate.
- Throughput (`rps`): derived from sample count / measured window for that label.

## Default/Fallback Strategy

- if endpoint SLA missing in input result, pull from plan by `id`.
- if `p99` missing, keep as `null`.
- if top errors missing, use empty list and mark warning.
- if endpoint not found in plan, keep it with tag `unmapped=true`.

## Analyzer Output Recommendations

Analyzer should generate:

- final verdict: pass/fail with reason.
- top bottlenecks (latency/errors/throughput).
- next-run actions:
  - thread/ramp/duration tuning
  - JVM heap / properties tuning
  - data prep action
  - environment dependency checks
