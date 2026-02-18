#!/usr/bin/env python3
"""
docs/papers/ 配下のレポートからindex.jsonを生成する。
ファイル名の末尾 _ja.md / _en.md で言語を判定する。
"""

import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def extract_frontmatter(text: str) -> dict:
    """Markdownの先頭にある---で囲まれたYAML frontmatterを抽出"""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    if yaml:
        try:
            return yaml.safe_load(parts[1]) or {}
        except Exception:
            return {}
    # yamlがなければ簡易パース
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def extract_first_paragraph(text: str) -> str:
    """frontmatter以降の最初の段落を抽出"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]

    lines = text.strip().split("\n")
    paragraph = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#"):
            started = True
            continue
        started = True
        paragraph.append(stripped)

    return " ".join(paragraph)[:200]


def detect_lang(filename: str, fm: dict) -> str:
    """ファイル名またはfrontmatterから言語を判定"""
    if fm.get("lang"):
        return fm["lang"]
    if filename.endswith("_ja.md"):
        return "ja"
    if filename.endswith("_en.md"):
        return "en"
    return "ja"


def main():
    project_root = Path(__file__).parent.parent
    papers_dir = project_root / "docs" / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    papers = []

    for md_file in sorted(papers_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)

        title = fm.get("title", md_file.stem.replace("_", " ").replace("-", " "))
        date = str(fm.get("date", ""))
        rounds = fm.get("rounds", 100)
        lang = detect_lang(md_file.name, fm)
        description = extract_first_paragraph(text)

        slug = md_file.stem
        tags = [t for t in re.split(r'[_\-]', slug) if len(t) > 2 and not t.isdigit() and t not in ("ja", "en")][:4]

        category = fm.get("category", "")

        paper_entry = {
            "file": md_file.name,
            "title": title,
            "date": date,
            "rounds": rounds,
            "lang": lang,
            "category": category,
            "description": description,
            "tags": tags,
        }
        papers.append(paper_entry)

    # 最新順（日付降順）にソート
    papers.sort(key=lambda p: p.get("date", ""), reverse=True)

    index_path = papers_dir / "index.json"
    index_path.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"index.json を生成しました: {len(papers)}件のレポート")


if __name__ == "__main__":
    main()
