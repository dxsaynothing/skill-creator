#!/usr/bin/env python3
"""
测试用例 XMind 文件生成器

从标准输入读取 JSON 格式的测试用例数据，生成可在 XMind 中打开的 .xmind 文件。

XMind 格式说明：
- .xmind 文件本质上是 ZIP 压缩包
- 包含 content.xml（思维导图内容）、meta.xml（元数据）、META-INF/manifest.xml（清单）

用法：
    python generate_xmind.py --output test_cases.xmind --title "项目-测试用例" < cases.json
    cat cases.json | python generate_xmind.py -o output.xmind -t "我的项目"
"""

import argparse
import json
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring


def make_topic_id():
    """生成唯一的 topic ID"""
    return f"topic-{uuid.uuid4().hex[:12]}"


def make_sheet_id():
    """生成唯一的 sheet ID"""
    return f"sheet-{uuid.uuid4().hex[:12]}"


def timestamp_now():
    """返回当前 ISO 格式时间戳"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def set_attrs(elem, attrs):
    """一键设置元素属性字典"""
    for k, v in attrs.items():
        elem.set(k, v)
    return elem


def build_content_xml(data):
    """
    根据测试用例数据构建 content.xml 的 ElementTree。

    data 结构详见 generate_xmind() 的文档注释。
    """
    NS = "urn:xmind:xmap:xmlns:content:3.0"

    root = Element(f"{{{NS}}}xmap-content")
    set_attrs(root, {"modified-by": ""})

    sheet_id = make_sheet_id()
    root_topic_id = make_topic_id()

    sheet = SubElement(root, "sheet")
    set_attrs(sheet, {
        "id": sheet_id,
        "topic-id": root_topic_id,
        "timestamp": timestamp_now(),
    })

    # 根节点
    root_topic = SubElement(sheet, "topic")
    set_attrs(root_topic, {
        "id": root_topic_id,
        "timestamp": timestamp_now(),
        "modified-by": "",
    })

    title_elem = SubElement(root_topic, "title")
    title_elem.text = data.get("title", "测试用例")

    modules = data.get("modules", [])
    if not modules:
        return root

    # 模块层 → root_topic 的 children
    root_children = SubElement(root_topic, "children")
    root_topics = SubElement(root_children, "topics")
    set_attrs(root_topics, {"type": "attached"})

    for mod in modules:
        mod_topic = SubElement(root_topics, "topic")
        mod_id = make_topic_id()
        set_attrs(mod_topic, {
            "id": mod_id,
            "timestamp": timestamp_now(),
            "modified-by": "",
        })

        mod_title = SubElement(mod_topic, "title")
        mod_title.text = mod["name"]

        groups = mod.get("groups", [])
        if not groups:
            continue

        mod_children = SubElement(mod_topic, "children")
        mod_topics = SubElement(mod_children, "topics")
        set_attrs(mod_topics, {"type": "attached"})

        for grp in groups:
            grp_topic = SubElement(mod_topics, "topic")
            grp_id = make_topic_id()
            set_attrs(grp_topic, {
                "id": grp_id,
                "timestamp": timestamp_now(),
                "modified-by": "",
            })

            grp_title = SubElement(grp_topic, "title")
            grp_title.text = grp["name"]

            cases = grp.get("cases", [])
            if not cases:
                continue

            grp_children = SubElement(grp_topic, "children")
            grp_topics = SubElement(grp_children, "topics")
            set_attrs(grp_topics, {"type": "attached"})

            for case in cases:
                case_topic = SubElement(grp_topics, "topic")
                case_id = make_topic_id()
                set_attrs(case_topic, {
                    "id": case_id,
                    "timestamp": timestamp_now(),
                    "modified-by": "",
                })

                case_title = SubElement(case_topic, "title")
                case_title.text = f"{case.get('id', '')} {case.get('title', '')}"

                # 用例的详细信息作为子节点
                details = []

                if case.get("precondition"):
                    details.append(("⚡前置条件", case["precondition"]))

                steps = case.get("steps", [])
                if steps:
                    step_text = " ".join(f"{i+1}. {s}" for i, s in enumerate(steps))
                    details.append(("📋步骤", step_text))

                if case.get("expected"):
                    details.append(("✅预期结果", case["expected"]))

                if case.get("priority"):
                    details.append(("🏷优先级", case["priority"]))

                if case.get("type"):
                    details.append(("🏷类型", case["type"]))

                if details:
                    case_children = SubElement(case_topic, "children")
                    case_topics = SubElement(case_children, "topics")
                    set_attrs(case_topics, {"type": "attached"})

                    for label, value in details:
                        detail_topic = SubElement(case_topics, "topic")
                        detail_id = make_topic_id()
                        set_attrs(detail_topic, {
                            "id": detail_id,
                            "timestamp": timestamp_now(),
                            "modified-by": "",
                        })
                        detail_title = SubElement(detail_topic, "title")
                        detail_title.text = f"{label}: {value}"

    return root


def build_meta_xml():
    """生成 meta.xml"""
    NS = "urn:xmind:xmap:xmlns:meta:2.0"
    root = Element(f"{{{NS}}}meta")
    set_attrs(root, {"version": "2.0"})

    author = SubElement(root, "Author")
    name = SubElement(author, "Name")
    name.text = "Test Case Generator"

    create = SubElement(root, "Create")
    create_time = SubElement(create, "Time")
    create_time.text = timestamp_now()

    return root


def build_manifest_xml():
    """生成 META-INF/manifest.xml"""
    NS = "urn:xmind:xmap:xmlns:manifest:1.0"
    root = Element(f"{{{NS}}}manifest")

    entries = [
        ("content.xml", "text/xml"),
        ("meta.xml", "text/xml"),
        ("META-INF/manifest.xml", "text/xml"),
    ]

    for full_path, media_type in entries:
        entry = SubElement(root, "file-entry")
        set_attrs(entry, {
            "full-path": full_path,
            "media-type": media_type,
        })

    return root


def serialize_xml(elem, default_ns):
    """
    将 Element 序列化为格式化的 XML 字符串 测试用
    Args:
        elem: ElementTree 元素
        default_ns: 此 XML 的默认命名空间 URI
    """
    import xml.etree.ElementTree as ET

    # 先注册通用命名空间
    ET.register_namespace("fo", "http://www.w3.org/1999/XSL/Format")
    ET.register_namespace("svg", "http://www.w3.org/2000/svg")
    ET.register_namespace("xhtml", "http://www.w3.org/1999/xhtml")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    # 注册当前文件的默认命名空间（全局覆盖，但 serialize 是顺序执行的）
    ET.register_namespace("", default_ns)

    raw = tostring(elem, encoding="unicode", xml_declaration=True)
    raw = raw.replace(
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
    )
    return raw


def generate_xmind(output_path, title, cases_data):
    """
    生成 .xmind 文件

    cases_data JSON 结构:
    {
        "title": "项目名称（可选，会覆盖 title 参数）",
        "modules": [
            {
                "name": "模块名称",
                "groups": [
                    {
                        "name": "测试分组名称",
                        "cases": [
                            {
                                "id": "TC-001",
                                "title": "用例标题",
                                "precondition": "前置条件（可选）",
                                "steps": ["步骤1", "步骤2"],
                                "expected": "预期结果",
                                "priority": "P0/P1/P2/P3",
                                "type": "功能测试/接口测试/边界值/异常场景"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    cases_data["title"] = cases_data.get("title", title)

    content_root = build_content_xml(cases_data)
    meta_root = build_meta_xml()
    manifest_root = build_manifest_xml()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.xml", serialize_xml(content_root, "urn:xmind:xmap:xmlns:content:3.0"))
        zf.writestr("meta.xml", serialize_xml(meta_root, "urn:xmind:xmap:xmlns:meta:2.0"))
        zf.writestr("META-INF/manifest.xml", serialize_xml(manifest_root, "urn:xmind:xmap:xmlns:manifest:1.0"))

    total_groups = sum(len(m.get("groups", [])) for m in cases_data.get("modules", []))
    total_cases = sum(
        sum(len(g.get("cases", [])) for g in m.get("groups", []))
        for m in cases_data.get("modules", [])
    )
    print(f"✅ 已生成 XMind 文件: {output_path}", file=sys.stderr)
    print(f"   共 {total_groups} 个测试分组, {total_cases} 条测试用例", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="测试用例 XMind 生成器")
    parser.add_argument("--output", "-o", required=True, help="输出 .xmind 文件路径")
    parser.add_argument("--title", "-t", default="测试用例", help="XMind 文档标题")
    args = parser.parse_args()

    # 从标准输入读取 JSON
    try:
        raw = sys.stdin.read()
        if not raw:
            print("❌ 错误: 请在标准输入中提供 JSON 数据", file=sys.stderr)
            print("   用法: python generate_xmind.py -o out.xmind < cases.json", file=sys.stderr)
            sys.exit(1)
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}", file=sys.stderr)
        sys.exit(1)

    generate_xmind(args.output, args.title, data)


if __name__ == "__main__":
    main()
