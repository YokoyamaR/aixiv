#!/usr/bin/env python3
"""
レポート生成器: 議論結果から日本語+英語のレポートを生成する
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Error: anthropic パッケージが必要です。pip install anthropic を実行してください。")
    sys.exit(1)


def collect_discussion(output_dir: Path) -> str:
    """議論ファイルを読み込んで結合する"""
    files = sorted(output_dir.glob("*.md"))
    files = [f for f in files if f.name not in ("00_index.md", "00_panel.md", "01_index.md")]

    all_content = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        all_content.append(content)

    return "\n\n---\n\n".join(all_content)


def load_meta(output_dir: Path) -> dict:
    """メタデータを読み込む"""
    meta_path = output_dir / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def summarize_discussion(client: anthropic.Anthropic, discussion: str, model: str) -> str:
    """長い議論を要約する"""
    chunks = []
    chunk_size = 40000
    for i in range(0, len(discussion), chunk_size):
        chunks.append(discussion[i : i + chunk_size])

    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"  議論の要約を生成中... ({i + 1}/{len(chunks)})")
        resp = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": f"以下の議論を詳細に要約してください。主要な論点、提案された概念、結論を含めてください。\n\n{chunk}",
                }
            ],
        )
        summaries.append(resp.content[0].text)

    return "\n\n".join(summaries)


def generate_paper_ja(
    client: anthropic.Anthropic,
    discussion: str,
    meta: dict,
    model: str,
) -> str:
    """日本語レポートを生成"""
    theme_title = meta.get("theme", {}).get("title", "思考実験")
    rounds = meta.get("rounds", "?")

    discussion_for_paper = discussion
    if len(discussion) > 80000:
        discussion_for_paper = summarize_discussion(client, discussion, model)

    prompt = f"""以下は「{theme_title}」をテーマとした{rounds}ラウンドの専門家パネルディスカッションの記録（または要約）です。

この議論結果を、学術的なレポート（論文）形式にまとめてください。

## 要件

1. **構成**: 以下の構成に従ってください
   - タイトル
   - 要旨（Abstract）: 300字程度
   - 1. はじめに（Introduction）
   - 2〜8. 本論（議論の主要テーマごとに章立て）
   - 9. 結論と提言
   - 10. 今後の課題
   - 付録: 議論で生まれた主要概念の一覧表

2. **スタイル**:
   - 学術論文のような客観的・分析的な文体
   - 各章で議論の内容を体系的に整理
   - 議論で生まれた新しい概念には適切な定義を付与
   - 表や図（テキスト表現）を適宜使用

3. **言語**: 日本語

4. **分量**: 充実した内容（各章それなりの分量）

## 議論内容

{discussion_for_paper}

---

上記の議論をレポートとしてまとめてください。Markdown形式で出力してください。
"""

    print("  日本語レポートを生成中...")
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_paper_en(
    client: anthropic.Anthropic,
    ja_paper: str,
    meta: dict,
    model: str,
) -> str:
    """日本語レポートを基に英語版を生成"""
    theme_title = meta.get("theme", {}).get("title", "思考実験")

    prompt = f"""以下は「{theme_title}」に関する日本語の学術レポートです。
これを英語の学術レポートとして翻訳・再構成してください。

## 要件
- 単なる機械翻訳ではなく、英語の学術論文として自然な文体にする
- 専門用語は適切な英語に翻訳し、初出時にはカッコ内で日本語の原語も併記
- 構成は日本語版に準拠
- Markdown形式で出力

## 日本語レポート

{ja_paper}
"""

    print("  英語レポートを生成中...")
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def add_frontmatter(content: str, meta: dict, lang: str) -> str:
    """frontmatterを追加"""
    theme_title = meta.get("theme", {}).get("title", "思考実験")
    rounds = meta.get("rounds", 100)
    date_str = datetime.now().strftime("%Y-%m-%d")

    return f"""---
title: "{theme_title}"
date: {date_str}
rounds: {rounds}
lang: {lang}
---

{content}
"""


def main():
    parser = argparse.ArgumentParser(description="レポート生成器")
    parser.add_argument("output_dir", help="議論結果のディレクトリパス")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="使用するモデル（デフォルト: claude-sonnet-4-5-20250929）",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"Error: ディレクトリ {output_dir} が見つかりません。")
        sys.exit(1)

    meta = load_meta(output_dir)
    theme_title = meta.get("theme", {}).get("title", "Unknown")
    slug = meta.get("theme", {}).get("slug", "paper")
    print(f"テーマ: {theme_title}")

    discussion = collect_discussion(output_dir)
    if not discussion.strip():
        print("Error: 議論ファイルが見つかりません。")
        sys.exit(1)
    print(f"議論テキスト: {len(discussion)}文字")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY 環境変数を設定してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 日本語レポート生成
    ja_paper = generate_paper_ja(client, discussion, meta, model=args.model)

    # 英語レポート生成（日本語レポートを基に）
    en_paper = generate_paper_en(client, ja_paper, meta, model=args.model)

    # 保存
    project_root = Path(__file__).parent.parent
    papers_dir = project_root / "docs" / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    ja_path = papers_dir / f"{date_str}_{slug}_ja.md"
    en_path = papers_dir / f"{date_str}_{slug}_en.md"

    ja_path.write_text(add_frontmatter(ja_paper, meta, "ja"), encoding="utf-8")
    en_path.write_text(add_frontmatter(en_paper, meta, "en"), encoding="utf-8")

    print(f"\n日本語レポート: {ja_path}")
    print(f"英語レポート:   {en_path}")

    # 出力ディレクトリにもコピー
    (output_dir / "report_ja.md").write_text(ja_paper, encoding="utf-8")
    (output_dir / "report_en.md").write_text(en_paper, encoding="utf-8")


if __name__ == "__main__":
    main()
