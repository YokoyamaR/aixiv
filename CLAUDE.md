# AIXiv — AI + arXiv

AIXivは、あらゆる分野の知識を集約するオープンプラットフォームです。
テーマを投げるだけで、AIが各分野の専門家を模擬し、100ラウンドのパネルディスカッションを実行。その議論をもとに学術レポートを生成します。

## 使い方

Claude Code 上で:

```
/forge テーマをここに書く
```

またはシェルから:

```
./forge "テーマをここに書く"
```

## プロジェクト構成

```
.claude/commands/forge.md  ← レポート生成コマンド（Claude Codeスキル）
scripts/build_index.py     ← index.json生成ユーティリティ
docs/index.html            ← GitHub Pages トップページ
docs/viewer.html           ← レポート閲覧ページ
docs/papers/               ← 生成されたレポート（JA/EN）
docs/papers/index.json     ← レポート一覧データ
output/                    ← 議論ログの保存先
forge                      ← シェルからのエントリーポイント
```

## レポート生成の流れ

1. **専門家パネル構成**: テーマに最適な10名の専門家＋ファシリテーターを設計
2. **100ラウンド議論**: 多角的な視点からの段階的なパネルディスカッション
3. **日本語レポート**: 議論を学術論文形式にまとめる
4. **英語レポート**: 日本語版を基に英語の学術論文として再構成
5. **インデックス更新**: `python3 scripts/build_index.py` でindex.jsonを生成
6. **Git操作**: commit & push でGitHub Pagesに公開

## ファイル命名規則

- レポート: `docs/papers/{YYYY-MM-DD}_{slug}_{ja|en}.md`
- 議論ログ: `output/{slug}/`
- frontmatterに `title`, `date`, `rounds`, `lang`, `category` を含める

## カテゴリ

law / philosophy / science / society / economics / ethics / environment / health / education / other
