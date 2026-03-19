# PLAN.md — codex-usage-indicator

## 概要

claude-usage-indicator（GNOME トップバーに Claude 使用量を表示するデーモン）と同様のツールを、Codex CLI 向けに作成する。Codex CLI は ChatGPT Plus の OAuth 認証を使用しており、公開の使用量 API は確認できていない。一方、`/status` 相当の 5 時間・週次 usage は `~/.codex/sessions/.../rollout-*.jsonl` に保存される `token_count.rate_limits` から再現可能であることを確認したため、まずは rollout のパースを基本方針とする。

本アプリは作者本人が個人環境で使う前提であり、用途は「日々の PC 使用が少し便利になること」である。したがって、厳密な完全性や配布品質よりも、壊れても把握しやすく、最低限実用になることを優先する。

実装は次の段階で進める。

1. Python で最小実装する。`claude-usage-indicator` は参考にするが、過度に構造を合わせない。
2. Claude Code などにレビューさせつつ、ローカルで実際に動かして修正する。
3. Python 版の挙動を基準として Rust に移植する。
4. 最後に、インストーラーやドキュメントを「自分で困らない程度」に整備する。

---

## 表示内容

- **使用量バー 2 本**: 5 時間 usage と週次 usage の残量または使用率
- カラー: 0–59% 緑 / 60–84% 黄 / 85–100% 赤（claude 版 icon.py の既存定数を流用）
- メニュー: `5h limit: 99% left`, `Weekly limit: 95% left`, plan 種別, 最終更新時刻

---

## データ取得元仕様

**主対象**: `~/.codex/sessions/**/rollout-*.jsonl`

**対象イベント例**:
```json
{
  "timestamp": "2026-03-17T22:59:31.055Z",
  "type": "event_msg",
  "payload": {
    "type": "token_count",
    "info": {
      "total_token_usage": {
        "total_tokens": 2803436
      },
      "model_context_window": 258400
    },
    "rate_limits": {
      "primary": {
        "used_percent": 14.0,
        "window_minutes": 300,
        "resets_at": 1773791854
      },
      "secondary": {
        "used_percent": 4.0,
        "window_minutes": 10080,
        "resets_at": 1774378654
      },
      "plan_type": "plus"
    }
  }
}
```

**パース対象フィールド**:
- `rate_limits.primary.used_percent` — 5 時間 usage
- `rate_limits.primary.resets_at` — 5 時間枠のリセット時刻
- `rate_limits.secondary.used_percent` — 週次 usage
- `rate_limits.secondary.resets_at` — 週次枠のリセット時刻
- `rate_limits.plan_type` — `plus` など
- タイムスタンプ（ISO8601 UTC）

再帰的に rollout を走査し、最新の `token_count` イベントを採用する。`rate_limits == null` の場合は「usage 情報なし」とみなす。

### 前提確認事項（実装前に検証すること）

- `~/.codex/sessions/**/rollout-*.jsonl` が実際に存在するか
- 最新 rollout に `token_count.rate_limits` が含まれるか
- `rate_limits == null` のセッションがあるため、その場合の表示仕様を決めること

---

## プロジェクト構成

**場所**: `~/devel/workspace/ai/codex-usage-indicator/`

```
codex-usage-indicator/
├── PLAN.md
├── README.md
├── config.example.ini
├── install.sh
└── codex_usage_indicator/
    ├── __init__.py
    ├── main.py          # AppIndicator メインループ（claude 版を踏襲）
    ├── rollout_reader.py # rollout パース（api.py 相当）★唯一の新規実装
    ├── icon.py          # 2本バーアイコン生成（claude 版をほぼそのまま流用）
    ├── config.py        # 設定読み込み（claude 版をほぼそのまま）
    └── menu.py          # ドロップダウンメニュー
```

Rust 移植時は別ディレクトリまたは別ブランチで進め、Python 版は正解系としてしばらく残す。

---

## 実装フェーズ

### Phase 1: Python 最小実装

- `rollout_reader.py` で最新の `token_count.rate_limits` を読む
- `icon.py` / `menu.py` / `main.py` で 5h / Weekly の表示を行う
- `Context window` は実装しない
- `rate_limits == null` はエラーではなく「usage 情報なし」として扱う
- まずは自分の環境で動けばよく、構造の綺麗さは二の次

### Phase 2: レビューと実動確認

- Claude Code などにコードレビューさせる
- レビュー指摘を見つつ、自分の環境で実際に動かして直す
- この段階では自動テストよりも、実運用で困らないことを優先する

### Phase 3: Rust 移植

- Python 版で確定した表示仕様と挙動を Rust に移す
- 先に機能同等を目指し、最適化や作り込みは後回し
- Python 版で扱わなかった `Context window` は Rust 版でも対象外

### Phase 4: 最低限の整備

- 自分が再インストールや再設定で困らない程度に `install.sh` を整える
- README にセットアップ方法・依存関係・既知の割り切りを書く
- 配布向けの汎用性や他環境対応は必須としない

---

## 各モジュール設計

### rollout_reader.py（新規、api.py 相当）

```python
SESSIONS_DIR = Path.home() / ".codex/sessions"

def fetch_usage() -> dict:
    """rollout 群から最新の token_count.rate_limits を返す"""

def fetch_usage_mock() -> dict:
    """開発用モック"""
```

戻り値:
```python
{
    "primary_used_percent": 1.0,
    "secondary_used_percent": 5.0,
    "primary_left_percent": 99.0,
    "secondary_left_percent": 95.0,
    "primary_resets_at": "2026-03-19T03:06:00+09:00",
    "secondary_resets_at": "2026-03-25T03:57:00+09:00",
    "plan_type": "plus",
    "timestamp": "2026-03-18T22:09:09+09:00"
}
```

### icon.py（claude 版をほぼそのまま流用）

- 22×22px、2本バー
- `generate_icon(five_hour_usage, weekly_usage)` / `generate_error_icon()`
- 既存の色定数・キャッシュバスティング機構をそのまま使用
- **変更点**: `extra_usage` は使わず、5 時間・週次の 2 本のみ表示する

### config.py（claude 版をほぼそのまま流用）

```ini
[general]
polling_interval = 30    # 秒 (デフォルト30, 範囲10-300)
mock = false
```

**変更点**: polling_interval のデフォルト値を `300` → `30`、range を `60–3600` → `10–300` に変更（ローカルファイル読み取りなので短くてよい）

### menu.py（claude 版から流用、フィールドを変更）

表示内容:
```
5h limit: 99% left
Weekly limit: 95% left
Plan: Plus
更新: 22:09 JST
─────────────────
今すぐ更新
終了
```

**変更点**: `build_menu` / `update_menu_data` の引数・ラベルを上記フィールドに変更

### main.py（claude 版をほぼそのまま流用）

- `GLib.timeout_add_seconds(polling_interval, poll)` でポーリング
- `poll()`: `rollout_reader.fetch_usage()` → icon 更新 → menu 更新
- エラー時: グレーアイコン + メニューにエラー表示
- **変更点**: `api.fetch_usage_*` の参照を `rollout_reader.fetch_usage` / `rollout_reader.fetch_usage_mock` に差し替え

---

## 流用・参照するファイル

| ファイル（claude 版） | 扱い |
|---|---|
| `claude_usage_indicator/api.py` | 参考のみ（rollout_reader.py として新規）|
| `claude_usage_indicator/icon.py` | ほぼそのまま流用（2本バー維持、extra は未使用）|
| `claude_usage_indicator/config.py` | ほぼそのまま流用（interval デフォルト・range 変更）|
| `claude_usage_indicator/menu.py` | 流用（ラベル・フィールドを変更）|
| `claude_usage_indicator/main.py` | 流用（fetch 関数の参照先変更）|
| `install.sh` | 流用（パス名変更）|

参照元: `~/devel/workspace/claude/claude-usage-indicator/`

---

## 実装リスク

**主要リスク: 最新 rollout に `rate_limits` が入っていない場合がある**
この場合、`/status` と同等の 5h/週次 usage を常に再現できない。個人用ツールなので、このケースは「usage 情報なし」と表示できれば十分とする。

**割り切り**
- `Context window` の再現は対象外とする
- 複数 rollout の厳密な整合性検証は行わない
- 自分の環境で動くことを優先し、汎用配布向けの堅牢化は後回しにする
- Python 版の段階では、自動テストや過度な設計整理は必須としない
- レビューは使うが、レビュアーの指摘をすべて取り込むことは目的にしない

---

## 検証方法

```bash
# Phase 1: rollout 値の確認
python3 scripts/status_from_rollout.py ~/.codex/sessions

# Phase 1: モックで動作確認（rollout 不要）
python3 -m codex_usage_indicator.main --mock

# Phase 1-2: 実 rollout で動作確認
python3 -m codex_usage_indicator.main

# Phase 2: Codex CLI を使った後、次のポーリングで 5h/週次 usage が反映されることを確認

# Phase 3: Rust 版でも Python 版と同等の表示になることを確認
```
