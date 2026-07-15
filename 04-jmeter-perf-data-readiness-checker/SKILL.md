---
name: jmeter-perf-data-readiness-checker
description: JMeter 压测前环境与数据就绪检查。含 JMeter/JVM/JMX/插件与 JTL 配置项，输出阻塞项与准备清单。
---

# 性能测试数据与环境就绪检查（JMeter）

## 概述

在压测执行前验证“环境、数据、幂等、JMeter 执行条件”是否就绪。

默认产物（**`runs/<plan_id>/`**）：

- `runs/<plan_id>/docs/performance-readiness.md`（给人读）

可选结构化产物：

- `runs/<plan_id>/ai/performance-readiness.json`（给 AI/CI/自动化门禁读）

默认只生成 Markdown 报告。仅当用户明确要求机器可读结果、自动化门禁、CI 集成或后续 Skill 消费时，才生成 `ai/performance-readiness.json`。

## 目录约定

- 输入：`runs/<plan_id>/data/performance-plan.yaml`。
- 输出：默认写入 `docs/`；若启用结构化输出，再写入 `ai/`。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 触发条件

适用于：

- 准备进入 **`jmeter-scaffold-from-plan`** 或手工 `jmeter -n` 之前。
- 担心数据污染、环境不一致、JMX/CSV 路径错误。

不适用于：

- 仅文档级计划、不执行压测。

## 输入

- 必选：`data/performance-plan.yaml`（含 `meta.runner: jmeter` 与 `run.jmeter`）。
- 可选：环境清单、数据说明、回收脚本、JMeter 安装路径与版本、是否需要结构化 JSON 输出。

## 输出

1. 必选：`docs/performance-readiness.md`：环境、数据、JMeter 专项、风险与阻塞项。
2. 可选：`ai/performance-readiness.json`：`ready`、`blockers`、`warnings`、`actions`、`checked_at`。

结构化 JSON 生成规则：

- 用户未要求机器可读输出时，不生成 `ai/performance-readiness.json`。
- 用户要求自动化门禁、CI 集成、后续 Skill 直接消费或明确点名 JSON 时，才生成该文件。
- 若不生成 JSON，Markdown 报告必须完整包含 `ready` 结论、阻塞项、警告项与下一步动作，避免信息只存在于结构化产物中。

## 检查清单（在通用清单基础上增加 JMeter 项）

1. **环境一致性**：`base_url`、限流、网关与线上差异。
2. **数据可用性**：账号池/库存等是否满足目标线程数。
3. **幂等与回收**。
4. **依赖前置**：鉴权、链路顺序、预热。
5. **监控可观测性**。
6. **数据源绑定**：`data.source=csv` 时 `data.file`、`variable_names` 有效且文件存在。
7. **API 造数产物**（若同目录无 `docs/api-seed-playbook.md` 且计划/说明未声明接口造数，则整项跳过）
   - `docs/api-seed-playbook.md` 是否存在且步骤完整（鉴权、顺序、CSV 写入约定）。
   - 可选 `data/api-seed.ps1` 与当前环境变量（如 token）是否可复现执行。
   - `data/data.csv` 是否已有真实数据行；若仅表头+占位，标为 **warning** 或 **blocker**（视压测是否强依赖预置数据而定）。
   - `docs/api-cleanup-playbook.md` 是否存在；清理路径不明时 **blocker** 或高优先级 **warning**。
8. **JMeter 执行条件**
   - `jmeter -v` 或等价命令可用；版本满足计划要求。
   - `run.jmeter.jmx_path` 存在或可由脚手架生成；若已存在 JMX，与 plan 场景是否一致。
   - `jtl_file`、`html_report_dir` 父目录可写；磁盘空间充足。
   - `properties_file`、`remote_hosts`（分布式）若配置则可达。
   - JVM：`run.jmeter.jvm_heap` 与机器内存匹配。
   - **百分位与聚合**：若门禁依赖 P95/P99，确认 JTL/HTML 报告配置能产出百分位（缺失则在 `warnings` 中标明“结论可能不完整”）。
9. **插件**：计划若依赖阶梯线程组等插件，检查插件是否安装。

## 门禁规则

- `blockers` 非空时，默认不建议执行正式压测。
- “带风险执行”须在报告中显式记录。

## 与上下游衔接

- 上游：`jmeter-perf-plan-from-doc`、`jmeter-perf-test-data-prep`。
- 下游：`jmeter-scaffold-from-plan`。

## 下一步建议

- `jmeter-scaffold-from-plan`（`ready=true` 时）。

## 失败处理

- 缺少计划文件：报错并终止检查。
- 数据源未回填：列出缺失场景，不自动改 plan。
