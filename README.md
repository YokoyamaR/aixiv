# AIchive

AI + Archive = AIchive

あらゆる分野の知識を集約するオープンプラットフォーム。テーマを与えるだけで、AIが各分野の専門家を模擬し、100ラウンドのパネルディスカッションを実行。その議論をもとに学術レポート（日本語+英語）を生成し、GitHub Pagesで公開します。

## 必要なもの

- [Claude Code](https://claude.ai/download)（Anthropic公式CLI）
- Claude Pro または Max プラン

> 1件のレポート生成で大量のトークンを消費します。定額プラン（Pro/Max）での利用を想定した設計です。

## 使い方

### Claude Code から（推奨）

```bash
git clone https://github.com/YokoyamaR/aichive.git
cd aichive
claude
```

Claude Code 内で:

```
/forge 法律の耐用年数と国家の変容
```

### シェルから

```bash
./forge "法律の耐用年数と国家の変容"
```

これだけで全自動:

1. テーマに最適な専門家10名 + ファシリテーターを自動構成
2. 100ラウンドのパネルディスカッションを実行
3. 日本語レポート + 英語レポートを生成
4. git commit & push → GitHub Pages に公開

## プロジェクト構成

```
.claude/commands/forge.md  ← レポート生成コマンド（Claude Codeスキル）
scripts/build_index.py     ← index.json生成ユーティリティ
docs/index.html            ← GitHub Pages トップページ
docs/viewer.html           ← レポート閲覧ページ
docs/papers/               ← 生成されたレポート（JA/EN）
output/                    ← 議論ログの保存先
forge                      ← シェルからのエントリーポイント
```

## 免責事項

本プロジェクトで生成されるレポートは、すべてAI（Anthropic Claude）が専門家を模擬して生成したものです。人間の専門家による査読・検証は行われていません。内容の正確性・完全性は保証されません。

## ライセンス

MIT
