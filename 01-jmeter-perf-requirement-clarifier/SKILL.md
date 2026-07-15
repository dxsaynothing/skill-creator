---
name: jmeter-perf-requirement-clarifier
description: 压测前置需求澄清与门禁确认（JMeter 链路）。通过分步问答明确目标、SLA、流量规模与成功标准，产出可追溯确认单。
---

# 性能测试需求澄清（前置 Gate，JMeter）

## 概述

本 Skill 用于在生成性能计划前完成“需求澄清与目标定义”，避免信息不全直接进入执行阶段。与 Locust 链路一致，仅下游执行器为 **JMeter**。

核心产物：

- `runs/<plan_id>/docs/performance-requirements.md`（可读确认单，给人读）
- `runs/<plan_id>/ai/performance-requirements.json`（结构化确认结果，给 AI 读）

## 目录约定（`runs/<plan_id>/`）

- 在澄清开始前与用户确认 **`plan_id`**（新建或沿用已有）；须与后续 `performance-plan.yaml` 的 `meta.plan_id` 一致。
- 所有本 Skill 产出写入 **`runs/<plan_id>/docs`** 与 **`runs/<plan_id>/ai`**，不在项目根目录散落。
- 建议在 `ai/performance-requirements.json` 的 `meta` 中写入 `plan_id` 与 **`runner: jmeter`**，供 `jmeter-perf-plan-from-doc` 等下游引用。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 触发条件

适用于：

- 用户刚开始提“做 JMeter 性能测试”，但目标/SLA/范围不完整。
- 需要给后续 `jmeter-perf-plan-from-doc` 提供可追溯输入。
- 需要明确“发布门禁标准”。

不适用于：

- 已有完整确认单并明确无需再澄清。
- 用户只想分析已有压测结果（转 `jmeter-perf-result-analyzer`）。

## 输入

- 必选其一：
  - 接口文档（OpenAPI/Swagger/Markdown）
  - 需求文档（PRD/业务流程）
- 可选：
  - 历史峰值（QPS/并发/日请求量）
  - 发布窗口与风险偏好
  - JMeter 执行环境（单机/分布式、插件依赖）

## 输出

1. `runs/<plan_id>/docs/performance-requirements.md`
   - 必须包含：目标类型、范围、SLA、负载目标、门禁标准、默认项与风险；注明 **JMeter** 为执行工具。
2. `runs/<plan_id>/ai/performance-requirements.json`
   - 供 `jmeter-perf-plan-from-doc` 直接消费；`meta.plan_id` 建议与目录名一致；建议含 `meta.runner: jmeter`。

## 必问清单（最小集）

1. 压测目标：`baseline|capacity|stress|soak|gate`
2. 核心 SLA：`P95/P99`、错误率、目标吞吐（RPS/QPS）
3. 负载规模：并发线程数、持续时长、爬坡策略（等价 ramp-up）
4. 业务范围：P0/P1 链路（至少 1 条交易链路）
5. 验收标准：什么条件判定通过/失败

## 工作流（强制 Gate）

1. **文档抽取**：抽取业务链路与关键接口，但不生成测试计划。
2. **分步问答**：每轮只问关键缺口。
3. **默认值提议**：缺失项给默认值，同时给风险与影响说明。
4. **确认摘要**：输出结构化摘要，要求用户明确“确认”。
5. **产物输出**：仅在确认后生成 `docs/performance-requirements.md` 与 `ai/performance-requirements.json`。

## 门禁规则

- 未确认关键项（目标/SLA/负载/范围）时，禁止进入计划生成阶段。
- 默认值必须逐项确认接受后才可落盘。
- 若用户拒绝默认值且不给数值，输出阻塞项清单并结束。

## 与上下游衔接

- 下游：`jmeter-perf-plan-from-doc`（优先消费 `ai/performance-requirements.json`）。
- 并行参考：`jmeter-perf-data-readiness-checker`（可在确认后检查环境与数据；执行前仍需完整计划）。

## 下一步建议

- 推荐执行：`jmeter-perf-plan-from-doc`。

## 失败处理

- 文档无法抽取：降级为“用户粘贴关键接口+目标参数”流程。
- 关键信息长期缺失：输出阻塞项与建议默认值，不生成下游输入文件。
