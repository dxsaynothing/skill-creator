---
name: jmeter-scaffold-from-plan
description: 读取 performance-plan.yaml（meta.runner=jmeter）生成或维护 JMX、非 GUI 执行方式与报告路径约定；业务取样器由计划驱动，不写死接口。
---

# JMeter 生成并执行（计划 -> JMX + CLI）

## 概述

从 **`runs/<plan_id>/data/performance-plan.yaml`** 驱动 JMeter：

- **计划驱动**：线程组、HTTP 请求、断言、鉴权、CSV 数据集与 SLA 元数据来自 YAML。
- **可执行**：非 GUI 命令 `jmeter -n -t ... -l ...` 与可选 `-e -o` HTML 报告。
- 脚本/模板可放在目标工程 `scripts/`、`templates/`，但业务 URL 与场景以 plan 为准。

## 触发条件

适用于：

- 已确认 `performance-plan.yaml`（`meta.runner: jmeter`），需要 **JMX 骨架 + 执行说明** 或直接执行。
- 希望 CSV、线程数、爬坡与计划一致。

不适用于：

- 仍在讨论测哪些接口（回到 `jmeter-perf-plan-from-doc`）。
- 仅要结果分析（`jmeter-perf-result-analyzer`）。

## 输入

- 必选：`runs/<plan_id>/data/performance-plan.yaml`（schema：`../perf-shared/references/plan_schema.md`）
- 可选：环境覆盖（host/token）、额外 `user.properties`

## 输出（目标工程建议结构）

- `runs/<plan_id>/data/plan.jmx`（或与 `run.jmeter.jmx_path` 一致）：Test Plan → Thread Group(s) → Config → Samplers → Assertions → Listeners（JTL/HTML 路径与 plan 对齐）。
- `scripts/README.md` 或仓库根说明：**执行命令**、覆盖参数、常见问题。
- 可选：`scripts/apply_plan_to_jmx.md`（纯文档步骤：如何用 GUI 合并生成物）或自动化脚本占位说明。
- 新增：`runs/<plan_id>/docs/JMX-EXPLAIN.md`（人类可读解析文档，帮助在 JMeter GUI 中快速理解结构与变量流转）。

报告与 JTL 建议目录：**`runs/<plan_id>/data/`**（如 `data/results.jtl`、`data/html/`；与 `run.jmeter.*` 对齐）。
兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 推荐执行命令（示例）

工作目录为 **`runs/<plan_id>/`** 时（将路径与 `plan_id` 替换为实际值）：

```powershell
jmeter -n -t .\data\plan.jmx -l .\data\results.jtl -e -o .\data\html -JbaseUrl=https://staging-api.example.com
```

分布式示例：

```powershell
jmeter -n -t .\data\plan.jmx -l .\data\results.jtl -R host1,host2
```

`baseUrl`、Token 等敏感项通过 **`-J` / 环境变量** 注入，不写进仓库明文（与 `global.auth.token_env` 一致）。

## 映射规则（核心）

1. **场景 → 线程组或取样器树**
   - `scenarios[].enabled=true` → 生成可执行取样器；`false` → 跳过。
   - 每个场景默认：**独立 Thread Group** 或 **单一 Thread Group 下多个取样器 + Throughput Controller**（二选一须在 README 说明）；默认推荐 **每 P0 链路独立 Thread Group** 便于调参。
2. **负载**
   - `scenario.jmeter.thread_group` 优先；否则从 `workload` 推导：
     - `num_threads = workload.users`
     - `ramp_time_sec = ceil(users / spawn_rate)`（`spawn_rate` 缺失时用 schema 默认）
     - `duration_sec` 来自 `workload.duration`；`scheduler=true`。
3. **HTTP**
   - `endpoint.method` + `meta.base_url` + `endpoint.path` → **HTTP Request**；`default_headers` → **HTTP Header Manager**。
4. **鉴权**
   - `global.auth.type=bearer` → `Authorization: Bearer ${__env(PERF_TOKEN,)}` 或 **HTTP Authorization Manager**；token 仅来自环境/`user.properties`，不落库。
5. **校验**
   - `checks.status_codes` → **Response Assertion**。
6. **数据**
   - `data.source=csv` → **CSV Data Set Config**：`filename`、`variableNames`、`recycle`、`shareMode` 映射 `data.recycle`、`data.sharing_mode`（计划字段见 schema）。
7. **SLA**
   - 写入 JMX 的 **JSR223 Listener/注释** 或仅作为元数据供分析器读取；阈值判定以 **`jmeter-perf-result-analyzer`** 为准。

## 工作流

1. 校验 YAML（runner、必填字段、场景 id 唯一）。
2. 生成或更新 JMX（含 Listeners：建议 **Simple Data Writer / jtl** 最小集，避免 GUI 重型监听器影响负载）。
3. 生成 `docs/JMX-EXPLAIN.md`（与当前 `data/plan.jmx` 一一对应）。
4. 输出 PowerShell 执行示例与环境变量清单。
5. 输出「待人工补充」：复杂 OAuth 流程、WebSocket、gRPC、签名头、插件型线程组等。

## `JMX-EXPLAIN.md` 必须包含

1. **测试总览**：`plan_id`、目标类型、`base_url`、线程数/爬坡/时长、CSV 文件与报告路径。
2. **线程组说明**：为何使用单线程组/多线程组；关键参数与计划字段映射。
3. **执行链路（按顺序）**：每个取样器的方法、路径、请求体变量来源、断言。
4. **变量与提取器映射表**：变量名、JSONPath、默认值、被哪些步骤消费。
5. **鉴权与数据源**：Header 逻辑、`PERF_TOKEN` 兜底、CSV Data Set Config 参数解释。
6. **结果产物说明**：JTL/HTML 输出路径与主要字段。
7. **常见问题排查**：变量为空、报告目录已存在、CSV 列不匹配、token 提取失败等。

要求：内容必须对应“当前生成的 `data/plan.jmx` 实际节点”，禁止只写模板化空文档。

## 默认策略

- 无 `scenario.jmeter.sampler_name`：默认 `"{METHOD} {path}"`。
- 无 CSV：`inline` 时生成占位变量并告警。
- 无断言：默认断言 `200`。
- JTL 字段：建议配置写入 `elapsed`、`responseCode`、`success`、`label` 等以便归一化。

## 与上下游衔接

- 上游：`jmeter-perf-plan-from-doc`、`jmeter-perf-data-readiness-checker`。
- 下游：JTL/HTML 放入 `runs/<plan_id>/data/`，供 **`jmeter-perf-result-analyzer`**。

## 下一步建议

- `jmeter-perf-result-analyzer`。

## 失败处理

- 计划缺关键字段：返回错误列表，不生成半成品 JMX。
- 非法 method/path：跳过该场景并记录告警。
- 鉴权冲突：降级 `none` 并提示风险。
