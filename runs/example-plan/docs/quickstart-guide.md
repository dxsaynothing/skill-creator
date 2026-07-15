# JMeter 性能测试技能快速开始指南

## 概述

本技能包提供了一套完整的 JMeter 性能测试工作流，从需求澄清到结果分析，共包含 7 个技能。所有产物统一在 `runs/<plan_id>/` 目录下管理。

## 工作流程图

```
需求澄清 → 计划生成 → 数据准备 → 就绪检查 → JMX执行 → 结果分析 → 可观测性关联
   (01)       (02)       (03)       (04)       (05)       (06)         (07)
```

## 快速开始步骤

### 第一步：需求澄清（必选）

**技能**：`jmeter-perf-requirement-clarifier`

**触发时机**：用户刚开始提"做性能测试"，但目标/SLA/范围不完整。

**输入**：
- 接口文档或需求文档
- 可选：历史峰值数据、发布窗口、JMeter环境信息

**输出**：
- `runs/<plan_id>/docs/performance-requirements.md` - 可读确认单
- `runs/<plan_id>/ai/performance-requirements.json` - 结构化确认结果

**关键流程**：
1. 确认 `plan_id`（与后续所有步骤关联）
2. 分步问答：压测目标、SLA、负载规模、业务范围、验收标准
3. 提供默认值与风险说明
4. 用户明确"确认"后才生成产物

**下一步**：执行 `jmeter-perf-plan-from-doc`

---

### 第二步：计划生成（必选）

**技能**：`jmeter-perf-plan-from-doc`

**触发时机**：需要根据文档制定结构化性能测试计划。

**输入**：
- 接口文档或需求文档
- 可选：`ai/performance-requirements.json`

**输出**：
- `runs/<plan_id>/data/performance-plan.yaml` - 结构化计划（供下游消费）
- `runs/<plan_id>/docs/performance-plan.md` - 可读计划文档

**关键流程**：
1. 抽取接口、业务路径、鉴权、依赖
2. 接口标记 P0/P1/P2
3. 分步提问 → 默认值+风险 → 用户确认
4. 生成 YAML 和 MD 文件
5. **必须包含** `meta.runner: jmeter`

**下一步**：执行 `jmeter-perf-test-data-prep`（需造数时）

---

### 第三步：测试数据准备（按需）

**技能**：`jmeter-perf-test-data-prep`

**触发时机**：需要为压测准备账号池、商品池等测试数据。

**准备模式**（Gate必选其一）：
- `ddl`：有表结构，可直接批量写入库
- `api`：数据只能经业务 HTTP 接口创建
- `hybrid`：部分走库表，部分走接口

**输入**：
- DDL/字段清单（DDL模式）
- 接口说明/API示例（API模式）
- `data/performance-plan.yaml`（用于推导数量）

**输出**（按模式）：
- DDL模式：`data/insert.sql`、`data/data.csv`、`data/delete.sql`
- API模式：`data/data.csv`、`docs/api-seed-playbook.md`、`docs/api-cleanup-playbook.md`
- Hybrid模式：两者结合

**关键流程**：
1. 确认造数模式
2. 根据计划推导建议数量（不再让用户拍脑袋）
3. 用户确认数量
4. 生成数据与清理脚本

**下一步**：执行 `jmeter-perf-data-readiness-checker`

---

### 第四步：就绪检查（必选）

**技能**：`jmeter-perf-data-readiness-checker`

**触发时机**：准备执行压测前，验证环境、数据、JMeter条件是否就绪。

**输入**：
- `data/performance-plan.yaml`

**输出**：
- `docs/performance-readiness.md` - 就绪检查报告
- 可选：`ai/performance-readiness.json` - 结构化结果（需用户明确要求）

**检查清单**：
1. 环境一致性
2. 数据可用性
3. 幂等与回收
4. 依赖前置
5. 监控可观测性
6. 数据源绑定
7. API造数产物完整性
8. **JMeter执行条件**（版本、JMX、JTL路径、JVM、插件）

**门禁规则**：`blockers` 非空时，不建议执行正式压测。

**下一步**：执行 `jmeter-scaffold-from-plan`

---

### 第五步：JMX生成与执行（必选）

**技能**：`jmeter-scaffold-from-plan`

**触发时机**：已确认计划，需要生成 JMX 并执行压测。

**输入**：
- `data/performance-plan.yaml`

**输出**：
- `data/plan.jmx` - JMeter测试计划
- `docs/JMX-EXPLAIN.md` - JMX结构解析文档
- `scripts/README.md` - 执行说明

**执行命令示例**：
```powershell
# 单机执行
jmeter -n -t .\data\plan.jmx -l .\data\results.jtl -e -o .\data\html -JbaseUrl=https://staging-api.example.com

# 分布式执行
jmeter -n -t .\data\plan.jmx -l .\data\results.jtl -R host1,host2
```

**关键映射**：
- 场景 → 线程组
- 负载 → 线程数/爬坡/时长
- HTTP → 请求配置
- 鉴权 → Header/Authorization Manager
- 校验 → Response Assertion
- 数据 → CSV Data Set Config

**下一步**：执行 `jmeter-perf-result-analyzer`

---

### 第六步：结果分析（必选）

**技能**：`jmeter-perf-result-analyzer`

**触发时机**：已有 JTL 或 HTML 报告产物，需要对照 SLA 做门禁判断。

**输入**：
- JTL 和/或 HTML 报告
- `data/performance-plan.yaml`

**输出**：
- `docs/perf-analysis.md` - 分析结论
- `ai/perf-results.json` - 归一化结果
- `ai/next-run-patch.yaml` - 下一轮建议（可选）

**分析维度**：
1. **达标判定**：P95、错误率、最小吞吐
2. **瓶颈识别**：latency/error/rps TopN
3. **风险分级**：high/medium/low

**下一步**：执行 `jmeter-perf-observability-correlator`（需结合监控定位时）

---

### 第七步：可观测性关联分析（按需）

**技能**：`jmeter-perf-observability-correlator`

**触发时机**：压测后需根因定位，已判定 Fail 或需加深分析。

**输入**：
- `ai/perf-results.json`
- 可选：APM、系统、DB、Redis、MQ等监控指标

**输出**：
- `docs/performance-correlation.md` - 瓶颈证据链
- `ai/performance-correlation.json` - 结构化分析结果

**分析方法**：
1. 对齐压测窗口与监控采样时间
2. 识别 RT/错误/吞吐突变区间
3. 多信号关联（CPU、GC、慢SQL、连接池、限流）
4. 输出高/中/低置信度假设与可验证动作

---

## 目录结构约定

```
runs/<plan_id>/
├── docs/                     # 给人读的文档
│   ├── performance-requirements.md
│   ├── performance-plan.md
│   ├── performance-readiness.md
│   ├── JMX-EXPLAIN.md
│   ├── perf-analysis.md
│   └── performance-correlation.md
├── ai/                       # 给AI/自动化消费的结构化文件
│   ├── performance-requirements.json
│   ├── perf-results.json
│   ├── performance-readiness.json
│   └── performance-correlation.json
└── data/                     # 执行数据与脚本
    ├── performance-plan.yaml
    ├── plan.jmx
    ├── results.jtl
    ├── data.csv
    ├── insert.sql
    ├── delete.sql
    └── html/                  # HTML报告目录
```

## 典型使用场景

### 场景一：完整流程（从零开始）

1. 执行 `jmeter-perf-requirement-clarifier` - 澄清需求
2. 执行 `jmeter-perf-plan-from-doc` - 生成计划
3. 执行 `jmeter-perf-test-data-prep` - 准备数据
4. 执行 `jmeter-perf-data-readiness-checker` - 检查就绪
5. 执行 `jmeter-scaffold-from-plan` - 生成并执行 JMX
6. 执行 `jmeter-perf-result-analyzer` - 分析结果
7. （可选）执行 `jmeter-perf-observability-correlator` - 根因定位

### 场景二：快速执行（已有计划）

1. 执行 `jmeter-perf-data-readiness-checker` - 检查就绪
2. 执行 `jmeter-scaffold-from-plan` - 执行压测
3. 执行 `jmeter-perf-result-analyzer` - 分析结果

### 场景三：仅分析结果

1. 执行 `jmeter-perf-result-analyzer` - 分析已有 JTL/HTML
2. （可选）执行 `jmeter-perf-observability-correlator` - 根因定位

## 重要约定

1. **plan_id 贯穿始终**：所有产物共享同一 `plan_id`，便于追溯。
2. **Gate 机制**：关键步骤需用户明确确认后才生成产物。
3. **默认值策略**：缺失参数提供合理默认值，同时标注风险。
4. **敏感信息**：Token 等敏感信息通过环境变量注入，不写入仓库。
5. **兼容读取**：优先读取新路径（`docs/`、`ai/`、`data/`），回退旧路径。

## 常见问题

**Q：如何选择造数模式？**
A：
- 有库表权限 → DDL 模式
- 只能通过接口 → API 模式
- 部分库表+部分接口 → Hybrid 模式

**Q：何时需要就绪检查？**
A：准备执行压测前必做，避免环境/数据问题导致无效测试。

**Q：如何处理阻塞项？**
A：阻塞项非空时，不建议执行正式压测。可选择"带风险执行"，但需在报告中记录。

**Q：结果分析 Pass/Fail 的判定标准？**
A：所有场景的 SLA 都达标才判定 Pass；P0 场景失败则风险等级为 high。

---

通过本指南，您可以快速理解并使用这套 JMeter 性能测试技能，从需求澄清到结果分析，实现标准化、可追溯的性能测试流程。