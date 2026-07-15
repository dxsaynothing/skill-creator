---
name: jmeter-perf-test-data-prep
description: JMeter 压测前测试数据准备。支持 DDL/SQL 批量造数与 HTTP 接口造数（及混合模式），产物对齐 CSV Data Set Config 与 runs 目录约定。
---

# JMeter 测试数据准备（DDL / API / Hybrid）

## 概述

在 **`runs/<plan_id>/`** 下产出压测可用数据与配套脚本/说明，目录分层如下：
- `docs/`：给人读的说明文档（`.md`）
- `ai/`：给 AI 读的结构化文件（`.json`）
- `data/`：执行数据与脚本（`.csv/.sql/.jtl/.jmx/.ps1/.sh`）

执行本 Skill 前须与用户确认 **`plan_id`**（与 `performance-plan.yaml` 的 `meta.plan_id` 一致）。

**准备模式 `prep_mode`（Gate 必选其一）**：

| 模式 | 适用 |
|------|------|
| `ddl` | 有表结构，可直接或经 SQL 批量写入库并导出/对齐 CSV。 |
| `api` | 无 DDL、或数据只能经业务 HTTP 接口创建；通过调用接口造数并落地 CSV。 |
| `hybrid` | 部分数据走库表批量、部分走接口；多 CSV 或分步合并。 |

## 用户引导提示（Gate）

当用户只触发本 Skill、但未明确提供 DDL、接口说明或造数模式时，必须先提示用户可以选择以下方式提供造数依据，禁止直接默认进入某一种模式：

1. **提供 DDL 或字段清单**：适合 `prep_mode=ddl`，需要数据库方言、表名、`CREATE TABLE` DDL 或字段清单，可生成 `insert.sql`、`data.csv`、`delete.sql`。
2. **提供接口说明或调用示例**：适合 `prep_mode=api`，需要接口文档片段、curl 示例或“步骤 A→B→C”的造数链路，可生成 API 造数脚本、CSV 与清理说明。
3. **说明哪些数据走库表、哪些走接口**：适合 `prep_mode=hybrid`，需要拆分实体、关联键与最终 CSV 合并策略。

推荐问法：

> 你希望用哪种方式造数？可以提供：1）DDL/字段清单；2）接口说明、curl 或造数步骤；3）库表 + 接口混合方案。若不确定，我可以根据 `performance-plan.yaml` 和现有接口文档先给出建议模式与所需补充信息。

## 目录约定

- 所有产物在 **`runs/<plan_id>/docs`、`runs/<plan_id>/ai`、`runs/<plan_id>/data`**。
- CSV 路径与 `data/performance-plan.yaml` 中 `data.file`、`variable_names` 对齐（首行表头、列顺序与 JMeter 变量名一致）。
- 兼容读取顺序：优先新路径（`docs/`、`ai/`、`data/`），若不存在再回退 `runs/<plan_id>/` 根目录旧路径。

## 造数数量推导（新增 Gate）

- 默认必须先读取 `runs/<plan_id>/data/performance-plan.yaml`，按计划给出“建议造数数量”，再向用户确认是否覆盖。
- 不再直接让用户拍脑袋给数量；若用户未指定，则使用计划推导值。
- 推导口径（优先级从高到低）：
  1. 若场景有 `jmeter.thread_group.num_threads`，取其最大值；
  2. 否则取 `workload.users` 最大值；
  3. 若均缺失，回退默认 `100` 并标注风险。
- 基线建议冗余系数：
  - `same_user_on_iteration=true`（或等价“每线程复用同一账号”）：建议数量 = `max_threads * 1.2`，向上取整；
  - 非复用（每迭代/每请求需新账号）：建议数量 = `max_threads * 5`（至少覆盖 5 分钟基线常见轮转）。
- 最终确认摘要必须同时给出：`计划推导值`、`用户确认值`、`偏差风险`（过少可能重复冲突，过多增加准备成本）。

## 触发条件

适用于：

- 需为压测准备账号池、商品池、订单池等可循环数据。
- **仅有接口文档**、无库表权限或不允许直连写库，需 **接口造数**。
- 需同时生成 **回收/清理** 手段（`delete.sql` 或 API 清理手册）。

不适用于：

- 只要单条 SQL 样例、不需要批量 CSV。
- 纯文档讨论、不落盘。

## 输出总览（按模式）

### `prep_mode: ddl`

- `runs/<plan_id>/data/insert.sql`
- `runs/<plan_id>/data/data.csv`
- `runs/<plan_id>/data/delete.sql`（按本次插入主键回收）

### `prep_mode: api`

- `runs/<plan_id>/data/data.csv`（完整数据或**表头 + 占位行**，配合脚本补全）
- `runs/<plan_id>/docs/api-seed-playbook.md`（分步说明，含示例）
- 可选：`runs/<plan_id>/data/api-seed.ps1`（可编辑脚本骨架）
- `runs/<plan_id>/docs/api-cleanup-playbook.md`（注销/删除接口或手工回收步骤；无 `delete.sql` 时必选其一）

### `prep_mode: hybrid`

- DDL 分支产物：`data/insert.sql`、`data/data-db.csv`、`data/delete.sql`（若适用）。
- API 分支产物：`data/data-api.csv`、`docs/api-seed-playbook.md`、`docs/api-cleanup-playbook.md`（及可选 `data/api-seed.ps1`）。
- 在 `docs/performance-plan.md` 或本 Skill 摘要中说明：JMeter **多 CSV Data Set Config** 或合并为单 `data/data.csv` 的策略（字段去重、主键关联列）。

## 模式 `ddl`：输入 / 工作流 / 规则

### 输入（必填）

1. 数据库方言：`mysql` 或 `postgresql`
2. 表名
3. 表结构（任选其一）：`CREATE TABLE` DDL 或字段清单
4. `data/performance-plan.yaml`（用于推导建议数量）或用户明确覆盖后的目标行数

### 输入（选填）

批大小、主键/唯一键策略、回收策略、外键策略、值域、空值率、脱敏规则（与通用 sql-csv-from-table-schema 一致）。

### 工作流（Gate）

1. 若用户未明确选择 `ddl`，先按“用户引导提示（Gate）”说明可提供 DDL/字段清单后再继续。
2. 解析 DDL 或字段清单。
3. 读取 `data/performance-plan.yaml` 并计算建议造数数量（见“造数数量推导”）。
4. 仅对关键缺口提问（方言、是否接受推导数量、主键/唯一键）。
5. 默认值 + 风险说明，用户确认接受项。
6. 输出确认摘要，用户明确「确认」后落盘。
7. 生成 `data/insert.sql`、`data/data.csv`、`data/delete.sql`。
8. 校验：SQL/CSV 行数与列顺序一致、唯一键无冲突、`delete.sql` 仅覆盖本次插入键。

### 生成与质量规则

- 类型映射、方言差异、约束处理、质量校验清单与 `performance_skill` 中 `sql-csv-from-table-schema` 保持一致。
- 批大小默认 `1000`；行数默认值改为“按计划推导”，仅在计划缺失时回退 `100`。
- 若用户指定行数与推导值偏差超过 2 倍，必须在确认摘要中显式提示风险。

## 模式 `api`：输入 / 工作流 / 规则

### 输入（必填）

1. `base_url`（可与 `performance-plan.yaml` 的 `meta.base_url` 一致）
2. 造数链路：接口说明（OpenAPI 片段、curl 示例、或「步骤 A→B→C」文字）
3. 目标 **CSV 列名** 及与 **响应字段** 的对应关系（如 JSONPath：`$.data.token` → 列 `accessToken`）
4. 目标行数或「循环调用次数」

### 输入（选填）

- 鉴权方式（与 `global.auth` 对齐：`bearer` / `cookie` / 登录换 token 等多步）
- 速率限制、并发上限、幂等键/防重策略
- 失败重试与超时

### 工作流（Gate）

1. 若用户未明确选择 `api`，先按“用户引导提示（Gate）”说明可提供接口说明、curl 示例或造数步骤后再继续。
2. 确认 `prep_mode=api`，确认 `plan_id`。
3. 梳理调用顺序（先登录再创建资源等），标出每步请求体/Query 中哪些字段来自上一步响应或循环变量。
4. 确认 CSV 表头与 JMeter `variable_names` 一致（逗号分隔、无多余空格）。
5. 确认回收策略：能写 `docs/api-cleanup-playbook.md` 的接口清单或明确「仅手工清理」及风险。
6. 用户「确认」后落盘：`docs/api-seed-playbook.md`、`data/data.csv`（及可选 `data/api-seed.ps1`）、`docs/api-cleanup-playbook.md`。

### `api-seed-playbook.md` 必须包含

- 环境变量占位（如 `$env:PERF_TOKEN`），禁止将真实密钥写入仓库。
- 至少一段可执行示例，且需覆盖当前用户平台：
  - Windows：**PowerShell**（`Invoke-RestMethod` / `Invoke-WebRequest`）；
  - macOS：优先 **pwsh**（PowerShell 7）或 **bash + curl (+ jq)** 等效示例。
- 示例需包含请求头、请求体与 UTF-8 编码注意事项。
- 如何将响应属性写入 `data.csv`（`Export-Csv -Append` 或逐行拼接的注意事项：引号与逗号转义）。
- 429/5xx 时的退避建议。

### 跨平台执行约定（新增）

- 生成 API 造数脚本时，默认同时提供：
  1. `data/api-seed.ps1`（Windows / macOS 的 `pwsh` 可执行）；
  2. `data/api-seed.sh`（macOS/Linux，基于 `bash + curl`，可选依赖 `jq`）。
- 若用户明确仅需某平台，可只生成对应脚本，但 `api-seed-playbook.md` 仍需说明另一平台的等效调用方式。
- 路径与换行要求：
  - 在文档中分别给出 Windows 路径示例（反斜杠）与 macOS 路径示例（正斜杠）；
  - CSV 输出统一 UTF-8，避免 BOM 导致 JMeter 读首列异常。
- macOS 命令示例至少包含：登录获取 token、循环创建、写入 `data.csv`、失败重试/退避。

### 校验

- `data.csv` 首行与 `variable_names` 列数一致。
- 若仅有表头无数据：在 playbook 中写明「须先执行 seed 再压测」，并在下游 readiness 标为告警或阻塞（由检查 Skill 判定）。

## 模式 `hybrid`

1. 若用户未明确选择 `hybrid`，先按“用户引导提示（Gate）”说明可提供库表 + 接口混合方案后再继续。
2. 与用户拆分：哪些实体走 `ddl`、哪些走 `api`。
3. 分别产出上述文件；文件命名区分 `data-db.csv` 与 `data-api.csv`（或用户指定名）。
4. 明确 JMeter 侧：多 **CSV Data Set Config**（不同线程组/不同路径）或合并为单 CSV 的合并键与顺序依赖。

## 与上下游衔接

- 上游：`jmeter-perf-plan-from-doc`（可选 `data/performance-plan.yaml` 中指明各场景 `data.file`）。
- 下游：`jmeter-perf-data-readiness-checker`、`jmeter-scaffold-from-plan`；DDL 模式下压测后执行 `data/delete.sql`；API 模式按 `docs/api-cleanup-playbook.md` 回收。

## 下一步建议

- `jmeter-perf-data-readiness-checker`（计划中已回填 `data.source=csv` 且造数产物就绪后）。

## 失败处理

- **ddl**：DDL 解析失败 → 降级字段清单模式；无主键/唯一键识别 → 不生成 `delete.sql` 并标明回收阻塞项；关键参数未确认 → 不落盘。
- **api**：接口契约不清 → 输出阻塞项与最小可运行 curl 模板，不生成伪数据；无法定义清理路径 → 强制 `api-cleanup-playbook.md` 中写明风险与手工步骤。
- **hybrid**：两路数据主键冲突 → 返回冲突策略选项，不输出半成品 CSV。
