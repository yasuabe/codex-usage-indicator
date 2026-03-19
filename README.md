# codex-usage-indicator

Codex の利用量を確認するための個人用 GNOME AppIndicator です。

現在の Python プロトタイプは `~/.codex/sessions/**/rollout-*.jsonl` を読み取り、次を表示します。

- 5h limit
- Weekly limit
- Plan

`Context window` は意図的に対象外としています。

## 情報源

Python 実装と Rust 実装はどちらも、次の場所にある
最新の `token_count.rate_limits` snapshot を読み取ります。

```text
~/.codex/sessions/**/rollout-*.jsonl
```

indicator のメニューには rollout のフルパスを表示しません。
UI に出すには長すぎて実用的でないためです。

## 実行

```bash
python3 -m codex_usage_indicator.main --mock
python3 -m codex_usage_indicator.main
cargo run -- ~/.codex/sessions
cargo run --bin indicator
```
