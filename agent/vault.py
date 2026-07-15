"""
智能备课助手 — Vault 文件管理模块

负责笔记的创建、读取、更新、删除，以及 _index.md 的同步维护。
"""
import re
import yaml
from pathlib import Path
from datetime import datetime
from config import VAULT_DIR, CATEGORIES


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，返回 (元数据, 正文)"""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            body = parts[2].strip()
            return meta, body
    return {}, content


def _format_frontmatter(meta: dict) -> str:
    """将元数据格式化为 YAML frontmatter 字符串"""
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        elif isinstance(v, str) and "\n" in v:
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def list_notes(category: str) -> list[dict]:
    """列出某个类别目录下的所有笔记"""
    cat_dir = VAULT_DIR / category
    if not cat_dir.exists():
        return []
    notes = []
    for f in sorted(cat_dir.glob("*.md")):
        if f.name == "_index.md":
            continue
        content = f.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(content)
        notes.append({
            "filename": f.name,
            "title": meta.get("title", f.stem),
            "tags": meta.get("tags", []),
            "created": meta.get("created", ""),
            "course": meta.get("course", ""),
        })
    return notes


def read_note(category: str, filename: str) -> str | None:
    """读取一篇笔记的完整内容"""
    filepath = VAULT_DIR / category / filename
    if not filepath.exists():
        return None
    return filepath.read_text(encoding="utf-8")


def write_note(category: str, filename: str, content: str, meta: dict | None = None) -> Path:
    """创建或覆写一篇笔记，自动添加 frontmatter"""
    filepath = VAULT_DIR / category / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if meta is None:
        meta = {}
    meta.setdefault("created", datetime.now().strftime("%Y-%m-%d"))
    if "tags" not in meta:
        meta["tags"] = []

    existing_meta = {}
    if "---" not in content:
        existing, body = {}, content
    else:
        existing, body = _parse_frontmatter(content)

    existing.update(meta)
    full = _format_frontmatter(existing) + "\n\n" + body
    filepath.write_text(full, encoding="utf-8")
    return filepath


def update_index(category: str) -> None:
    """根据目录下的实际笔记，自动刷新 _index.md"""
    cat_dir = VAULT_DIR / category
    if not cat_dir.exists():
        return

    desc = CATEGORIES.get(category, "")
    notes = list_notes(category)

    lines = [f"# {category}/ — 目录索引", ""]
    if desc:
        lines.append(f"> {desc}")
        lines.append("")

    lines.append("## 已有笔记")
    lines.append("")
    if notes:
        for n in notes:
            lines.append(f"- [[{n['filename']}]] — {n['title']}")
    else:
        lines.append("暂无笔记。")
    lines.append("")

    index_path = cat_dir / "_index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")


def search_notes(query: str, categories: list[str] | None = None) -> list[dict]:
    """在所有笔记中搜索关键词"""
    results = []
    search_dirs = [VAULT_DIR / c for c in (categories or CATEGORIES.keys())]
    for cat_dir in search_dirs:
        if not cat_dir.exists():
            continue
        for f in cat_dir.glob("*.md"):
            if f.name == "_index.md":
                continue
            content = f.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                meta, body = _parse_frontmatter(content)
                # 截取匹配片段
                idx = content.lower().find(query.lower())
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 150)
                snippet = "..." + content[start:end].replace("\n", " ") + "..."
                results.append({
                    "category": cat_dir.name,
                    "filename": f.name,
                    "title": meta.get("title", f.stem),
                    "snippet": snippet,
                    "tags": meta.get("tags", []),
                })
    return results[:20]


def get_vault_tree() -> dict:
    """获取仓库的完整目录树（用于前端侧边栏）"""
    tree = {}
    for cat_name in CATEGORIES:
        cat_dir = VAULT_DIR / cat_name
        files = []
        if cat_dir.exists():
            for f in sorted(cat_dir.glob("*.md")):
                if f.name == "_index.md":
                    continue
                files.append(f.name)
        tree[cat_name] = files
    return tree


def get_context_for_skill(skill_name: str) -> str:
    """根据 skill 类型，收集相关上下文"""
    context_parts = []

    profile = VAULT_DIR / "1_关于我" / "教师背景.md"
    if profile.exists():
        context_parts.append("## 教师背景\n")
        context_parts.append(profile.read_text(encoding="utf-8")[:1500])

    categories_map = {
        "prepare_lesson": ["3_课程", "4_教案", "2_教学灵感"],
        "generate_slides": ["4_教案", "5_课件", "3_课程"],
        "generate_exercises": ["4_教案", "6_习题", "3_课程"],
        "teaching_research": ["8_教研", "2_教学灵感"],
        "update_vault": [],
    }

    for cat in categories_map.get(skill_name, []):
        index_file = VAULT_DIR / cat / "_index.md"
        if index_file.exists():
            context_parts.append(f"\n## {cat}/ 已有笔记\n")
            context_parts.append(index_file.read_text(encoding="utf-8"))

    return "\n".join(context_parts)


def init_vault():
    """初始化 vault 目录结构（如果不存在则从模板创建）"""
    from config import CATEGORIES as cats

    for cat_name, desc in cats.items():
        cat_dir = VAULT_DIR / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        index = cat_dir / "_index.md"
        if not index.exists():
            lines = [f"# {cat_name}/ — 目录索引", "", f"> {desc}", "", "## 已有笔记", "", "暂无笔记。", ""]
            index.write_text("\n".join(lines), encoding="utf-8")

    # 创建 system_config
    sys_dir = VAULT_DIR / "system_config"
    sys_dir.mkdir(parents=True, exist_ok=True)
    memory = sys_dir / "memory.md"
    if not memory.exists():
        memory.write_text("# 智能备课助手 — 长期记忆\n\n## 教师偏好\n- 教学风格：理论推导 + 案例驱动\n- PPT 风格：要点式，数据图表丰富\n- 案例偏好：中国市场真实案例\n\n## 教学经验\n（待积累）\n", encoding="utf-8")

    # 创建教师背景模板
    profile = VAULT_DIR / "1_关于我" / "教师背景.md"
    if not profile.exists():
        profile.write_text("""---
created: 2026-07-15
tags: [教师信息, 基本信息]
---

# 教师背景

## 基本信息
- **教学科目**：大学金融学
- **教学手段**：PPT 课堂讲解
- **授课对象**：金融学大三本科生

## 教学风格
- 以理论推导为主，辅以案例驱动
- PPT 要点式风格，注重数据图表
- 偏好中国市场真实案例

## 当前授课课程
| 课程名称 | 授课对象 | 周学时 | 教材 |
|---------|---------|--------|------|
| 投资学 | 金融学大三 | 3 | Bodie《Investments》 |

## 对 AI 的期望
- 教案注重金融案例与理论结合
- 出题偏好计算题和案例分析题
- 课件每页要点不超过 4 条
""", encoding="utf-8")
