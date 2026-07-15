---
name: jmeter-perf-result-analyzer
description: 读取 JMeter JTL/HTML 报告并归一化为 perf-results.json，对照 performance-plan.yaml 判定 SLA，输出 perf-analysis.md 与可选 next-run-patch.yaml。
---

# 性能结果分析（JMeter 结果 -> 结论）

## 概述

对 **JMeter** 压测结果做统一分析，产出可决策结论：

- Pass/Fail、未达标场景/标签、原因
- 下一轮线程/爬坡/时长/JVM 建议
- 瓶颈方向提示

归一化契约：**`../perf-shared/references/result_schema.md`**。

## 目录约定（`runs/<plan_id>/`）

- 输入：`data/performance-plan.yaml`、JTL（`run.jmeter.jtl_file` 或 `data/*.jtl`）、可选 `data/html/` 报告目录中的统计文件。
- 中间/输出：`ai/perf-results.json`（归一化）、`docs/perf-analysis.md`、可选 `ai/next-run-patch.yaml`。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 触发条件

适用于：

- 已有 JMeter **JTL** 或 **HTML dashboard** 产物。
- 需对照计划中的 SLA 做门禁判断。

不适用于：

- 无任何结果文件。
- 仅需生成 JMX（`jmeter-scaffold-from-plan`）。

## 输入

- 必选：JTL 和/或 HTML 报告产物。
- 建议：`runs/<plan_id>/data/performance-plan.yaml`。
- 输出/更新：`runs/<plan_id>/ai/perf-results.json`（`meta.tool: jmeter`，schema 见 perf-shared）。

## 输出

1. `docs/perf-analysis.md`：结论、达标情况、风险、建议动作（给人读）。
2. `ai/perf-results.json`：按 `result_schema` 填充 `overall`、`endpoints`（与 **sampler Label** 或 `scenario.jmeter.sampler_name` 对齐）、`summary`（给 AI 读）。
3. `ai/next-run-patch.yaml`（可选）：建议调整 `run.jmeter`、`workload` 或 `thread_group` 片段。

## 分析规则

1. **达标判定**：与通用分析器相同——endpoint 维度 `p95_ms`、`error_rate_pct`、`min_rps`；P0 整体错误率。
2. **瓶颈识别**：按 label 聚合 latency/error/rps TopN。
3. **风险分级**：`high|medium|low`（P0 失败为 high）。

## JTL 解析要点

- 按 **label** 聚合样本；将 `scenarios[].id` 与 label 映射（优先 plan 中 `jmeter.sampler_name`）。
- **百分位**：若 JTL 无直接百分位，从 HTML 报告 `statistics.json`（若存在）解析，或基于 `elapsed` 列表计算；缺失则 `null` 并 warning。
- **错误类型**：从响应码、断言失败信息归纳 `top_errors`。

## 工作流

1. 定位 JTL/HTML 路径。
2. 聚合为 `ai/perf-results.json`。
3. 合并 plan 中 SLA。
4. 生成 `docs/perf-analysis.md` 与 `ai/next-run-patch.yaml`（可选）。

## 与上下游衔接

- 上游：`jmeter-scaffold-from-plan`。
- 下游：`jmeter-perf-observability-correlator`；计划修订可回到 `jmeter-perf-plan-from-doc`。

## 下一步建议

- `jmeter-perf-observability-correlator`（需结合监控定位时）。

## 失败处理

- 字段缺失：部分分析并列出缺失项。
- 无法关联 `plan_id`：以结果为准，标注不可比对警告。
- 单位统一为 ms 与百分比后再判定。
