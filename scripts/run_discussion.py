#!/usr/bin/env python3
"""
思考実験エンジン: テーマを与えると、最適な専門家パネルを自動構成し、
100ラウンドの議論を実行してホワイトペーパーの素材を生成する。
"""

import os
import sys
import json
import time
import argparse
import yaml
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Error: anthropic パッケージが必要です。pip install anthropic を実行してください。")
    sys.exit(1)


def load_theme(theme_path: str) -> dict:
    """テーマ定義をYAMLから読み込む"""
    with open(theme_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_panel(client: anthropic.Anthropic, theme: dict, model: str) -> dict:
    """テーマに最適な専門家パネルをAIで自動生成する"""
    prompt = f"""以下のテーマについて100ラウンドの専門家パネルディスカッションを行います。
このテーマを多角的に議論するのに最適な専門家パネルを構成してください。

## テーマ
タイトル: {theme['title']}
説明: {theme['description']}

## 要件
- ファシリテーター1名 + 専門家10名 = 計11名
- 多様な専門分野からの視点を確保する（同じ分野の専門家は2名以上入れない）
- テーマに直接関連する分野だけでなく、意外な角度から切り込める分野も含める
- 名前はリアルな架空の名前（日本人・外国人を混在させる）
- 各専門家の立場・視点が互いに対立しうるよう設計する

## 出力形式（厳密にこのJSON形式で出力してください。JSON以外のテキストは不要です）
```json
{{
  "name": "パネル名",
  "facilitator": {{
    "name": "名前",
    "specialty": "専門",
    "description": "役割の説明"
  }},
  "experts": [
    {{
      "name": "名前",
      "specialty": "専門分野",
      "description": "この専門家の視点・立場の説明"
    }}
  ]
}}
```

JSON以外のテキストは出力しないでください。"""

    print("テーマに最適な専門家パネルを構成中...")
    response = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # JSONブロックを抽出
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    panel = json.loads(text)
    print(f"パネル構成完了: {panel['name']}")
    print(f"  ファシリテーター: {panel['facilitator']['name']}（{panel['facilitator']['specialty']}）")
    for i, e in enumerate(panel["experts"], 1):
        print(f"  専門家{i}: {e['name']}（{e['specialty']}）")
    return panel


def build_system_prompt(panel: dict, theme: dict) -> str:
    """システムプロンプトを構築"""
    experts = panel["experts"]
    expert_list = "\n".join(
        f"- {e['name']}（{e['specialty']}）: {e['description']}"
        for e in experts
    )
    facilitator = panel["facilitator"]

    return f"""あなたは思考実験シミュレーターです。以下の専門家パネルによるディスカッションをシミュレートしてください。

## テーマ
{theme['title']}

## テーマの説明
{theme['description']}

## 問いかけ
{theme.get('question', theme['description'])}

## パネル構成

**ファシリテーター:** {facilitator['name']}（{facilitator['specialty']}）— {facilitator['description']}

**専門家:**
{expert_list}

## 議論ルール
1. 各ラウンドでは、ファシリテーターが論点を提示し、複数の専門家が応答する
2. 専門家は自分の専門分野の視点から発言する
3. 専門家同士で意見が対立することも歓迎する
4. 新しい概念や仮説が生まれた場合は明示的に名付ける
5. 各ラウンドの最後に「次のラウンドへの問い」を提示する
6. 議論は日本語で行う

## 出力形式
Markdownで出力してください。見出し、箇条書き、表、引用を適宜使用してください。
"""


def save_panel(panel: dict, output_dir: Path):
    """パネル構成をMarkdownで保存"""
    md = f"# パネル構成：{panel['name']}\n\n"
    f = panel["facilitator"]
    md += f"## ファシリテーター\n\n"
    md += f"**{f['name']}**（{f['specialty']}）\n\n{f['description']}\n\n"
    md += f"## 専門家（{len(panel['experts'])}名）\n\n"
    md += "| # | 名前 | 専門 | 視点 |\n"
    md += "|---|------|------|------|\n"
    for i, e in enumerate(panel["experts"], 1):
        md += f"| {i} | {e['name']} | {e['specialty']} | {e['description']} |\n"

    filepath = output_dir / "00_panel.md"
    filepath.write_text(md, encoding="utf-8")
    return filepath


def run_rounds(
    client: anthropic.Anthropic,
    system_prompt: str,
    theme: dict,
    output_dir: Path,
    rounds_per_file: int = 4,
    total_rounds: int = 100,
    model: str = "claude-sonnet-4-5-20250929",
) -> list[Path]:
    """議論を実行し、ファイルに保存する"""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []
    previous_summary = ""
    current_round = 1

    while current_round <= total_rounds:
        end_round = min(current_round + rounds_per_file - 1, total_rounds)
        file_num = len(generated_files) + 1

        if current_round == 1:
            user_prompt = f"""第{current_round}ラウンドを開始してください。

テーマ「{theme['title']}」について、まず各専門家の基本的な立場を確認し、核心的な問いを設定してください。

出力はMarkdownで、ファイルの冒頭に「# 第{current_round}ラウンド：（サブテーマ）」という見出しをつけてください。
最後に「## 次のラウンドへの問い」セクションをつけてください。"""
        elif current_round >= total_rounds - 5:
            user_prompt = f"""第{current_round}〜{end_round}ラウンドを実行してください。

これまでの議論の要約：
{previous_summary}

これは最終段階です。議論を総括し、最終的な結論・提言をまとめてください。
- 各専門家の最終的な立場表明
- 議論で生まれた主要概念のまとめ
- 最終宣言（共同声明のような形式で）

出力はMarkdownで、ファイルの冒頭に「# 第{current_round}〜{end_round}ラウンド：（サブテーマ）」という見出しをつけてください。"""
        else:
            user_prompt = f"""第{current_round}〜{end_round}ラウンドを実行してください。

これまでの議論の要約：
{previous_summary}

前のラウンドで提示された問いを起点に、議論を深めてください。
- 新しい視点や反論を積極的に提示
- 具体例や歴史的事例を交える
- 新しい概念が生まれた場合は名付ける
- 専門家同士の建設的な対立を演出

出力はMarkdownで、ファイルの冒頭に「# 第{current_round}〜{end_round}ラウンド：（サブテーマ）」という見出しをつけてください。
最後に「## 次のラウンドへの問い」セクションをつけてください。"""

        print(f"  ラウンド {current_round}〜{end_round} を生成中...")

        try:
            response = client.messages.create(
                model=model,
                max_tokens=8000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text
        except Exception as e:
            print(f"  エラー: {e}")
            print("  10秒後にリトライします...")
            time.sleep(10)
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=8000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                content = response.content[0].text
            except Exception as e2:
                print(f"  リトライ失敗: {e2}")
                content = f"# 第{current_round}〜{end_round}ラウンド：生成エラー\n\nこのラウンドの生成中にエラーが発生しました: {e2}\n"

        # ファイルに保存
        filename = f"{file_num:02d}_round_{current_round:03d}-{end_round:03d}.md"
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        generated_files.append(filepath)
        print(f"  → {filename} を保存しました")

        # 要約を生成（次のラウンドへの文脈として）
        try:
            summary_response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"以下の議論を300字程度で要約してください。主要な論点、新概念、対立点を含めてください。\n\n{content}",
                    }
                ],
            )
            new_summary = summary_response.content[0].text
            previous_summary = f"{previous_summary}\n\n【第{current_round}〜{end_round}ラウンド】{new_summary}"
            # 要約が長くなりすぎないよう、直近の内容を保持
            if len(previous_summary) > 6000:
                previous_summary = previous_summary[-5000:]
        except Exception:
            pass

        current_round = end_round + 1
        # API レート制限対策
        time.sleep(2)

    return generated_files


def generate_index(theme: dict, panel: dict, files: list[Path], output_dir: Path):
    """議論ファイルの目次を生成"""
    index_content = f"# 思考実験：{theme['title']}\n\n"
    index_content += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    index_content += f"## テーマ\n\n{theme['description']}\n\n"
    index_content += f"## パネル\n\n{panel['name']}（専門家{len(panel['experts'])}名 + ファシリテーター）\n\n"
    index_content += "## 議論ファイル一覧\n\n"

    for f in files:
        first_line = f.read_text(encoding="utf-8").split("\n")[0]
        title = first_line.lstrip("# ").strip() if first_line.startswith("#") else f.name
        index_content += f"- [{title}]({f.name})\n"

    index_path = output_dir / "01_index.md"
    index_path.write_text(index_content, encoding="utf-8")
    return index_path


def main():
    parser = argparse.ArgumentParser(description="思考実験エンジン")
    parser.add_argument("theme", help="テーマファイル（YAML）のパス")
    parser.add_argument("--output", default=None, help="出力ディレクトリ")
    parser.add_argument(
        "--rounds", type=int, default=100, help="ラウンド数（デフォルト: 100）"
    )
    parser.add_argument(
        "--rounds-per-file",
        type=int,
        default=4,
        help="1ファイルあたりのラウンド数（デフォルト: 4）",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="使用するモデル（デフォルト: claude-sonnet-4-5-20250929）",
    )
    args = parser.parse_args()

    # テーマ読み込み
    theme = load_theme(args.theme)
    print(f"テーマ: {theme['title']}")

    # Anthropic クライアント初期化
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY 環境変数を設定してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 出力ディレクトリ
    project_root = Path(__file__).parent.parent
    if args.output:
        output_dir = Path(args.output)
    else:
        slug = theme.get("slug", theme["title"].replace(" ", "_")[:30])
        output_dir = project_root / "output" / slug

    output_dir.mkdir(parents=True, exist_ok=True)

    # パネルをテーマから自動生成
    panel = generate_panel(client, theme, args.model)

    # パネル構成を保存
    panel_file = save_panel(panel, output_dir)
    print(f"パネル構成: {panel_file}")

    # パネルをJSONでも保存（メタデータ用）
    panel_json_path = output_dir / "panel.json"
    panel_json_path.write_text(
        json.dumps(panel, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n出力先: {output_dir}")
    print(f"ラウンド数: {args.rounds}")
    print(f"モデル: {args.model}")
    print()

    # 議論実行
    print("=" * 60)
    print(f"思考実験「{theme['title']}」を開始します")
    print("=" * 60)

    system_prompt = build_system_prompt(panel, theme)
    files = run_rounds(
        client=client,
        system_prompt=system_prompt,
        theme=theme,
        output_dir=output_dir,
        rounds_per_file=args.rounds_per_file,
        total_rounds=args.rounds,
        model=args.model,
    )

    # 目次生成
    index_file = generate_index(theme, panel, files, output_dir)
    print(f"\n目次ファイル: {index_file}")

    print("\n" + "=" * 60)
    print(f"議論が完了しました。{len(files)}ファイルを生成しました。")
    print("=" * 60)

    # メタデータ保存
    meta = {
        "theme": theme,
        "panel": panel,
        "rounds": args.rounds,
        "model": args.model,
        "files": [str(f.name) for f in files],
        "generated_at": datetime.now().isoformat(),
    }
    meta_path = output_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
