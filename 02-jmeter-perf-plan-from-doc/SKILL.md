---
name: jmeter-perf-plan-from-doc
description: 从接口文档或需求文档生成 JMeter 性能测试计划。输出 performance-plan.yaml（meta.runner=jmeter）与可读版性能计划文档。
---

# 性能测试计划生成（文档 -> 计划，JMeter）

## 概述

本 Skill 把“接口文档/需求文档”转成结构化性能测试计划，供 JMeter 脚手架与结果分析消费：

- `runs/<plan_id>/data/performance-plan.yaml`（下游 JMX/CLI 输入，执行配置）
- `runs/<plan_id>/docs/performance-plan.md`（评审用，给人读）

## 目录约定（`runs/<plan_id>/`）

- `<plan_id>` 与 `data/performance-plan.yaml` 中 `meta.plan_id` 一致；与 `jmeter-perf-requirement-clarifier` 产出对齐。
- 计划文件写入 **`runs/<plan_id>/data`** 与 **`runs/<plan_id>/docs`**。
- **`meta.runner` 必须为 `jmeter`**。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

文档信息不完整时，须引导补齐；无法补齐时使用默认值并记录风险。

## 触发条件

适用于：

- 用户提供 OpenAPI/Swagger/Markdown 或需求文档，需要制定 **JMeter** 性能计划。
- 需要“接口优先级 + 线程/爬坡/时长建议 + SLA 草案”。

不适用于：

- 已有完整 `performance-plan.yaml` 且只需生成 JMX（转 `jmeter-scaffold-from-plan`）。
- 用户只想分析测试结果（转 `jmeter-perf-result-analyzer`）。

## 输入

- 必选其一：接口文档或需求文档。
- 可选：历史流量、非功能目标、环境信息、`ai/performance-requirements.json`。

## 输出

1. `runs/<plan_id>/data/performance-plan.yaml`
   - 结构遵循：`../perf-shared/references/plan_schema.md`
   - 必须包含 `run.jmeter`（可由默认值生成）：`jmx_path`、`jtl_file`、`html_report_dir` 等。
2. `runs/<plan_id>/docs/performance-plan.md`
   - 接口清单、优先级、测试类型、JMeter 参数建议、风险、待确认项。

## 工作流（两阶段）

> **先问答确认，再生成文件**。未完成确认前，禁止写入 `data/performance-plan.yaml`。

### Stage 1：读取与抽取

1. 抽取接口、业务路径、鉴权、依赖。
2. 接口标记 `P0/P1/P2`，覆盖核心交易、鉴权、高频查询。

### Stage 2–4：引导、默认值、确认 Gate

与通用压测计划相同：分步提问 → 默认值+风险 → 用户回复「确认」后方可落盘。

确认摘要须包含：目标、`base_url`、线程数/爬坡/时长、SLA、链路依赖、JMeter 报告路径约定、默认项与风险。

### Stage 5A：计划骨架（Phase A）

1. 生成 `data/performance-plan.yaml` / `docs/performance-plan.md`。
2. 写入 `meta.runner: jmeter` 与 `run.jmeter`（`non_gui`、`jmx_path`、`jtl_file`、`html_report_dir` 等）。
3. 各场景可省略 `scenario.jmeter.thread_group`，由脚手架从 `workload` 推导；复杂阶梯负载在 md 中标注插件需求。
4. 动态数据场景允许 `data.source=inline` 占位，并标注待 CSV 回填。

### Stage 5B：数据源回填（Phase B）

1. `data.source=csv`，`data.file`、`variable_names` 与 JMeter **CSV Data Set Config** 一致。
2. 产出回填摘要供 readiness 使用。

### Stage 6：一致性检查

校验 schema、单位、场景可执行性；未完成 CSV 回填则高优先级告警。

## 与上下游衔接

- 上游：`jmeter-perf-requirement-clarifier`（可选）。
- Phase A 后：`jmeter-perf-test-data-prep` 造数。
- Phase B 后：`jmeter-perf-data-readiness-checker`。
- 执行：`jmeter-scaffold-from-plan`。
- 结果：`jmeter-perf-result-analyzer` 用 `meta.plan_id` 关联。

## 下一步建议

- 推荐执行：`jmeter-perf-test-data-prep`（需造数时）。

## 失败处理

- 文档解析失败：回退到用户粘贴接口清单。
- 关键参数未确认：不生成 YAML。
- SLA 缺失且用户拒绝默认值：阻塞，不进入脚手架阶段。
