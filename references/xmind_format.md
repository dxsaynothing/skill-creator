# XMind 文件格式参考

## 概述

XMind (.xmind) 文件是一个标准 ZIP 压缩包，内部包含 XML 格式的内容文件。本 skill 生成的 XMind 文件兼容 XMind 8 / XMind 2020 / XMind 2021 及以上版本。

## 文件结构

```
test_cases.xmind
├── META-INF/
│   └── manifest.xml      # 清单文件，列出包内所有文件
├── meta.xml              # 元数据（作者、创建时间）
└── content.xml           # 思维导图内容（核心）
```

## content.xml 结构

### 命名空间

```xml
xmlns="urn:xmind:xmap:xmlns:content:3.0"
```

### 层级关系

```
xmap-content
  └── sheet
       └── topic (根节点)
            └── children
                 └── topics (type="attached")
                      ├── topic (模块)
                      │    ├── title
                      │    └── children
                      │         └── topics
                      │              ├── topic (测试分组)
                      │              │    ├── title
                      │              │    └── children
                      │              │         └── topics
                      │              │              ├── topic (用例)
                      │              │              │    ├── title
                      │              │              │    └── children
                      │              │              │         └── topics
                      │              │              │              ├── topic (前置条件)
                      │              │              │              ├── topic (步骤)
                      │              │              │              ├── topic (预期结果)
                      │              │              │              ├── topic (优先级)
                      │              │              │              └── topic (类型)
```

### 元素属性

| 元素 | 属性 | 说明 |
|------|------|------|
| `sheet` | `id`, `topic_id`, `timestamp` | 画布 |
| `topic` | `id`, `timestamp`, `modified-by` | 节点 |
| `topics` | `type="attached"` | 子节点容器 |

每个 `topic` 必须包含一个 `<title>` 子元素作为显示文本。

### id 生成规则

使用 UUID hex 前 12 位：
```
topic-a1b2c3d4e5f6
sheet-abcdef123456
```

## 测试用例 JSON 输入格式

```json
{
  "title": "项目名称",
  "modules": [
    {
      "name": "模块名称",
      "groups": [
        {
          "name": "分组名称",
          "cases": [
            {
              "id": "TC-001",
              "title": "测试用例标题",
              "precondition": "前置条件",
              "steps": ["步骤1", "步骤2"],
              "expected": "预期结果",
              "priority": "P0",
              "type": "功能测试"
            }
          ]
        }
      ]
    }
  ]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | 是 | 根节点名称 |
| `modules[].name` | 是 | 功能模块名称 |
| `groups[].name` | 是 | 测试分组名称（正常功能测试/边界值测试/异常场景测试等） |
| `cases[].id` | 是 | 用例编号 |
| `cases[].title` | 是 | 用例标题 |
| `cases[].precondition` | 否 | 前置条件 |
| `cases[].steps` | 否 | 测试步骤数组 |
| `cases[].expected` | 否 | 预期结果 |
| `cases[].priority` | 是 | 优先级 (P0/P1/P2/P3) |
| `cases[].type` | 否 | 用例类型 |

## 验证方法

生成后的 .xmind 文件可通过以下方式验证：

1. **直接打开** — 用 XMind 8+/XMind 2020/XMind 2021 打开
2. **检查 ZIP 结构** — `unzip -l output.xmind`
3. **检查 XML** — `unzip -p output.xmind content.xml | head -50`
