# AIカイブ (AIchive)

テーマを投げるだけ。AIが専門家パネルを自動構成し、100ラウンドの議論を実行し、レポート（日本語+英語）にまとめて GitHub Pages で公開する思考実験アーカイブ。

## セットアップ

```bash
git clone https://github.com/YokoyamaR/aichive.git
cd aichive
export ANTHROPIC_API_KEY="sk-ant-..."
pip install -r scripts/requirements.txt
```

## 使い方

```bash
./forge "法律の耐用年数と国家の変容"
```

これだけ。あとは全自動:

1. テーマに最適な専門家10名 + ファシリテーターを自動構成
2. 100ラウンドのパネルディスカッションを実行
3. 日本語レポート + 英語レポートを生成
4. git commit & push → GitHub Pages に公開

### オプション

```bash
./forge "AIに意識は宿るか" --rounds 50
./forge "量子コンピュータと暗号の未来" --model claude-opus-4-6
```

## 仕組み

```
./forge "テーマ"
    │
    ├─ テーマに最適な専門家パネルをAIが自動構成
    ├─ 100ラウンドの議論を実行（Markdownで保存）
    ├─ 日本語レポート + 英語レポートを生成
    ├─ GitHub Pages 用のインデックスを更新
    └─ git commit & push → Pages自動デプロイ
```

## 注意

- 100ラウンドで約50回以上のAPI呼び出しが発生します
- `claude-sonnet-4-5-20250929`（デフォルト）が最もコスパが良いです
- 完了まで数十分かかります
