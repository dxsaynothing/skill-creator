---
name: jmeter-perf-observability-correlator
description: 将 JMeter 压测归一化结果与监控指标时间关联，输出瓶颈证据链与优先级建议。
---

# 性能可观测性关联分析（JMeter）

## 概述

回答“为什么慢/为什么报错”：把 **`ai/perf-results.json`（tool=jmeter）** 与应用/系统/中间件监控对齐，输出定位结论。

核心产物（**`runs/<plan_id>/`**）：

- `runs/<plan_id>/docs/performance-correlation.md`（给人读）
- `runs/<plan_id>/ai/performance-correlation.json`（给 AI 读）

## 目录约定

- 输入优先：`runs/<plan_id>/ai/perf-results.json`；原始 **JTL** 时间戳可对齐监控轴。
- 输出：`docs/` 与 `ai/` 分层目录。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 触发条件

适用于：

- 压测后需根因定位；`jmeter-perf-result-analyzer` 已判定 Fail 或需加深分析。

不适用于：

- 无压测结果数据。

## 输入

- 必选：`ai/perf-results.json`（或 JTL + 计划临时归一化）。
- 可选：APM、系统、DB、Redis、MQ 等指标导出。

## 输出

1. `docs/performance-correlation.md`：异常时间窗、跨层信号、假设与优先级。
2. `ai/performance-correlation.json`：`time_windows`、`signals`、`suspicions`、`confidence`、`actions`。

## 分析方法（默认）

1. 对齐压测窗口与监控采样时间（注意 JMeter 客户端时钟与服务器 NTP）。
2. 识别 RT/错误/吞吐突变区间。
3. 多信号关联（CPU、GC、慢 SQL、连接池、限流）。
4. 输出高/中/低置信度假设与可验证动作。

## 门禁规则

- 关键监控缺失时不输出确定性根因。

## 与上下游衔接

- 上游：`jmeter-scaffold-from-plan`、`jmeter-perf-result-analyzer`。
- 下游：根据分析结论回到性能计划、造数、应用优化或人工评审流程。

## 下一步建议

- 根据 `performance-correlation.md` 的瓶颈证据更新测试计划或推动应用侧优化。

## 失败处理

- 时间戳无法对齐：给出标准化建议与近似结论。
- 监控缺失：输出必补指标清单。
